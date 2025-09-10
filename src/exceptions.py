"""
Custom exceptions for the Craigslist scraper application.
Provides specific error types for better error handling and debugging.
"""


class CraigslistScraperError(Exception):
    """Base exception for all scraper-related errors."""
    pass


class ConfigurationError(CraigslistScraperError):
    """Raised when there's an issue with configuration."""
    pass


class DatabaseError(CraigslistScraperError):
    """Raised when there's a database-related error."""
    pass


class ScrapingError(CraigslistScraperError):
    """Raised when there's an error during the scraping process."""
    pass


class BrowserError(ScrapingError):
    """Raised when there's an issue with browser setup or operation."""
    pass


class AlertError(CraigslistScraperError):
    """Raised when there's an error sending alerts."""
    pass


class EmailAlertError(AlertError):
    """Raised when there's an error sending email alerts."""
    pass


class SMSAlertError(AlertError):
    """Raised when there's an error sending SMS alerts."""
    pass


class DiscordAlertError(AlertError):
    """Raised when there's an error sending Discord alerts."""
    pass


class ValidationError(CraigslistScraperError):
    """Raised when data validation fails."""
    pass