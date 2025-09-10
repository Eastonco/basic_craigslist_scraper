"""
Tests for the configuration models and validation.
"""

import pytest
from pydantic import ValidationError

from models import Config


class TestConfig:
    """Test configuration validation."""
    
    def test_valid_config(self, sample_config):
        """Test that a valid config is accepted."""
        assert sample_config.urls
        assert isinstance(sample_config.filters, list)
        assert sample_config.db_user == "test_user"
    
    def test_empty_urls_validation(self):
        """Test that empty URLs list raises validation error."""
        with pytest.raises(ValidationError, match="At least one URL must be provided"):
            Config(
                urls=[],
                filters=[],
                send_email_alerts=False,
                send_sms_alerts=False,
                send_discord_alerts=False
            )
    
    def test_sms_validation_missing_fields(self):
        """Test SMS validation when fields are missing."""
        with pytest.raises(ValidationError):
            Config(
                urls=["https://example.craigslist.org/search/zip"],
                send_sms_alerts=True,
                # Missing required SMS fields
                send_email_alerts=False,
                send_discord_alerts=False
            )
    
    def test_discord_validation_missing_webhook(self):
        """Test Discord validation when webhook URL is missing."""
        with pytest.raises(ValidationError):
            Config(
                urls=["https://example.craigslist.org/search/zip"],
                send_discord_alerts=True,
                # Missing discord_webhook_url
                send_email_alerts=False,
                send_sms_alerts=False
            )