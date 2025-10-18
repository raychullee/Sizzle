#!/usr/bin/env python3
"""
Batch Bottom Line Shadow Killer

This script processes all images in a directory with extreme focus on
removing thin shadow lines at the bottom of objects.

Usage:
    python batch.py path/to/directory [--extensions jpg png jpeg]

Requirements:
    pip install rembg pillow numpy scikit-image
"""

import os
import sys
import argparse
import time
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
        Tuple of (success, output_path)
    """
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
            output_path = input_path.parent / f"{input_path.stem}_nobg.png"
        else:
            output_path = Path(output_path)
        
        # Save the output image
        final_output.save(output_path, format="PNG")
        
        return (True, output_path)
    
    except Exception as e:
        print(f"Error processing {input_path.name}: {e}")
        return (False, None)


def process_directory(directory_path, extensions=None):
    """
    Process all images in a directory.
    
    Args:
        directory_path: Path to the directory containing images
        extensions: List of file extensions to process (default: ['jpg', 'jpeg', 'png'])
        
    Returns:
        Dictionary with statistics
    """
    if extensions is None:
        extensions = ['jpg', 'jpeg', 'png']
    
    # Convert extensions to lowercase and ensure they start with a dot
    extensions = [f".{ext.lower().lstrip('.')}" for ext in extensions]
    
    # Get all image files, excluding any that are already processed (_nobg suffix)
    directory = Path(directory_path)
    image_files = [
        f for f in directory.iterdir()
        if f.is_file() and f.suffix.lower() in extensions and not f.name.endswith("_nobg.png")
        and not f.name.endswith("_final.png") and not f.name.endswith("_noshadow.png")
        and not f.name.endswith("_ultimate.png") and not f.name.endswith("_perfect.png")
        and not f.name.endswith("_clean.png")
    ]
    
    if not image_files:
        print(f"No suitable images found in {directory}")
        return {"total": 0, "success": 0, "failed": 0}
    
    print(f"Found {len(image_files)} images to process")
    
    # Process images sequentially
    successful = 0
    failed = 0
    start_time = time.time()
    
    for i, image_path in enumerate(image_files, 1):
        print(f"[{i}/{len(image_files)}] Processing {image_path.name}...")
        success, output_path = kill_bottom_lines(image_path)
        
        if success:
            successful += 1
            print(f"✓ Processed: {image_path.name} -> {output_path.name}")
        else:
            failed += 1
            print(f"✗ Failed: {image_path.name}")
            
    # Calculate elapsed time
    elapsed_time = time.time() - start_time
    
    # Print summary
    print(f"\nCompleted in {elapsed_time:.2f} seconds")
    print(f"Processed {len(image_files)} images: {successful} successful, {failed} failed")
    
    return {
        "total": len(image_files),
        "success": successful,
        "failed": failed,
        "elapsed_time": elapsed_time
    }


def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Batch process to remove bottom shadow lines')
    parser.add_argument('directory', type=str, help='Directory containing images to process')
    parser.add_argument('--extensions', nargs='+', default=['jpg', 'jpeg', 'png'],
                       help='File extensions to process (default: jpg, jpeg, png)')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Process the directory
    process_directory(args.directory, args.extensions)


if __name__ == "__main__":
    main()
