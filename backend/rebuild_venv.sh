#!/bin/bash

# Script to recreate the virtual environment and install requirements
echo "Rebuilding the virtual environment..."

# Remove old virtual environment
rm -rf venv

# Create new virtual environment
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt

# Test the installation
echo "Testing the Supabase installation..."
python -c "import supabase; print(f'Supabase version: {supabase.__version__}')"

echo "Virtual environment has been rebuilt."
