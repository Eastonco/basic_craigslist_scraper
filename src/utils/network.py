"""
Network utilities for handling HTTP requests in different environments.
Provides SSL-aware request handling for Docker and local environments.
"""

import logging
from typing import Optional, Dict, Any
import requests
import urllib3

from exceptions import AlertError


def make_robust_request(
    url: str, 
    method: str = "POST", 
    data: Optional[Dict[str, Any]] = None,
    timeout: int = 10,
    logger: Optional[logging.Logger] = None
) -> requests.Response:
    """
    Make a robust HTTP request with SSL fallback handling.
    
    Args:
        url: URL to request
        method: HTTP method (GET, POST, etc.)
        data: Request data/payload
        timeout: Request timeout
        logger: Optional logger instance
        
    Returns:
        Response object
        
    Raises:
        AlertError: If all request attempts fail
    """
    if logger is None:
        logger = logging.getLogger(__name__)
    
    # First attempt: Standard request with SSL verification
    try:
        logger.debug(f"Attempting {method} request to {url} with SSL verification")
        
        if method.upper() == "POST":
            response = requests.post(url, json=data, timeout=timeout, verify=True)
        else:
            response = requests.get(url, timeout=timeout, verify=True)
            
        logger.debug(f"Request successful with SSL verification: {response.status_code}")
        return response
        
    except requests.exceptions.SSLError as ssl_error:
        logger.warning(f"SSL verification failed: {ssl_error}")
        logger.info("Attempting request without SSL verification...")
        
        # Second attempt: Disable SSL verification
        try:
            # Suppress SSL warnings for this request
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            
            if method.upper() == "POST":
                response = requests.post(url, json=data, timeout=timeout, verify=False)
            else:
                response = requests.get(url, timeout=timeout, verify=False)
                
            logger.warning(f"Request successful without SSL verification: {response.status_code}")
            return response
            
        except Exception as fallback_error:
            logger.error(f"Request failed even without SSL verification: {fallback_error}")
            raise AlertError(f"All request attempts failed. SSL Error: {ssl_error}, Fallback Error: {fallback_error}")
    
    except Exception as general_error:
        logger.error(f"Request failed with general error: {general_error}")
        raise AlertError(f"Request failed: {general_error}")