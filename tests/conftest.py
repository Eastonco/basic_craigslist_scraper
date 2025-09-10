"""
Test configuration for the Craigslist scraper.
Provides common test fixtures and utilities.
"""

import pytest
from unittest.mock import Mock

from models import Config
from utils.logger import setup_logger


@pytest.fixture
def sample_config():
    """Sample configuration for testing."""
    return Config(
        urls=["https://example.craigslist.org/search/zip"],
        filters=["dirt", "soil"],
        send_email_alerts=False,
        send_sms_alerts=False,
        send_discord_alerts=False,
        combine_texts=False,
        db_user="test_user",
        db_password="test_password",
        db_host="localhost",
        db_port="5432",
        db_name="test_db"
    )


@pytest.fixture
def mock_logger():
    """Mock logger for testing."""
    return Mock()


@pytest.fixture
def test_logger():
    """Real logger configured for testing."""
    return setup_logger("test_scraper", level="DEBUG")


@pytest.fixture
def sample_listing_data():
    """Sample listing data for testing."""
    return {
        "link": "https://example.craigslist.org/zip/d/test-item/1234567890.html",
        "title": "Test Item",
        "cl_id": "1234567890",
        "time_posted": "5 mins ago",
        "location": "Test City",
        "time_scraped": "2023-01-01 12:00:00"
    }