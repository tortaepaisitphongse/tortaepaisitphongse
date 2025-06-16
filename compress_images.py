"""
Image Compressor for Astro Assets
Compresses images in src/assets/ while maintaining good quality for web use.
"""

import os
import sys
from PIL import Image, ImageOps
import argparse


def compress_image(input_path, output_path=None, quality=75, max_width=1200, max_height=1200):
    """
    Compress an image while maintaining aspect ratio and quality.
    
    Args:
        input_path (str): Path to input image
        output_path (str): Path for output image (if None, overwrites original)
        quality (int): JPEG quality (1-100, higher = better quality)
        max_width (int): Maximum width in pixels
        max_height (int): Maximum height in pixels
    """
    try:
        # Open and process image
        with Image.open(input_path) as img:
            # Convert to RGB if necessary (handles PNG, etc.)
            if img.mode in ('RGBA', 'LA', 'P'):
                # Create white background for transparency
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Auto-rotate based on EXIF data
            img = ImageOps.exif_transpose(img)
            
            # Get original dimensions
            original_width, original_height = img.size
            original_size = os.path.getsize(input_path)
            
            # Resize if too large
            if original_width > max_width or original_height > max_height:
                img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
                print(f"  Resized from {original_width}x{original_height} to {img.size[0]}x{img.size[1]}")
            
            # Set output path
            if output_path is None:
                output_path = input_path
            
            # Save compressed image
            img.save(output_path, 'JPEG', quality=quality, optimize=True)
            
            # Report results
            new_size = os.path.getsize(output_path)
            compression_ratio = (1 - new_size / original_size) * 100
            
            print(f"  Original: {original_size / 1024 / 1024:.1f}MB")
            print(f"  Compressed: {new_size / 1024 / 1024:.1f}MB")
            print(f"  Saved: {compression_ratio:.1f}%")
            
            return True
            
    except Exception as e:
        print(f"  Error: {e}")
        return False


def find_images(directory, extensions=('.jpg', '.jpeg', '.png', '.bmp', '.tiff')):
    """Find all image files in directory and subdirectories."""
    image_files = []
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(extensions):
                image_files.append(os.path.join(root, file))
    
    return image_files


def main():
    parser = argparse.ArgumentParser(description='Compress images for web use')
    parser.add_argument('--directory', '-d', default='src/assets', 
                       help='Directory to search for images (default: src/assets)')
    parser.add_argument('--quality', '-q', type=int, default=75,
                       help='JPEG quality 1-100 (default: 75)')
    parser.add_argument('--max-width', type=int, default=1200,
                       help='Maximum width in pixels (default: 1200)')
    parser.add_argument('--max-height', type=int, default=1200,
                       help='Maximum height in pixels (default: 1200)')
    parser.add_argument('--backup', '-b', action='store_true',
                       help='Create backup of original files')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be compressed without doing it')
    
    args = parser.parse_args()
    
    # Check if directory exists
    if not os.path.exists(args.directory):
        print(f"Error: Directory '{args.directory}' not found!")
        sys.exit(1)
    
    # Find all images
    images = find_images(args.directory)
    
    if not images:
        print(f"No images found in '{args.directory}'")
        return
    
    print(f"Found {len(images)} image(s) in '{args.directory}':")
    
    # Process each image
    for image_path in images:
        rel_path = os.path.relpath(image_path, args.directory)
        file_size = os.path.getsize(image_path) / 1024 / 1024  # MB
        
        print(f"\n📁 {rel_path} ({file_size:.1f}MB)")
        
        # Skip if already small
        if file_size < 0.5:  # Less than 500KB
            print("  ✅ Already optimized (< 500KB)")
            continue
        
        if args.dry_run:
            print("  🔍 Would compress this image")
            continue
        
        # Create backup if requested
        if args.backup:
            backup_path = f"{image_path}.backup"
            if not os.path.exists(backup_path):
                import shutil
                shutil.copy2(image_path, backup_path)
                print(f"  💾 Backup created: {backup_path}")
        
        # Compress image
        success = compress_image(
            image_path,
            quality=args.quality,
            max_width=args.max_width,
            max_height=args.max_height
        )
        
        if success:
            print("  ✅ Compressed successfully!")
        else:
            print("  ❌ Compression failed!")


if __name__ == "__main__":
    print("Astro Image Compressor")
    print("=" * 30)
    main()
    print("\nDone!")