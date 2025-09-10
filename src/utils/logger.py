"""
Logging utility module for the Craigslist scraper.
Provides structured logging with colors and proper formatting.
"""

import logging
import sys
from typing import Optional


class ColoredFormatter(logging.Formatter):
    """Custom formatter that adds colors to log levels."""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[94m',     # Blue
        'INFO': '\033[96m',      # Cyan
        'WARNING': '\033[93m',   # Yellow
        'ERROR': '\033[91m',     # Red
        'CRITICAL': '\033[95m',  # Magenta
        'SUCCESS': '\033[92m',   # Green
        'RESET': '\033[0m',      # Reset
        'BOLD': '\033[1m'        # Bold
    }
    
    def format(self, record: logging.LogRecord) -> str:
        """Format the log record with colors."""
        log_color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']
        bold = self.COLORS['BOLD']
        
        # Format the message
        record.levelname = f"{log_color}{bold}{record.levelname}{reset}"
        formatted = super().format(record)
        
        return formatted


def setup_logger(
    name: str = "craigslist_scraper",
    level: str = "INFO",
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    Set up a logger with both console and optional file output.
    
    Args:
        name: Logger name
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path for file logging
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Prevent duplicate handlers if logger already exists
    if logger.handlers:
        return logger
    
    logger.setLevel(getattr(logging, level.upper()))
    
    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = ColoredFormatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger


def log_success(logger: logging.Logger, message: str, *args) -> None:
    """Log a success message with green color."""
    # Create a custom log level for success
    if not hasattr(logging, 'SUCCESS'):
        logging.addLevelName(25, 'SUCCESS')
    
    if logger.isEnabledFor(25):
        logger._log(25, message, args)


# Add success method to logger class
logging.Logger.success = log_success


def get_logger(name: str = "craigslist_scraper") -> logging.Logger:
    """Get an existing logger or create a new one."""
    return logging.getLogger(name)


def welcome_message(logger: logging.Logger) -> None:
    """Display the welcome message using proper logging."""
    welcome_text = """
    ╔══════════════════════════════════════════════════╗
    ║        Welcome to Craigslist Scraper Bot         ║
    ║                                                  ║
    ║  Monitors Craigslist for new listings and       ║
    ║  sends alerts via SMS, Discord, or Email        ║
    ╚══════════════════════════════════════════════════╝
    """
    logger.info(welcome_text)