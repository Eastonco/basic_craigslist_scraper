"""
Constants for the Craigslist scraper application.
Centralizes magic numbers, timeouts, and configuration defaults.
"""

from typing import Final

# Selenium and scraping constants
BROWSER_IMPLICIT_WAIT: Final[int] = 1
PAGE_LOAD_TIMEOUT: Final[int] = 5
ELEMENT_CLASS_SEARCH_RESULT: Final[str] = 'cl-search-result'
ELEMENT_CLASS_POSTING_TITLE: Final[str] = 'posting-title'
ELEMENT_CLASS_META: Final[str] = 'meta'

# Sleep intervals (in seconds)
MIN_SLEEP_BETWEEN_URLS: Final[int] = 5
MAX_SLEEP_BETWEEN_URLS: Final[int] = 15
MIN_SLEEP_BETWEEN_CYCLES: Final[int] = 45
MAX_SLEEP_BETWEEN_CYCLES: Final[int] = 90

# Error handling
MAX_ERROR_COUNT: Final[int] = 3

# Database defaults
DEFAULT_DB_HOST: Final[str] = 'localhost'
DEFAULT_DB_PORT: Final[str] = '5432'
DEFAULT_DB_USER: Final[str] = 'postgres'
DEFAULT_DB_PASSWORD: Final[str] = 'password'
DEFAULT_DB_NAME: Final[str] = 'craigslist'

# Email configuration
SMTP_SERVER: Final[str] = 'smtp.gmail.com'
SMTP_PORT: Final[int] = 465

# HTTP status codes
HTTP_OK: Final[int] = 200
HTTP_NO_CONTENT: Final[int] = 204

# Default configuration paths
DEFAULT_CONFIG_PATH: Final[str] = './config/config.json'
DEFAULT_SERVER_CONFIG_PATH: Final[str] = './config/serverConfig.json'

# Logging
DEFAULT_LOG_LEVEL: Final[str] = 'INFO'
DEFAULT_DATE_FORMAT: Final[str] = '%Y-%m-%d %H:%M:%S'
DEFAULT_TIME_FORMAT: Final[str] = '%H:%M:%S'