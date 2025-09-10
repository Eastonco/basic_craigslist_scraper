"""
Main application class for the Craigslist scraper.
Orchestrates scraping, database operations, and alerting.
"""

import logging
from typing import List, Optional

from sqlalchemy import or_

from alerts.alert_manager import AlertManager, SMSAlertSender, EmailAlertSender, DiscordAlertSender
from constants import (
    MIN_SLEEP_BETWEEN_URLS, MAX_SLEEP_BETWEEN_URLS,
    MIN_SLEEP_BETWEEN_CYCLES, MAX_SLEEP_BETWEEN_CYCLES,
    MAX_ERROR_COUNT
)
from database.db_manager import DatabaseManager
from exceptions import CraigslistScraperError
from models import Config
from scraper.craigslist_scraper import CraigslistScraper
from utils.timing import SleepManager


class CraigslistScraperApp:
    """Main application class that orchestrates the scraping process."""
    
    def __init__(
        self,
        config: Config,
        engine,
        db_model_class,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the scraper application.
        
        Args:
            config: Application configuration
            engine: SQLAlchemy engine
            db_model_class: Database model class
            logger: Optional logger instance
        """
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        self.error_count = 0
        
        # Initialize components
        self.scraper = CraigslistScraper(logger=self.logger)
        self.database = DatabaseManager(engine, db_model_class, logger=self.logger)
        self.alert_manager = AlertManager(logger=self.logger)
        self.sleep_manager = SleepManager(logger=self.logger)
        
        # Setup database
        self.database.create_tables()
        
        # Setup alert senders
        self._setup_alert_senders()
        
        # Create filter conditions for database queries
        self.filter_conditions = self._create_filter_conditions(db_model_class)
    
    def _setup_alert_senders(self) -> None:
        """Set up alert senders based on configuration."""
        if self.config.send_sms_alerts:
            sms_sender = SMSAlertSender(
                account_sid=self.config.twilio_account_sid,
                auth_token=self.config.twilio_auth_token,
                from_number=self.config.src_phone_number,
                to_numbers=self.config.dst_phone_numbers,
                logger=self.logger
            )
            self.alert_manager.add_sender(sms_sender)
        
        if self.config.send_email_alerts:
            email_sender = EmailAlertSender(
                from_email=self.config.src_email,
                email_password=self.config.email_key,
                to_emails=self.config.dst_emails,
                logger=self.logger
            )
            self.alert_manager.add_sender(email_sender)
        
        if self.config.send_discord_alerts:
            discord_sender = DiscordAlertSender(
                webhook_url=str(self.config.discord_webhook_url),
                logger=self.logger
            )
            self.alert_manager.add_sender(discord_sender)
    
    def _create_filter_conditions(self, db_model_class) -> List:
        """
        Create SQLAlchemy filter conditions from config filters.
        
        Args:
            db_model_class: Database model class
            
        Returns:
            List of filter conditions
        """
        if not self.config.filters:
            return []
        
        return [
            db_model_class.title.regexp_match(rf'\\b({word})\\b', 'ix') 
            for word in self.config.filters
        ]
    
    def scrape_single_url(self, url: str, timestamp: str) -> int:
        """
        Scrape a single URL and save new listings.
        
        Args:
            url: URL to scrape
            timestamp: Current timestamp
            
        Returns:
            Number of new listings found
            
        Raises:
            CraigslistScraperError: If scraping fails
        """
        try:
            # Scrape the URL
            listings = self.scraper.scrape_url(url, timestamp, self.database.db_model)
            
            # Save new listings to database
            new_count = self.database.save_new_listings(listings)
            
            return new_count
            
        except Exception as e:
            self.error_count += 1
            error_msg = f"Error scraping {url}: {e}"
            self.logger.error(error_msg)
            
            # Send error alert if we have SMS configured
            if hasattr(self.alert_manager, 'alert_senders'):
                sms_senders = [
                    sender for sender in self.alert_manager.alert_senders 
                    if isinstance(sender, SMSAlertSender)
                ]
                for sender in sms_senders:
                    try:
                        attempts_left = MAX_ERROR_COUNT - self.error_count
                        sender.send_error_alert(
                            f"{error_msg}\\nScript will try {attempts_left} more times."
                        )
                    except Exception as alert_error:
                        self.logger.error(f"Failed to send error alert: {alert_error}")
            
            if self.error_count >= MAX_ERROR_COUNT:
                raise CraigslistScraperError(
                    f"Max error count ({MAX_ERROR_COUNT}) reached. Shutting down."
                )
            
            return 0
    
    def process_alerts_for_timestamp(self, timestamp: str) -> None:
        """
        Process and send alerts for new listings from the given timestamp.
        
        Args:
            timestamp: Timestamp to check for new listings
        """
        try:
            # Get new listings that should trigger alerts
            alert_listings = self.database.get_new_listings_for_alerts(
                timestamp, 
                self.filter_conditions
            )
            
            if alert_listings:
                self.logger.info(f"Processing {len(alert_listings)} listings for alerts")
                for i, listing in enumerate(alert_listings, 1):
                    self.logger.info(f"{i}. {listing.title} : {listing.link}")
                
                # Send alerts
                self.alert_manager.send_alerts(alert_listings)
            else:
                self.logger.info("No new listings found for alerts")
                
        except Exception as e:
            self.logger.error(f"Failed to process alerts: {e}")
    
    def run_single_cycle(self, initial_loop: bool = False) -> None:
        """
        Run a single scraping cycle for all configured URLs.
        
        Args:
            initial_loop: Whether this is the initial loop (skip alerts)
        """
        timestamp = self.sleep_manager.get_current_timestamp()
        total_new_listings = 0
        
        self.logger.info(f"Starting scraping cycle at {timestamp}")
        
        for i, url in enumerate(self.config.urls):
            try:
                # Scrape the URL
                new_count = self.scrape_single_url(str(url), timestamp)
                total_new_listings += new_count
                
                # Reset error count on successful scrape
                self.error_count = 0
                
                # Sleep between URLs (except for the last one)
                if i < len(self.config.urls) - 1:
                    self.sleep_manager.sleep_random(
                        MIN_SLEEP_BETWEEN_URLS, 
                        MAX_SLEEP_BETWEEN_URLS
                    )
                    
            except CraigslistScraperError:
                # This is a fatal error, re-raise
                raise
            except Exception as e:
                self.logger.error(f"Unexpected error processing URL {url}: {e}")
                continue
        
        # Process alerts (skip on initial loop)
        if not initial_loop:
            self.process_alerts_for_timestamp(timestamp)
        
        self.logger.info(
            f"Cycle completed. Total new listings: {total_new_listings}"
        )
    
    def run(self) -> None:
        """
        Run the main scraping loop continuously.
        
        Raises:
            CraigslistScraperError: If a fatal error occurs
        """
        from utils.logger import welcome_message
        welcome_message(self.logger)
        
        self.logger.info("Starting Craigslist scraper application")
        self.logger.info(f"Monitoring {len(self.config.urls)} URLs")
        self.logger.info(f"Filters configured: {len(self.config.filters)} terms")
        
        initial_loop = True
        
        try:
            while True:
                self.run_single_cycle(initial_loop=initial_loop)
                initial_loop = False
                
                # Sleep between major cycles
                self.sleep_manager.sleep_random(
                    MIN_SLEEP_BETWEEN_CYCLES,
                    MAX_SLEEP_BETWEEN_CYCLES
                )
                
        except KeyboardInterrupt:
            self.logger.info("Received interrupt signal. Shutting down gracefully...")
        except CraigslistScraperError as e:
            self.logger.error(f"Fatal application error: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected application error: {e}")
            raise CraigslistScraperError(f"Unexpected application error: {e}")
        finally:
            self.logger.info("Craigslist scraper application stopped")