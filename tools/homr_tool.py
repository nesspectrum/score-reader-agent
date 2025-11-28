"""
HOMR Tool - Converts music sheet images to MusicXML format
"""

import os
import subprocess
from typing import Dict, Any, Optional
from pathlib import Path


def convert_image_to_musicxml(image_path: str, output_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    Convert a music sheet image to MusicXML format using homr.
    
    Args:
        image_path: Path to the input image file (PNG, JPG, etc.)
        output_dir: Optional directory for output XML file (defaults to same as input)
        
    Returns:
        Dictionary with status and path to generated XML file
    """
    try:
        # Validate input file exists
        if not os.path.exists(image_path):
            return {
                "status": "error",
                "error_message": f"Image file not found: {image_path}"
            }
        
        # Determine output path
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            base_name = os.path.splitext(os.path.basename(image_path))[0]
            xml_path = os.path.join(output_dir, f"{base_name}.musicxml")
        else:
            # Use same directory as input
            xml_path = os.path.splitext(image_path)[0] + ".musicxml"
        
        # Check if homr is available
        # Try to find homr in the homr directory (same level as tools)
        project_root = os.path.dirname(os.path.dirname(__file__))
        homr_dir = os.path.join(project_root, "homr")
        homr_script = os.path.join(homr_dir, "homr", "main.py")
        
        # Check if we can use poetry run homr
        homr_command = None
        if os.path.exists(homr_dir):
            # Try poetry run homr
            try:
                result = subprocess.run(
                    ["poetry", "run", "homr", "--help"],
                    cwd=homr_dir,
                    capture_output=True,
                    timeout=5
                )
                if result.returncode == 0:
                    homr_command = ["poetry", "run", "homr"]
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
        
        # Fallback: try direct python execution
        if not homr_command and os.path.exists(homr_script):
            homr_command = ["python", homr_script]
        
        if not homr_command:
            return {
                "status": "error",
                "error_message": "homr tool not found. Please ensure homr is installed and available."
            }
        
        # Run homr conversion
        print(f"Converting {image_path} to MusicXML using homr...")
        
        # Change to homr directory if using poetry
        cwd = homr_dir if homr_command[0] == "poetry" else None
        
        result = subprocess.run(
            homr_command + [image_path],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode != 0:
            return {
                "status": "error",
                "error_message": f"homr conversion failed: {result.stderr}",
                "stdout": result.stdout
            }
        
        # Check if XML file was created
        # homr creates XML in the same directory as the input image
        expected_xml = os.path.splitext(image_path)[0] + ".musicxml"
        
        if not os.path.exists(expected_xml):
            return {
                "status": "error",
                "error_message": f"XML file not created at expected location: {expected_xml}",
                "stdout": result.stdout
            }
        
        # Copy to output_dir if specified and different
        if output_dir and expected_xml != xml_path:
            import shutil
            shutil.copy2(expected_xml, xml_path)
        
        return {
            "status": "success",
            "xml_path": expected_xml if not output_dir else xml_path,
            "image_path": image_path,
            "message": f"Successfully converted image to MusicXML"
        }
        
    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "error_message": "homr conversion timed out after 5 minutes"
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Error during homr conversion: {str(e)}"
        }

