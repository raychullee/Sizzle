#!/usr/bin/env python3
"""
Bottom Line Shadow Killer

This script specifically targets thin shadow lines at the bottom of objects,
with extreme aggression toward any semi-transparency in the bottom portion.

Usage:
    python remove_bg.py path/to/image.jpg [--output path/to/output.png]

Requirements:
    pip install rembg pillow numpy scikit-image
"""

import os
import sys
import argparse
import numpy as np
from pathlib import Path
from rembg import remove, new_session
from PIL import Image, ImageEnhance, ImageFilter
from skimage import morphology, filters


def kill_bottom_lines(input_path, output_path=None):
    """
    Remove the background and specifically target bottom shadow lines.
    
    Args:
        input_path: Path to the input image file
        output_path: Path for the output image (optional)
    
    Returns:
        Path to the output image file
    """
    # Validate that input file exists
    input_path = Path(input_path)
    if not input_path.exists():
        print(f"Error: File not found: {input_path}")
        return None
    
    try:
        # Read the input image
        input_image = Image.open(input_path).convert("RGBA")
        
        # Step 1: Use rembg with best settings for outline preservation
        model_name = "u2net"  # Best model for detailed objects
        session = new_session(model_name)
        
        # Use alpha matting for better edge quality
        output = remove(
            input_image,
            session=session,
            alpha_matting=True,
            alpha_matting_foreground_threshold=240,  # More aggressive foreground detection
            alpha_matting_background_threshold=5,    # Lower to include more foreground details
            alpha_matting_erode_size=5               # Lower to preserve details
        )
        
        # Step 2: Convert to numpy array for precise pixel manipulation
        output_array = np.array(output)
        
        # Get RGB and alpha channels
        rgb = output_array[:, :, :3]
        alpha = output_array[:, :, 3]
        
        # Step 3: Create extremely aggressive shadow detection
        # Calculate RGB variance (higher variance = more colorful, lower = gray/shadow)
        r, g, b = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]
        rgb_variance = np.max([
            np.abs(r.astype(np.int16) - g.astype(np.int16)),
            np.abs(g.astype(np.int16) - b.astype(np.int16)),
            np.abs(r.astype(np.int16) - b.astype(np.int16))
        ], axis=0)
        
        # Step 4: Create height-based analysis to target bottom sections
        height, width = alpha.shape
        y_coords = np.arange(height).reshape(-1, 1)
        y_normalized = y_coords / height  # 0 at top, 1 at bottom
        
        # Create masks for different parts of image - getting more aggressive toward bottom
        bottom_half = y_normalized > 0.5
        bottom_third = y_normalized > 0.67
        bottom_fifth = y_normalized > 0.8
        bottom_tenth = y_normalized > 0.9
        
        # Step 5: Multi-layer shadow detection with extreme focus on bottom areas
        
        # Normal shadow detection (semi-transparent + low color variance)
        shadow_mask = (alpha > 0) & (alpha < 230) & (rgb_variance < 40)
        
        # More aggressive in bottom half
        bottom_shadow_mask = bottom_half & (alpha > 0) & (alpha < 245) & (rgb_variance < 50)
        
        # Even more aggressive in bottom third
        bottom_third_mask = bottom_third & (alpha > 0) & (alpha < 255) & (rgb_variance < 70)
        
        # Ultra aggressive for bottom fifth - almost any semi-transparency is considered shadow
        bottom_fifth_mask = bottom_fifth & (alpha > 0) & (alpha < 255)
        
        # EXTREME for bottom tenth - remove absolutely everything
        bottom_edge_mask = bottom_tenth & (alpha > 0)
        
        # Combine all masks
        combined_shadow_mask = shadow_mask | bottom_shadow_mask | bottom_third_mask | bottom_fifth_mask | bottom_edge_mask
        
        # Step 6: Apply specific horizontal line detection for bottom shadow lines
        
        # Detect horizontal edges using Sobel filter which is good for finding lines
        sobel_y = filters.sobel_h(alpha)
        horizontal_line_mask = np.zeros_like(alpha, dtype=bool)
        
        # Look for horizontal lines in the bottom third
        for y in range(int(height * 0.67), height):
            # Get horizontal gradient values for this row
            row = sobel_y[y, :]
            
            # Look for strong horizontal gradients (likely shadow edges)
            for x in range(width - 10):
                # If we detect potential horizontal edge
                if abs(row[x]) > 5:  # Threshold for edge detection
                    # Mark this and neighboring pixels as shadow line
                    horizontal_line_mask[y, x-5:x+5] = True
        
        # Step 7: Apply bottom clearing to ensure no shadow lines remain
        # Create a mask that clears any semi-transparent pixels in a small margin above detected lines
        bottom_clear_mask = np.zeros_like(alpha, dtype=bool)
        
        # For each potential shadow line, clear pixels above it
        for y in range(height-1, int(height * 0.67), -1):
            for x in range(width):
                if horizontal_line_mask[y, x]:
                    # Clear 10 pixels above this point
                    for up in range(1, 11):
                        if y-up >= 0:
                            bottom_clear_mask[y-up, x] = True
        
        # Step 8: Combine all masks
        final_shadow_mask = combined_shadow_mask | horizontal_line_mask | bottom_clear_mask
        
        # Step 9: Apply extreme morphological operations on the bottom area
        # Convert shadow mask to binary image
        shadow_binary = final_shadow_mask.astype(np.uint8)
        
        # Apply dilation to ensure all shadow components are connected
        dilated_shadow = morphology.binary_dilation(shadow_binary, morphology.disk(5))
        
        # Apply erosion specifically to the outline of the main object to preserve detail
        # We don't want to erode the entire mask, only the bottom shadow areas
        eroded_shadow = dilated_shadow.copy()
        
        # Only apply erosion to bottom half to preserve top details
        eroded_shadow[0:int(height * 0.5), :] = shadow_binary[0:int(height * 0.5), :]
        
        # Step 10: Apply the shadow mask to make shadow areas fully transparent
        new_alpha = alpha.copy()
        new_alpha[eroded_shadow > 0] = 0
        
        # Step 11: Special fix for the absolute bottom pixels
        # Make the bottom 5 rows completely transparent to ensure no shadow lines
        new_alpha[height-5:height, :] = 0
        
        # Step 12: Create the final image with original colors but no shadows
        output_array[:, :, 3] = new_alpha
        final_output = Image.fromarray(output_array)
        
        # Step 13: Apply minimal post-processing to maintain quality
        # Subtle sharpening just to refine edges
        final_output = final_output.filter(ImageFilter.SHARPEN)
        
        # Create output path if not provided
        if output_path is None:
            output_path = input_path.parent / f"{input_path.stem}_clean.png"
        else:
            output_path = Path(output_path)
        
        # Save the output image
        final_output.save(output_path, format="PNG")
        
        print(f"Bottom shadow lines completely eliminated! Saved to: {output_path}")
        return output_path
    
    except Exception as e:
        print(f"Error: Failed to process image: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Remove ALL shadow lines from images')
    parser.add_argument('image_path', type=str, help='Path to the input image file')
    parser.add_argument('--output', type=str, help='Output path (optional)')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Process the image
    kill_bottom_lines(args.image_path, args.output)


if __name__ == "__main__":
    main()
