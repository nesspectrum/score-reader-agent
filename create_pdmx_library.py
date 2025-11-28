#!/usr/bin/env python3
"""
Script to create a searchable library from PDMX data folder.

This script:
1. Reads PDMX.csv to get metadata
2. Loads metadata JSON files
3. Optionally parses MusicXML files for measure data
4. Converts to library format and saves using LibraryManager
"""

import os
import csv
import json
import argparse
from typing import Dict, Any, Optional, List
from tools.library_manager import LibraryManager
from tools.musicxml_parser import parse_musicxml_to_json


def parse_keysig(keysig_str: str) -> str:
    """
    Parse keysig string (e.g., "G major, E minor") to extract primary key.
    
    Args:
        keysig_str: Keysig string from metadata
        
    Returns:
        Primary key signature (e.g., "G Major")
    """
    if not keysig_str:
        return ""
    
    # Take first part before comma
    primary = keysig_str.split(',')[0].strip()
    
    # Normalize capitalization
    parts = primary.split()
    if len(parts) >= 2:
        key = parts[0].capitalize()
        mode = parts[1].capitalize()
        return f"{key} {mode}"
    
    return primary


def extract_tempo_from_metadata(metadata: Dict[str, Any]) -> Optional[str]:
    """
    Extract tempo from metadata JSON.
    
    Args:
        metadata: Metadata dictionary
        
    Returns:
        Tempo string or None
    """
    # Check various possible locations
    score_data = metadata.get("data", {}).get("score", {})
    
    # Check body/description for tempo info
    body = score_data.get("body", "")
    if body:
        # Look for tempo patterns like "Tempo: 120" or "BPM: 120"
        import re
        tempo_match = re.search(r'(?:tempo|bpm)[:\s]+(\d+)', body.lower())
        if tempo_match:
            return tempo_match.group(1)
    
    # Check if there's a tempo field directly
    if "tempo" in score_data:
        return str(score_data["tempo"])
    
    return None


def convert_pdmx_to_library_format(
    csv_row: Dict[str, str],
    metadata: Optional[Dict[str, Any]] = None,
    mxl_path: Optional[str] = None,
    pdmx_dir: str = "./pdmx_data"
) -> Dict[str, Any]:
    """
    Convert PDMX CSV row and metadata to library format.
    
    Args:
        csv_row: Row from PDMX.csv
        metadata: Optional metadata JSON data
        mxl_path: Optional path to MusicXML file
        pdmx_dir: Base directory for PDMX data
        
    Returns:
        Dictionary in library format with 'data' key
    """
    # Start with basic info from CSV
    piece_name = csv_row.get("title", "") or csv_row.get("song_name", "")
    composer = csv_row.get("composer_name", "")
    artist = csv_row.get("artist_name", "")
    
    # Extract from metadata if available
    measures = []
    key = ""
    tempo = None
    
    if metadata:
        score_data = metadata.get("data", {}).get("score", {})
        
        # Get piece name (prefer metadata title)
        if not piece_name:
            piece_name = score_data.get("title", "") or score_data.get("file_score_title", "")
        
        # Get composer
        if not composer:
            composer = score_data.get("composer_name", "")
            if not composer and score_data.get("composer"):
                composer = score_data["composer"].get("name", "")
        
        # Get key signature
        keysig = score_data.get("keysig", "")
        if keysig:
            key = parse_keysig(keysig)
        
        # Get tempo
        tempo = extract_tempo_from_metadata(metadata)
        
        # Get measure count
        measure_count = score_data.get("measures", 0)
    
    # Try to parse MusicXML for detailed measure data
    if mxl_path and os.path.exists(mxl_path):
        try:
            parsed_xml = parse_musicxml_to_json(mxl_path)
            if parsed_xml.get("status") == "success":
                # Use parsed data for more accurate fields
                if parsed_xml.get("piece_name"):
                    piece_name = parsed_xml["piece_name"]
                if parsed_xml.get("composer"):
                    composer = parsed_xml["composer"]
                if parsed_xml.get("key"):
                    key = parsed_xml["key"]
                if parsed_xml.get("tempo"):
                    tempo = parsed_xml["tempo"]
                if parsed_xml.get("measures"):
                    measures = parsed_xml["measures"]
        except Exception as e:
            print(f"Warning: Could not parse MusicXML {mxl_path}: {e}")
    
    # Build library data format
    library_data = {
        "piece_name": piece_name,
        "composer": composer,
        "artist": artist,
        "key": key,
        "tempo": tempo,
        "measures": measures,
        "genres": csv_row.get("genres", "").split(",") if csv_row.get("genres") else [],
        "rating": float(csv_row.get("rating", 0)) if csv_row.get("rating") else 0.0,
        "complexity": int(csv_row.get("complexity", 0)) if csv_row.get("complexity") else 0,
        "source": "PDMX",
        "mxl_path": csv_row.get("mxl", ""),
        "pdf_path": csv_row.get("pdf", ""),
        "metadata_path": csv_row.get("metadata", "")
    }
    
    return library_data


