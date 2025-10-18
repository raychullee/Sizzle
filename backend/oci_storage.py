"""
Oracle Cloud Infrastructure (OCI) Object Storage integration module.

This module provides functionality for interacting with OCI Object Storage,
including file uploads, PAR generation, and object listing.
"""

import os
import io
import datetime
import mimetypes
from typing import List, Dict, Optional, Any, BinaryIO, Tuple
from pathlib import Path
import requests
import json

# Set up mime types
mimetypes.init()

# Set a flag indicating if OCI is available
OCI_AVAILABLE = False

# Try to import OCI SDK
try:
    import oci
    from oci.config import from_file
    OCI_AVAILABLE = True
except ImportError:
    OCI_AVAILABLE = False

# Local imports
from config import (
    OCI_BUCKET_NAME, OCI_NAMESPACE, STATIC_DIR
)
from utils import logger, log_exception, format_oci_url

# Add PAR URL from config
from config import OCI_PAR_URL

class OCIObjectStorage:
    """
    Class to handle Oracle Cloud Infrastructure Object Storage operations.
    
    This class provides functionality for uploading objects to OCI buckets,
    generating pre-authenticated requests (PARs), and listing objects.
    """
    
    def __init__(self):
        """Initialize the OCIObjectStorage instance."""
        self.client = None
        self.namespace = OCI_NAMESPACE
        self.bucket_name = OCI_BUCKET_NAME
        self.configured = False
        
        # Using PAR directly, so we don't need the OCI SDK for uploads
        self.par_configured = bool(OCI_PAR_URL)
        
        # Try to initialize if OCI is available but don't require it
        if OCI_AVAILABLE:
            self._try_initialize()
    
    def _try_initialize(self) -> bool:
        """
        Try to initialize the OCI Object Storage client.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Since we're using PAR, we don't need full OCI initialization
            self.configured = self.par_configured
            
            # Log configuration status
            if self.configured:
                logger.info(f"OCI Object Storage PAR configured for bucket: {self.bucket_name}")
            else:
                logger.warning("OCI Object Storage PAR not configured")
                
            return self.configured
        except Exception as e:
            log_exception(e, "Failed to initialize OCI Object Storage")
            self.configured = False
            return False
    
    def upload_file(self, file_path: str, object_name: Optional[str] = None) -> Tuple[bool, str]:
        """
        Upload a file to OCI Object Storage using PAR URL.
        
        Args:
            file_path: Path to the file to upload
            object_name: Name to use for the object in storage (defaults to file basename)
            
        Returns:
            Tuple of (success, object_name or error message)
        """
        if not self.par_configured:
            return False, "OCI PAR not configured"
            
        try:
            # Prepare the file and object name
            file_path = Path(file_path)
            if not file_path.exists():
                return False, f"File not found: {file_path}"
                
            # Use the provided object name or default to the file basename
            if not object_name:
                object_name = file_path.name
                
            # Get content type
            content_type, _ = mimetypes.guess_type(str(file_path))
            if not content_type:
                content_type = 'application/octet-stream'
                
            # Upload using the PAR URL
            with open(file_path, 'rb') as f:
                par_upload_url = f"{OCI_PAR_URL.rstrip('/')}/{object_name}"
                
                # Make the PUT request
                response = requests.put(
                    par_upload_url,
                    data=f,
                    headers={
                        'Content-Type': content_type
                    }
                )
                
                if response.status_code in (200, 201):
                    logger.info(f"File uploaded successfully: {object_name}")
                    return True, object_name
                else:
                    error_msg = f"Failed to upload file. Status: {response.status_code}, Response: {response.text}"
                    logger.error(error_msg)
                    return False, error_msg
                    
        except Exception as e:
            error_msg = f"Error uploading file: {str(e)}"
            log_exception(e, error_msg)
            return False, error_msg
    
    def get_object_url(self, object_name: str) -> str:
        """
        Get a URL for an object using the PAR.
        
        Args:
            object_name: The name of the object
            
        Returns:
            The URL for the object
        """
        if not self.par_configured:
            return ""
            
        # Clean up the object name
        object_name = object_name.lstrip('/')
        
        # Construct the URL using the PAR
        return f"{OCI_PAR_URL.rstrip('/')}/{object_name}"
    
    def object_exists(self, object_name: str) -> bool:
        """
        Check if an object exists in the bucket.
        
        Args:
            object_name: The name of the object to check
            
        Returns:
            True if the object exists, False otherwise
        """
        if not self.par_configured:
            return False
            
        try:
            # Clean up the object name
            object_name = object_name.lstrip('/')
            
            # Construct the URL using the PAR
            url = f"{OCI_PAR_URL.rstrip('/')}/{object_name}"
            
            # Make a HEAD request to check if the object exists
            response = requests.head(url)
            
            # 200 means the object exists
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Error checking if object exists: {str(e)}")
            return False
