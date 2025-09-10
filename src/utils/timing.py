"""
Timing utilities for the Craigslist scraper.
Handles sleep intervals and timing operations.
"""

import datetime
import logging
import random
import time
from typing import Optional


class SleepManager:
    """Manages sleep intervals with logging."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the sleep manager.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
    
    def sleep_random(self, min_seconds: int, max_seconds: int) -> None:
        """
        Sleep for a random amount of time between min and max seconds.
        
        Args:
            min_seconds: Minimum sleep time in seconds
            max_seconds: Maximum sleep time in seconds
        """
        seconds = random.randint(min_seconds, max_seconds)
        next_iteration = datetime.datetime.now() + datetime.timedelta(seconds=seconds)
        
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        
        current_time = datetime.datetime.now().strftime('%H:%M:%S')
        next_time = next_iteration.strftime('%H:%M:%S')
        
        if minutes > 0:
            sleep_msg = f"{minutes} minutes and {remaining_seconds} seconds"
        else:
            sleep_msg = f"{remaining_seconds} seconds"
        
        self.logger.info(f"[{current_time}] Sleeping for {sleep_msg}")
        self.logger.info(f"[{current_time}] Next iteration at {next_time}")
        
        time.sleep(seconds)
    
    def get_current_timestamp(self, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
        """
        Get current timestamp as formatted string.
        
        Args:
            format_str: Format string for timestamp
            
        Returns:
            Formatted timestamp string
        """
        return datetime.datetime.now().strftime(format_str)