def import_pdmx_to_library(
    pdmx_dir: str = "./pdmx_data",
    library_dir: str = "library",
    sample_size: Optional[int] = None,
    parse_musicxml: bool = False,
    skip_existing: bool = True
) -> Dict[str, Any]:
    """
    Import PDMX data into searchable library.
    
    Args:
        pdmx_dir: Directory containing PDMX data
        library_dir: Directory for library storage
        sample_size: Number of entries to process (None = all)
        parse_musicxml: Whether to parse MusicXML files for measure data
        skip_existing: Skip entries that already exist in library
        
    Returns:
        Dictionary with import statistics
    """
    csv_path = os.path.join(pdmx_dir, "PDMX.csv")
    
    if not os.path.exists(csv_path):
        return {
            "status": "error",
            "error_message": f"PDMX.csv not found at {csv_path}"
        }
    
    library_manager = LibraryManager(library_dir=library_dir)
    
    imported_count = 0
    skipped_count = 0
    error_count = 0
    errors = []
    
    print(f"Reading PDMX CSV from {csv_path}...")
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            total_rows = len(rows)
            if sample_size:
                rows = rows[:sample_size]
                print(f"Processing {len(rows)} entries (sample size: {sample_size})")
            else:
                print(f"Processing {total_rows} entries...")
            
            for idx, row in enumerate(rows, 1):
                if idx % 100 == 0:
                    print(f"Progress: {idx}/{len(rows)} (imported: {imported_count}, skipped: {skipped_count}, errors: {error_count})")
                
                try:
                    # Resolve file paths
                    mxl_path = None
                    if row.get("mxl"):
                        mxl_path = os.path.join(pdmx_dir, row["mxl"].lstrip("./"))
                    
                    pdf_path = None
                    if row.get("pdf"):
                        pdf_path = os.path.join(pdmx_dir, row["pdf"].lstrip("./"))
                    
                    # Use PDF or MXL for hash calculation (prefer PDF if available)
                    file_path = pdf_path if pdf_path and os.path.exists(pdf_path) else mxl_path
                    
                    if not file_path or not os.path.exists(file_path):
                        error_count += 1
                        errors.append(f"Row {idx}: File not found: {file_path}")
                        continue
                    
                    # Check if already in library
                    if skip_existing:
                        cached_data = library_manager.get_cached_data(file_path)
                        if cached_data:
                            skipped_count += 1
                            continue
                    
                    # Load metadata JSON
                    metadata = None
                    if row.get("metadata"):
                        metadata_path = os.path.join(pdmx_dir, row["metadata"].lstrip("./"))
                        if os.path.exists(metadata_path):
                            try:
                                with open(metadata_path, 'r', encoding='utf-8') as mf:
                                    metadata = json.load(mf)
                            except Exception as e:
                                print(f"Warning: Could not load metadata {metadata_path}: {e}")
                    
                    # Convert to library format
                    library_data = convert_pdmx_to_library_format(
                        csv_row=row,
                        metadata=metadata,
                        mxl_path=mxl_path if parse_musicxml else None,
                        pdmx_dir=pdmx_dir
                    )
                    
                    # Save to library
                    success = library_manager.save_to_library(
                        file_path=file_path,
                        data=library_data,
                        user_id="pdmx_import"
                    )
                    
                    if success:
                        imported_count += 1
                    else:
                        error_count += 1
                        errors.append(f"Row {idx}: Failed to save to library")
                        
                except Exception as e:
                    error_count += 1
                    error_msg = f"Row {idx}: {str(e)}"
                    errors.append(error_msg)
                    print(f"Error processing row {idx}: {e}")
            
            print(f"\nImport complete!")
            print(f"  Imported: {imported_count}")
            print(f"  Skipped: {skipped_count}")
            print(f"  Errors: {error_count}")
            
            return {
                "status": "success",
                "imported": imported_count,
                "skipped": skipped_count,
                "errors": error_count,
                "error_list": errors[:10]  # First 10 errors
            }
            
    except Exception as e:
        return {
            "status": "error",
            "error_message": str(e),
            "imported": imported_count,
            "skipped": skipped_count,
            "errors": error_count
        }


def main():
    parser = argparse.ArgumentParser(
        description="Import PDMX data into searchable library"
    )
    parser.add_argument(
        "--pdmx-dir",
        default="./pdmx_data",
        help="Directory containing PDMX data (default: ./pdmx_data)"
    )
    parser.add_argument(
        "--library-dir",
        default="library",
        help="Library directory (default: library)"
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=None,
        help="Number of entries to process (default: all)"
    )
    parser.add_argument(
        "--parse-musicxml",
        action="store_true",
        help="Parse MusicXML files for detailed measure data (slower)"
    )
    parser.add_argument(
        "--no-skip-existing",
        action="store_true",
        help="Re-import entries that already exist in library"
    )
    
    args = parser.parse_args()
    
    result = import_pdmx_to_library(
        pdmx_dir=args.pdmx_dir,
        library_dir=args.library_dir,
        sample_size=args.sample_size,
        parse_musicxml=args.parse_musicxml,
        skip_existing=not args.no_skip_existing
    )
    
    if result["status"] == "success":
        print(f"\n✅ Successfully imported {result['imported']} entries")
        if result["errors"] > 0:
            print(f"⚠️  {result['errors']} errors occurred")
            if result.get("error_list"):
                print("\nFirst few errors:")
                for err in result["error_list"]:
                    print(f"  - {err}")
    else:
        print(f"\n❌ Error: {result.get('error_message', 'Unknown error')}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())

