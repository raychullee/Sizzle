#!/usr/bin/env python3
"""
Installation script for the Sizzle backend.

This script sets up the Python environment, creates necessary directories,
and installs required dependencies.
"""

import os
import sys
import subprocess
import platform
import venv
from pathlib import Path


def create_virtual_env(venv_path: str) -> None:
    """
    Create a Python virtual environment.
    
    Args:
        venv_path: Path where to create the virtual environment
    """
    print(f"Creating virtual environment at {venv_path}...")
    venv.create(venv_path, with_pip=True)
    print("Virtual environment created successfully.")


def install_dependencies(venv_path: str, requirements_file: str) -> None:
    """
    Install dependencies from a requirements file.
    
    Args:
        venv_path: Path to the virtual environment
        requirements_file: Path to the requirements.txt file
    """
    # Determine the Python executable in the virtual environment
    if platform.system() == "Windows":
        python_executable = os.path.join(venv_path, "Scripts", "python.exe")
    else:
        python_executable = os.path.join(venv_path, "bin", "python")
    
    # Check if the executable exists
    if not os.path.exists(python_executable):
        print(f"Error: Python executable not found at {python_executable}")
        sys.exit(1)
    
    print(f"Installing dependencies from {requirements_file}...")
    try:
        subprocess.check_call([
            python_executable, 
            "-m", "pip", "install", "-r", requirements_file
        ])
        print("Dependencies installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {str(e)}")
        sys.exit(1)


def create_directories() -> None:
    """
    Create necessary directories for the application.
    """
    directories = [
        "static/images/ingredients",
        "static/images/actions",
        "static/images/steps",
        "static/animations/actions",
        "static/animations/ingredients",
        "static/animations/generated",
        "temp"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"Created directory: {directory}")


def create_env_file() -> None:
    """
    Create a .env file if it doesn't exist.
    """
    env_file = ".env"
    if not os.path.exists(env_file):
        with open(env_file, "w") as f:
            f.write("""# Sizzle Backend Configuration

# Database configuration
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=postgres
DB_NAME=sizzle
# Or use DATABASE_URL for a connection string:
# DATABASE_URL=postgresql://user:password@host:port/dbname

# Supabase configuration
SUPABASE_URL=
SUPABASE_KEY=
SUPABASE_SERVICE_KEY=

# Oracle Cloud Infrastructure configuration
OCI_BUCKET_NAME=sizzle-images
OCI_CONFIG_FILE=~/.oci/config
OCI_CONFIG_PROFILE=DEFAULT
OCI_NAMESPACE=

# API configuration
API_PORT=8000
API_HOST=0.0.0.0
API_DEBUG=True
API_CORS_ORIGINS=*

# OpenAI configuration
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4
OPENAI_TIMEOUT=60

# Logging configuration
LOG_LEVEL=INFO
""")
        print(f"Created .env file. Please edit it to set your configuration values.")
    else:
        print(".env file already exists.")


def main() -> None:
    """
    Main installation function.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(base_dir)
    
    venv_path = os.path.join(base_dir, "venv")
    requirements_file = os.path.join(base_dir, "requirements.txt")
    
    print("Starting Sizzle backend installation...")
    
    # Create virtual environment if it doesn't exist
    if not os.path.exists(venv_path):
        create_virtual_env(venv_path)
    else:
        print(f"Virtual environment already exists at {venv_path}")
    
    # Install dependencies
    install_dependencies(venv_path, requirements_file)
    
    # Create necessary directories
    create_directories()
    
    # Create .env file
    create_env_file()
    
    print("\nInstallation completed successfully!")
    print("\nNext steps:")
    print("1. Edit the .env file to set your configuration values")
    print("2. Configure database settings")
    print("3. Start the backend with: python run_sizzle.py")


if __name__ == "__main__":
    main()
