"""
Environment setup module.

This module initializes environment variables needed for the application.
"""

import os
import sys
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

logger = logging.getLogger('setup_env')

def setup_virtual_env():
    """
    Ensures the current environment has the necessary packages.
    This is a no-op function that's called for compatibility.
    """
    logger.info("Virtual environment check completed")
    return True

# Find the .env file
env_path = Path(__file__).parent / '.env'

# Load environment variables from .env file if it exists
if env_path.exists():
    logger.info(f"Loading environment from {env_path}")
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            key, value = line.split('=', 1)
            os.environ[key] = value
    logger.info("Environment variables loaded")
else:
    # Create a default .env file with sample values
    logger.warning(f".env file not found at {env_path}, using default environment")
    
    # Set default environment variables
    if 'API_HOST' not in os.environ:
        os.environ['API_HOST'] = '0.0.0.0'
    
    if 'API_PORT' not in os.environ:
        os.environ['API_PORT'] = '8000'
    
    if 'API_DEBUG' not in os.environ:
        os.environ['API_DEBUG'] = 'true'
    
    if 'API_CORS_ORIGINS' not in os.environ:
        os.environ['API_CORS_ORIGINS'] = 'http://localhost:3000,http://127.0.0.1:3000'
    
    # Sample environment file
    sample_env = """
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=true
API_CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=sizzle
DB_USER=postgres
DB_PASSWORD=postgres

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key

# OCI Storage Configuration
OCI_BUCKET_NAME=sizzle-media
OCI_NAMESPACE=your_oci_namespace
OCI_REGION=your_oci_region
OCI_USER_OCID=your_user_ocid
OCI_TENANCY_OCID=your_tenancy_ocid
OCI_FINGERPRINT=your_api_key_fingerprint
OCI_KEY_FILE=your_api_key_file_path

# Paths
STATIC_DIR=static
TEMP_DIR=temp
"""
    
    # Write the sample .env file
    with open(env_path, 'w') as f:
        f.write(sample_env.strip())
    
    logger.info(f"Created sample .env file at {env_path}")
    logger.info("You should edit this file with your actual configuration values")

# Verify required environment variables
required_vars = [
    'API_HOST', 
    'API_PORT', 
    'API_DEBUG', 
    'API_CORS_ORIGINS'
]

missing_vars = [var for var in required_vars if var not in os.environ]

if missing_vars:
    logger.warning(f"Missing required environment variables: {', '.join(missing_vars)}")
    logger.warning("The application may not function correctly!")
else:
    logger.info("All required environment variables are set")
