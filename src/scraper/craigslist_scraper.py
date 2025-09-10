"""
Web scraping module for Craigslist listings.
Handles browser setup, page interaction, and data extraction.
"""

import datetime
import logging
from typing import List, Optional

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

from constants import (
    BROWSER_IMPLICIT_WAIT, PAGE_LOAD_TIMEOUT,
    ELEMENT_CLASS_SEARCH_RESULT, ELEMENT_CLASS_POSTING_TITLE, ELEMENT_CLASS_META
)
from exceptions import BrowserError, ScrapingError


class CraigslistScraper:
    """Handles scraping of Craigslist listings."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the scraper.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
    
    def setup_browser(self) -> webdriver.Firefox:
        """
        Set up and return a Firefox browser instance.
        
        Returns:
            Configured Firefox webdriver instance
            
        Raises:
            BrowserError: If browser setup fails
        """
        try:
            self.logger.debug("Setting up Firefox browser in headless mode")
            firefox_options = Options()
            firefox_options.add_argument('--headless')
            firefox_options.add_argument('--no-sandbox')
            firefox_options.add_argument('--disable-dev-shm-usage')
            
            browser = webdriver.Firefox(options=firefox_options)
            browser.implicitly_wait(BROWSER_IMPLICIT_WAIT)
            
            self.logger.debug("Browser setup completed successfully")
            return browser
            
        except WebDriverException as e:
            raise BrowserError(f"Failed to setup Firefox browser: {e}")
        except Exception as e:
            raise BrowserError(f"Unexpected error during browser setup: {e}")
    
    def extract_listings_from_page(
        self, 
        browser: webdriver.Firefox, 
        timestamp: str,
        db_model_class
    ) -> List:
        """
        Extract listing data from the current page.
        
        Args:
            browser: WebDriver instance with page loaded
            timestamp: Timestamp string for when scraping occurred
            db_model_class: Database model class for creating listing objects
            
        Returns:
            List of listing objects
            
        Raises:
            ScrapingError: If extraction fails
        """
        try:
            listings = []
            
            # Wait for page to load
            before_load = datetime.datetime.now()
            self.logger.info(f"Starting page load at {before_load.strftime('%H:%M:%S')}")
            
            try:
                WebDriverWait(browser, PAGE_LOAD_TIMEOUT).until(
                    EC.presence_of_element_located((By.CLASS_NAME, ELEMENT_CLASS_SEARCH_RESULT))
                )
            except TimeoutException:
                self.logger.warning(f"Page load timeout after {PAGE_LOAD_TIMEOUT} seconds")
            
            after_load = datetime.datetime.now()
            load_time = (after_load - before_load).total_seconds()
            self.logger.info(f"Page loaded in {load_time:.2f} seconds")
            
            # Find all listing elements
            listing_elements = browser.find_elements(
                by=By.CLASS_NAME, 
                value=ELEMENT_CLASS_SEARCH_RESULT
            )
            
            self.logger.info(f"Found {len(listing_elements)} listing elements")
            
            for element in listing_elements:
                try:
                    listing_data = self._extract_single_listing(element, timestamp, db_model_class)
                    if listing_data:
                        listings.append(listing_data)
                except Exception as e:
                    self.logger.warning(f"Failed to extract single listing: {e}")
                    continue
            
            self.logger.info(f"Successfully extracted {len(listings)} listings")
            return listings
            
        except Exception as e:
            raise ScrapingError(f"Failed to extract listings from page: {e}")
    
    def _extract_single_listing(self, element, timestamp: str, db_model_class):
        """
        Extract data from a single listing element.
        
        Args:
            element: Selenium WebElement for the listing
            timestamp: Timestamp string for when scraping occurred
            db_model_class: Database model class for creating listing objects
            
        Returns:
            Listing object or None if extraction fails
        """
        try:
            # Extract title and link
            title_element = element.find_element(By.CLASS_NAME, ELEMENT_CLASS_POSTING_TITLE)
            title = title_element.text.strip()
            link = title_element.get_attribute('href')
            
            if not title or not link:
                self.logger.debug("Skipping listing with missing title or link")
                return None
            
            # Extract Craigslist ID from URL
            cl_id = link.split('/')[-1].removesuffix('.html')
            
            # Extract metadata (time posted and location)
            meta_element = element.find_element(by=By.CLASS_NAME, value=ELEMENT_CLASS_META)
            meta_text = meta_element.text.strip()
            
            # Parse metadata - typically "time_posted\nlocation"
            meta_parts = meta_text.split('\n')
            if len(meta_parts) >= 2:
                time_posted = meta_parts[0].strip()
                location = meta_parts[1].strip()
            else:
                time_posted = meta_text
                location = "Unknown"
            
            # Create listing object
            listing = db_model_class(
                link=link,
                title=title,
                cl_id=cl_id,
                time_posted=time_posted,
                location=location,
                time_scraped=timestamp
            )
            
            return listing
            
        except Exception as e:
            self.logger.warning(f"Failed to extract single listing: {e}")
            return None
    
    def scrape_url(
        self, 
        url: str, 
        timestamp: str, 
        db_model_class
    ) -> List:
        """
        Scrape a single URL and return extracted listings.
        
        Args:
            url: URL to scrape
            timestamp: Timestamp string for when scraping occurred
            db_model_class: Database model class for creating listing objects
            
        Returns:
            List of listing objects
            
        Raises:
            ScrapingError: If scraping fails
        """
        browser = None
        try:
            self.logger.info(f"Starting scrape of URL: {url}")
            browser = self.setup_browser()
            browser.get(url)
            
            listings = self.extract_listings_from_page(browser, timestamp, db_model_class)
            self.logger.success(f"Successfully scraped {len(listings)} listings from {url}")
            
            return listings
            
        except Exception as e:
            self.logger.error(f"Failed to scrape URL {url}: {e}")
            raise ScrapingError(f"Failed to scrape URL {url}: {e}")
        finally:
            if browser:
                try:
                    browser.quit()
                    self.logger.debug("Browser closed successfully")
                except Exception as e:
                    self.logger.warning(f"Error closing browser: {e}")