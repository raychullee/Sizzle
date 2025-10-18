"""
Configuration module for the Sizzle backend.

This module loads configuration values from environment variables.
"""

import os
from typing import List

# API Configuration
API_HOST = os.environ.get('API_HOST', '0.0.0.0')
API_PORT = int(os.environ.get('API_PORT', '8000'))
API_DEBUG = os.environ.get('API_DEBUG', 'true').lower() in ('true', 't', '1', 'yes', 'y')
API_CORS_ORIGINS = os.environ.get('API_CORS_ORIGINS', 'http://localhost:3000,http://127.0.0.1:3000').split(',')

# Supabase Configuration
SUPABASE_URL = os.environ.get('SUPABASE_URL', '')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY', '')

# OpenAI Configuration
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
OPENAI_MODEL = os.environ.get('OPENAI_MODEL', 'gpt-4o')
OPENAI_TIMEOUT = int(os.environ.get('OPENAI_TIMEOUT', '120'))

# OCI Storage Configuration
OCI_BUCKET_NAME = os.environ.get('OCI_BUCKET_NAME', 'sizzle-media')
OCI_NAMESPACE = os.environ.get('OCI_NAMESPACE', '')
OCI_REGION = os.environ.get('OCI_REGION', '')
OCI_PAR_URL = os.environ.get('OCI_PAR_URL', '')

# Application Paths
STATIC_DIR = os.environ.get('STATIC_DIR', os.path.join(os.path.dirname(__file__), 'static'))
TEMP_DIR = os.environ.get('TEMP_DIR', os.path.join(os.path.dirname(__file__), 'temp'))

# Other Constants
MAX_RETRIES = 3
DEFAULT_QUERY_TIMEOUT = 30
