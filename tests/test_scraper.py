"""
Tests for the scraper functionality.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from scraper.craigslist_scraper import CraigslistScraper
from exceptions import BrowserError, ScrapingError


class TestCraigslistScraper:
    """Test the CraigslistScraper class."""
    
    def test_init(self, mock_logger):
        """Test scraper initialization."""
        scraper = CraigslistScraper(logger=mock_logger)
        assert scraper.logger == mock_logger
    
    @patch('scraper.craigslist_scraper.webdriver.Firefox')
    def test_setup_browser_success(self, mock_firefox, mock_logger):
        """Test successful browser setup."""
        mock_browser = Mock()
        mock_firefox.return_value = mock_browser
        
        scraper = CraigslistScraper(logger=mock_logger)
        browser = scraper.setup_browser()
        
        assert browser == mock_browser
        mock_browser.implicitly_wait.assert_called_once()
    
    @patch('scraper.craigslist_scraper.webdriver.Firefox')
    def test_setup_browser_failure(self, mock_firefox, mock_logger):
        """Test browser setup failure."""
        mock_firefox.side_effect = Exception("Firefox not found")
        
        scraper = CraigslistScraper(logger=mock_logger)
        
        with pytest.raises(BrowserError, match="Failed to setup Firefox browser"):
            scraper.setup_browser()
    
    def test_extract_single_listing_success(self, mock_logger, sample_listing_data):
        """Test successful single listing extraction."""
        # Mock the WebElement
        mock_element = Mock()
        mock_title_element = Mock()
        mock_title_element.text = sample_listing_data["title"]
        mock_title_element.get_attribute.return_value = sample_listing_data["link"]
        
        mock_meta_element = Mock()
        mock_meta_element.text = f"{sample_listing_data['time_posted']}\\n{sample_listing_data['location']}"
        
        mock_element.find_element.side_effect = [mock_title_element, mock_meta_element]
        
        # Mock the db model class
        mock_db_class = Mock()
        mock_listing = Mock()
        mock_db_class.return_value = mock_listing
        
        scraper = CraigslistScraper(logger=mock_logger)
        result = scraper._extract_single_listing(
            mock_element, 
            sample_listing_data["time_scraped"], 
            mock_db_class
        )
        
        assert result == mock_listing
        mock_db_class.assert_called_once()
    
    def test_extract_single_listing_failure(self, mock_logger):
        """Test single listing extraction failure."""
        mock_element = Mock()
        mock_element.find_element.side_effect = Exception("Element not found")
        
        scraper = CraigslistScraper(logger=mock_logger)
        result = scraper._extract_single_listing(mock_element, "2023-01-01", Mock())
        
        assert result is None