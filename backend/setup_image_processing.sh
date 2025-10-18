#!/bin/bash
# Setup script for image processing dependencies
# This installs all requirements for the bottom_line_killer scripts

set -e

echo "Setting up image processing environment..."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "Virtual environment activated"
else
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    echo "Virtual environment created and activated"
fi

# Install required packages
echo "Installing dependencies..."
pip install rembg pillow numpy scikit-image onnxruntime

echo "Setup complete! You can now run the image processing scripts."
echo "Example usage:"
echo "  python bottom_line_killer.py static/images/ingredients/salt.png --output static/images/ingredients_clean/salt.png"
echo "  python batch_bottom_line_killer.py static/images/ingredients --extensions png"
