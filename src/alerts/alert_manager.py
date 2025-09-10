"""
Alerting system for sending notifications about new Craigslist listings.
Supports SMS, Email, and Discord notifications.
"""

import logging
import ssl
from abc import ABC, abstractmethod
from email.message import EmailMessage
from typing import List, Optional, Protocol
import smtplib

import requests
from twilio.rest import Client

from constants import SMTP_SERVER, SMTP_PORT, HTTP_OK, HTTP_NO_CONTENT
from exceptions import EmailAlertError, SMSAlertError, DiscordAlertError
from utils.network import make_robust_request


class AlertSender(Protocol):
    """Protocol for alert senders."""
    
    def send_alert(self, listing) -> None:
        """Send an alert for a single listing."""
        ...


class BaseAlertSender(ABC):
    """Base class for alert senders."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the alert sender.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
    
    @abstractmethod
    def send_alert(self, listing) -> None:
        """Send an alert for a single listing."""
        pass
    
    def format_listing_message(self, listing) -> str:
        """
        Format a listing into a readable message.
        
        Args:
            listing: Listing object to format
            
        Returns:
            Formatted message string
        """
        return (
            f"Title: {listing.title}\n"
            f"Posted: {listing.time_posted}\n"
            f"Location: {listing.location}\n"
            f"Scraped: {listing.time_scraped}\n"
            f"Link: {listing.link}"
        )


class SMSAlertSender(BaseAlertSender):
    """Sends SMS alerts using Twilio."""
    
    def __init__(
        self, 
        account_sid: str,
        auth_token: str,
        from_number: str,
        to_numbers: List[str],
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize SMS alert sender.
        
        Args:
            account_sid: Twilio account SID
            auth_token: Twilio auth token
            from_number: Source phone number
            to_numbers: List of destination phone numbers
            logger: Optional logger instance
        """
        super().__init__(logger)
        self.client = Client(account_sid, auth_token)
        self.from_number = from_number
        self.to_numbers = to_numbers
    
    def send_alert(self, listing) -> None:
        """
        Send SMS alert for a listing.
        
        Args:
            listing: Listing object to send alert for
            
        Raises:
            SMSAlertError: If SMS sending fails
        """
        try:
            message_body = self.format_listing_message(listing)
            
            for to_number in self.to_numbers:
                self.logger.info(f"Sending SMS alert to {to_number}")
                
                message = self.client.messages.create(
                    body=message_body,
                    from_=self.from_number,
                    to=to_number
                )
                
                self.logger.success(f"SMS sent successfully. SID: {message.sid}")
                
        except Exception as e:
            raise SMSAlertError(f"Failed to send SMS alert: {e}")
    
    def send_error_alert(self, error_message: str) -> None:
        """
        Send an error alert via SMS.
        
        Args:
            error_message: Error message to send
        """
        try:
            for to_number in self.to_numbers:
                self.client.messages.create(
                    body=f"Craigslist Scraper Error: {error_message}",
                    from_=self.from_number,
                    to=to_number
                )
            self.logger.info("Error alert sent via SMS")
        except Exception as e:
            self.logger.error(f"Failed to send error alert via SMS: {e}")


class EmailAlertSender(BaseAlertSender):
    """Sends email alerts using SMTP."""
    
    def __init__(
        self,
        from_email: str,
        email_password: str,
        to_emails: List[str],
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize email alert sender.
        
        Args:
            from_email: Source email address
            email_password: Email password/app password
            to_emails: List of destination email addresses
            logger: Optional logger instance
        """
        super().__init__(logger)
        self.from_email = from_email
        self.email_password = email_password
        self.to_emails = to_emails
    
    def send_alert(self, listing) -> None:
        """
        Send email alert for a listing.
        
        Args:
            listing: Listing object to send alert for
            
        Raises:
            EmailAlertError: If email sending fails
        """
        try:
            msg = EmailMessage()
            msg['Subject'] = f'New Craigslist Listing: {listing.title}'
            msg['From'] = self.from_email
            msg['To'] = ', '.join(self.to_emails)
            
            message_body = self.format_listing_message(listing)
            msg.set_content(message_body)
            
            ssl_context = ssl.create_default_context()
            
            with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=ssl_context) as server:
                server.login(self.from_email, self.email_password)
                server.send_message(msg)
            
            self.logger.success(f"Email alert sent for listing: {listing.title}")
            
        except Exception as e:
            raise EmailAlertError(f"Failed to send email alert: {e}")


class DiscordAlertSender(BaseAlertSender):
    """Sends Discord alerts using webhooks."""
    
    def __init__(
        self,
        webhook_url: str,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize Discord alert sender.
        
        Args:
            webhook_url: Discord webhook URL
            logger: Optional logger instance
        """
        super().__init__(logger)
        self.webhook_url = webhook_url
    
    def send_alert(self, listing) -> None:
        """
        Send Discord alert for a listing.
        
        Args:
            listing: Listing object to send alert for
            
        Raises:
            DiscordAlertError: If Discord sending fails
        """
        try:
            message_body = (
                f"@here\n"
                f"**🆕 New Craigslist Listing**\n\n"
                f"**Title:** {listing.title}\n"
                f"**Posted:** {listing.time_posted}\n"
                f"**Location:** {listing.location}\n"
                f"**Scraped:** {listing.time_scraped}\n\n"
                f"🔗 **Link:** {listing.link}"
            )
            
            data = {"content": message_body}
            
            self.logger.info(f"Sending Discord alert for listing: {listing.title}")
            
            # Use robust request handling for SSL issues in Docker
            response = make_robust_request(
                url=self.webhook_url,
                method="POST",
                data=data,
                timeout=10,
                logger=self.logger
            )
            
            if response.status_code not in [HTTP_OK, HTTP_NO_CONTENT]:
                raise DiscordAlertError(
                    f"Discord webhook failed with status {response.status_code}: {response.text}"
                )
            
            self.logger.success(f"Discord alert sent for listing: {listing.title}")
            
        except Exception as e:
            # Check if it's already a DiscordAlertError, if so re-raise
            if isinstance(e, DiscordAlertError):
                raise
            raise DiscordAlertError(f"Failed to send Discord alert: {e}")


class AlertManager:
    """Manages multiple alert senders and coordinates alert sending."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the alert manager.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self.alert_senders: List[AlertSender] = []
    
    def add_sender(self, sender: AlertSender) -> None:
        """
        Add an alert sender.
        
        Args:
            sender: Alert sender to add
        """
        self.alert_senders.append(sender)
        self.logger.info(f"Added alert sender: {sender.__class__.__name__}")
    
    def send_alerts(self, listings: List) -> None:
        """
        Send alerts for a list of listings using all configured senders.
        
        Args:
            listings: List of listings to send alerts for
        """
        if not listings:
            self.logger.info("No listings to send alerts for")
            return
        
        if not self.alert_senders:
            self.logger.warning("No alert senders configured")
            return
        
        self.logger.info(f"Sending alerts for {len(listings)} listings")
        
        for i, listing in enumerate(listings, 1):
            self.logger.info(f"Processing listing {i}/{len(listings)}: {listing.title}")
            
            for sender in self.alert_senders:
                try:
                    sender.send_alert(listing)
                except Exception as e:
                    self.logger.error(
                        f"Failed to send alert via {sender.__class__.__name__}: {e}"
                    )
        
        self.logger.success(f"Completed alert sending for {len(listings)} listings")