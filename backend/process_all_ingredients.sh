#!/bin/bash
# Process all ingredient images to remove backgrounds and shadows
# Usage: ./process_all_ingredients.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Make sure dependencies are installed
if [ ! -f venv/bin/activate ]; then
    echo "Environment not set up. Running setup script first..."
    ./setup_image_processing.sh
else
    source venv/bin/activate
fi

# Create output directory if it doesn't exist
mkdir -p static/images/ingredients_clean

# Process all png files in the ingredients directory
echo "Processing all ingredient images..."
python batch_bottom_line_killer.py static/images/ingredients --extensions png

echo "Processing complete! Clean images are in static/images/ingredients_clean/"
