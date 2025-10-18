"""
Utility functions for the Sizzle backend application.

This module provides shared functionality used across different parts of the
backend, including error handling, logging, URL formatting, and other common operations.
"""

import os
import sys
import logging
import traceback
import json
from config import MAX_RETRIES, DEFAULT_QUERY_TIMEOUT as DEFAULT_TIMEOUT
from typing import Dict, Any, Optional
from urllib.parse import urlparse, parse_qs

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("sizzle")

# Constants already defined in config.py


# Using centralized logger instead of individual loggers


def format_oci_url(url: str) -> str:
    """
    Formats an Oracle Cloud Infrastructure URL to ensure it has proper access tokens.
    
    Args:
        url: The original OCI URL
        
    Returns:
        A properly formatted OCI URL with the correct access parameters
    """
    if not url or 'objectstorage' not in url:
        return url
        
    try:
        parsed_url = urlparse(url)
        
        # Already has a proper access token
        if '/p/' in parsed_url.path:
            return url
            
        # Extract namespace, bucket and object
        path = parsed_url.path
        namespace = ""
        bucket = ""
        object_name = ""
        
        # Extract namespace
        n_index = path.find('/n/')
        if n_index >= 0:
            after_n = path[n_index + 3:]
            next_slash = after_n.find('/')
            namespace = after_n[:next_slash] if next_slash > 0 else after_n
            
        # Extract bucket
        b_index = path.find('/b/')
        if b_index >= 0:
            after_b = path[b_index + 3:]
            next_slash = after_b.find('/')
            bucket = after_b[:next_slash] if next_slash > 0 else after_b
            
        # Extract object name
        o_index = path.find('/o/')
        if o_index >= 0:
            object_name = path[o_index + 3:]
            
        # If we have all components, construct a proper PAR URL
        if namespace and bucket and object_name:
            return f"{parsed_url.scheme}://{parsed_url.netloc}/p/auto-par-token/n/{namespace}/b/{bucket}/o/{object_name}"
    except Exception as e:
        logger.error(f"Error formatting OCI URL {url}: {str(e)}")
        
    # Return original if anything fails
    return url


def log_exception(e: Exception, context: str = "") -> None:
    """
    Logs an exception with optional context information.
    
    Args:
        e: The exception to log
        context: Additional context about where/why the exception occurred
    """
    error_msg = f"{context}: {str(e)}" if context else str(e)
    logger.error(error_msg)
    logger.debug(traceback.format_exc())


def safe_get_env(key: str, default: str = None) -> str:
    """
    Safely gets an environment variable with a default value.
    
    Args:
        key: The environment variable name
        default: The default value if the environment variable is not set
        
    Returns:
        The environment variable value or the default
    """
    return os.environ.get(key, default)


def parse_json_safely(json_str: str, default: Any = None) -> Any:
    """
    Safely parses a JSON string with error handling.
    
    Args:
        json_str: The JSON string to parse
        default: Default value to return if parsing fails
        
    Returns:
        The parsed JSON object or the default value
    """
    if not json_str:
        return default
        
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        logger.error(f"Failed to parse JSON: {json_str[:100]}...")
        return default


def format_api_response(data: Any = None, status: str = "success", 
                       message: str = "", status_code: int = 200) -> Dict[str, Any]:
    """
    Creates a standardized API response format.
    
    Args:
        data: The data to include in the response
        status: Status indicator (success, error, etc.)
        message: Optional message to include
        status_code: HTTP status code
        
    Returns:
        A formatted API response dictionary
    """
    response = {
        "status": status,
        "status_code": status_code
    }
    
    if data is not None:
        response["data"] = data
        
    if message:
        response["message"] = message
        
    return response


def format_error_response(message: str, status_code: int = 400, 
                         details: Any = None) -> Dict[str, Any]:
    """
    Creates a standardized error response.
    
    Args:
        message: Error message
        status_code: HTTP status code
        details: Optional additional error details
        
    Returns:
        A formatted error response dictionary
    """
    response = {
        "status": "error",
        "status_code": status_code,
        "message": message
    }
    
    if details is not None:
        response["details"] = details
        
    return response
