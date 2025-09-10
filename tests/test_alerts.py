"""
Tests for the alert system.
"""

import pytest
from unittest.mock import Mock, patch

from alerts.alert_manager import SMSAlertSender, DiscordAlertSender, AlertManager
from exceptions import SMSAlertError, DiscordAlertError


class TestSMSAlertSender:
    """Test SMS alert functionality."""
    
    def test_init(self):
        """Test SMS sender initialization."""
        sender = SMSAlertSender(
            account_sid="test_sid",
            auth_token="test_token",
            from_number="+1234567890",
            to_numbers=["+0987654321"]
        )
        assert sender.from_number == "+1234567890"
        assert sender.to_numbers == ["+0987654321"]
    
    @patch('alerts.alert_manager.Client')
    def test_send_alert_success(self, mock_client_class, sample_listing_data):
        """Test successful SMS alert sending."""
        mock_client = Mock()
        mock_message = Mock()
        mock_message.sid = "test_message_sid"
        mock_client.messages.create.return_value = mock_message
        mock_client_class.return_value = mock_client
        
        # Create a mock listing object
        mock_listing = Mock()
        mock_listing.title = sample_listing_data["title"]
        mock_listing.time_posted = sample_listing_data["time_posted"]
        mock_listing.location = sample_listing_data["location"]
        mock_listing.time_scraped = sample_listing_data["time_scraped"]
        mock_listing.link = sample_listing_data["link"]
        
        sender = SMSAlertSender(
            account_sid="test_sid",
            auth_token="test_token",
            from_number="+1234567890",
            to_numbers=["+0987654321"]
        )
        
        sender.send_alert(mock_listing)
        
        mock_client.messages.create.assert_called_once()
    
    @patch('alerts.alert_manager.Client')
    def test_send_alert_failure(self, mock_client_class):
        """Test SMS alert sending failure."""
        mock_client = Mock()
        mock_client.messages.create.side_effect = Exception("Twilio error")
        mock_client_class.return_value = mock_client
        
        sender = SMSAlertSender(
            account_sid="test_sid",
            auth_token="test_token",
            from_number="+1234567890",
            to_numbers=["+0987654321"]
        )
        
        mock_listing = Mock()
        mock_listing.title = "Test"
        mock_listing.time_posted = "Now"
        mock_listing.location = "Here"
        mock_listing.time_scraped = "2023-01-01"
        mock_listing.link = "http://test.com"
        
        with pytest.raises(SMSAlertError):
            sender.send_alert(mock_listing)


class TestDiscordAlertSender:
    """Test Discord alert functionality."""
    
    @patch('alerts.alert_manager.requests.post')
    def test_send_alert_success(self, mock_post, sample_listing_data):
        """Test successful Discord alert sending."""
        mock_response = Mock()
        mock_response.status_code = 204
        mock_post.return_value = mock_response
        
        mock_listing = Mock()
        mock_listing.title = sample_listing_data["title"]
        mock_listing.time_posted = sample_listing_data["time_posted"]
        mock_listing.location = sample_listing_data["location"]
        mock_listing.time_scraped = sample_listing_data["time_scraped"]
        mock_listing.link = sample_listing_data["link"]
        
        sender = DiscordAlertSender(webhook_url="https://discord.com/webhook/test")
        sender.send_alert(mock_listing)
        
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert "json" in kwargs
        assert "content" in kwargs["json"]
    
    @patch('alerts.alert_manager.requests.post')
    def test_send_alert_failure(self, mock_post):
        """Test Discord alert sending failure."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad request"
        mock_post.return_value = mock_response
        
        sender = DiscordAlertSender(webhook_url="https://discord.com/webhook/test")
        
        mock_listing = Mock()
        mock_listing.title = "Test"
        mock_listing.time_posted = "Now"
        mock_listing.location = "Here"
        mock_listing.time_scraped = "2023-01-01"
        mock_listing.link = "http://test.com"
        
        with pytest.raises(DiscordAlertError):
            sender.send_alert(mock_listing)


class TestAlertManager:
    """Test alert manager functionality."""
    
    def test_add_sender(self, mock_logger):
        """Test adding an alert sender."""
        manager = AlertManager(logger=mock_logger)
        mock_sender = Mock()
        mock_sender.__class__.__name__ = "TestSender"
        
        manager.add_sender(mock_sender)
        
        assert len(manager.alert_senders) == 1
        assert manager.alert_senders[0] == mock_sender
    
    def test_send_alerts_empty_list(self, mock_logger):
        """Test sending alerts with empty listing list."""
        manager = AlertManager(logger=mock_logger)
        
        # Should not raise any errors
        manager.send_alerts([])
    
    def test_send_alerts_with_senders(self, mock_logger):
        """Test sending alerts with configured senders."""
        manager = AlertManager(logger=mock_logger)
        
        mock_sender1 = Mock()
        mock_sender2 = Mock()
        manager.add_sender(mock_sender1)
        manager.add_sender(mock_sender2)
        
        mock_listing = Mock()
        mock_listing.title = "Test Listing"
        
        manager.send_alerts([mock_listing])
        
        mock_sender1.send_alert.assert_called_once_with(mock_listing)
        mock_sender2.send_alert.assert_called_once_with(mock_listing)