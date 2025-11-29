#!/usr/bin/env python3
"""
Helper script to create few-shot examples from existing music sheet extractions.
Takes an image/PDF and its corresponding JSON extraction and creates a few-shot example pair.
"""

import os
import json
import sys
import argparse
import shutil


def create_few_shot_example(image_path: str, json_path: str, description: str = None, 
                           output_dir: str = "few_shot_examples"):
    """
    Create a few-shot example pair from image and JSON files.
    
    Args:
        image_path: Path to music sheet image/PDF
        json_path: Path to JSON extraction file
        description: Optional description (will be extracted from JSON if not provided)
        output_dir: Directory to save the example pair
    """
    # Validate inputs
    if not os.path.exists(image_path):
        print(f"❌ Image file not found: {image_path}")
        return False
    
    if not os.path.exists(json_path):
        print(f"❌ JSON file not found: {json_path}")
        return False
    
    # Read JSON to get description if not provided
    try:
        with open(json_path, 'r') as f:
            json_data = json.load(f)
        
        # Handle different JSON formats
        if 'data' in json_data:
            # Library format
            actual_data = json_data['data']
        else:
            actual_data = json_data
        
        # Get description
        if not description:
            description = actual_data.get('description') or \
                        actual_data.get('piece_name') or \
                        os.path.splitext(os.path.basename(image_path))[0]
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Create base name
        base_name = os.path.splitext(os.path.basename(image_path))[0]
        # Sanitize base name
        base_name = "".join(c for c in base_name if c.isalnum() or c in (' ', '-', '_')).strip()
        base_name = base_name.replace(' ', '_')
        
        # Copy image file
        image_ext = os.path.splitext(image_path)[1]
        dest_image = os.path.join(output_dir, f"{base_name}{image_ext}")
        shutil.copy2(image_path, dest_image)
        print(f"✅ Copied image: {dest_image}")
        
        # Create JSON file with description
        dest_json = os.path.join(output_dir, f"{base_name}.json")
        output_json = {
            "description": description,
            **actual_data
        }
        
        with open(dest_json, 'w') as f:
            json.dump(output_json, f, indent=2)
        print(f"✅ Created JSON: {dest_json}")
        
        print(f"\n✅ Few-shot example created:")
        print(f"   Description: {description}")
        print(f"   Image: {os.path.basename(dest_image)}")
        print(f"   JSON: {os.path.basename(dest_json)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating example: {e}")
        import traceback
        traceback.print_exc()
        return False


def create_from_library(image_path: str, library_dir: str = "library", 
                       output_dir: str = "few_shot_examples"):
    """
    Create few-shot example from library entry.
    Finds the JSON in library based on image file hash.
    """
    import hashlib
    
    # Calculate hash of image
    sha256_hash = hashlib.sha256()
    try:
        with open(image_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        file_hash = sha256_hash.hexdigest()
    except Exception as e:
        print(f"❌ Error reading image file: {e}")
        return False
    
    # Find matching JSON in library
    json_path = os.path.join(library_dir, f"{file_hash}.json")
    
    if not os.path.exists(json_path):
        print(f"❌ No matching library entry found for {os.path.basename(image_path)}")
        print(f"   Expected: {json_path}")
        return False
    
    print(f"📚 Found library entry: {os.path.basename(json_path)}")
    
    # Extract description from library entry
    with open(json_path, 'r') as f:
        lib_data = json.load(f)
    
    description = lib_data.get('original_filename', os.path.basename(image_path))
    
    # Create example using the data from library
    return create_few_shot_example(image_path, json_path, description, output_dir)


def main():
    parser = argparse.ArgumentParser(
        description="Create few-shot examples from music sheet images and JSON extractions"
    )
    parser.add_argument("image", help="Path to music sheet image/PDF")
    parser.add_argument("json", nargs="?", help="Path to JSON extraction file (optional if using --from-library)")
    parser.add_argument("--description", help="Description for the example")
    parser.add_argument("--output-dir", default="few_shot_examples", 
                       help="Output directory for examples (default: few_shot_examples)")
    parser.add_argument("--from-library", action="store_true",
                       help="Find JSON in library directory based on image hash")
    parser.add_argument("--library-dir", default="library",
                       help="Library directory (default: library)")
    
    args = parser.parse_args()
    
    if args.from_library:
        success = create_from_library(args.image, args.library_dir, args.output_dir)
    elif args.json:
        success = create_few_shot_example(args.image, args.json, args.description, args.output_dir)
    else:
        print("❌ Error: Either provide --json or use --from-library")
        parser.print_help()
        sys.exit(1)
    
    if success:
        print(f"\n💡 Tip: Test with:")
        print(f"   python3 test_extraction_performance.py <file> --few-shot-dir {args.output_dir}")
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()

