"""
PDMX Datastore Tool - Converts PDMX dataset to Vertex AI Search datastore

This tool processes the PDMX (Public Domain MusicXML) dataset from Zenodo
and creates a searchable datastore using Vertex AI Search.
"""

import os
import json
import csv
import zipfile
import tarfile
from typing import Dict, Any, Optional, List
from pathlib import Path
import subprocess

try:
    from google.cloud import storage
    STORAGE_AVAILABLE = True
except ImportError:
    STORAGE_AVAILABLE = False


def download_pdmx_dataset(
    output_dir: str = "./pdmx_data",
    download_csv_only: bool = False
) -> Dict[str, Any]:
    """
    Download PDMX dataset from Zenodo.
    
    Args:
        output_dir: Directory to save downloaded files
        download_csv_only: If True, only download CSV metadata file
        
    Returns:
        Dictionary with status and paths to downloaded files
    """
    try:
        os.makedirs(output_dir, exist_ok=True)
        
        # Zenodo record URL
        record_id = "15571083"
        base_url = f"https://zenodo.org/record/{record_id}/files"
        
        files_to_download = [
            "PDMX.csv",
            "data.tar.gz",
            "metadata.tar.gz",
            "mxl.tar.gz",
            "subset_paths.tar.gz"
        ]
        
        if not download_csv_only:
            files_to_download.extend([
                "pdf.tar.gz",
                "mid.tar.gz"
            ])
        
        downloaded_files = []
        
        for filename in files_to_download:
            file_url = f"{base_url}/{filename}?download=1"
            output_path = os.path.join(output_dir, filename)
            
            # Skip download if file already exists
            if os.path.exists(output_path):
                print(f"✓ {filename} already exists, skipping download")
                downloaded_files.append(output_path)
                continue
            
            print(f"Downloading {filename}...")
            # Use wget or curl to download
            try:
                result = subprocess.run(
                    ["wget", "-O", output_path, file_url],
                    capture_output=True,
                    text=True,
                    timeout=3600  # 1 hour timeout
                )
                if result.returncode == 0:
                    downloaded_files.append(output_path)
                    print(f"✓ Downloaded {filename}")
                else:
                    # Try curl as fallback
                    result = subprocess.run(
                        ["curl", "-L", "-o", output_path, file_url],
                        capture_output=True,
                        text=True,
                        timeout=3600
                    )
                    if result.returncode == 0:
                        downloaded_files.append(output_path)
                        print(f"✓ Downloaded {filename}")
                    else:
                        return {
                            "status": "error",
                            "error_message": f"Failed to download {filename}: {result.stderr}"
                        }
            except subprocess.TimeoutExpired:
                return {
                    "status": "error",
                    "error_message": f"Download timeout for {filename}"
                }
            except FileNotFoundError:
                return {
                    "status": "error",
                    "error_message": "wget or curl not found. Please install one of them."
                }
        
        return {
            "status": "success",
            "output_dir": output_dir,
            "downloaded_files": downloaded_files,
            "message": f"Downloaded {len(downloaded_files)} files to {output_dir}"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Error downloading PDMX dataset: {str(e)}"
        }


def extract_pdmx_archives(data_dir: str) -> Dict[str, Any]:
    """
    Extract all tar.gz archives from PDMX dataset.
    
    Args:
        data_dir: Directory containing downloaded PDMX files
        
    Returns:
        Dictionary with status and extracted paths
    """
    try:
        archives = [
            "data.tar.gz",
            "metadata.tar.gz",
            "mxl.tar.gz",
            "subset_paths.tar.gz",
            "pdf.tar.gz",
            "mid.tar.gz"
        ]
        
        extracted_dirs = []
        
        for archive_name in archives:
            archive_path = os.path.join(data_dir, archive_name)
            if not os.path.exists(archive_path):
                continue
            
            # Remove .tar.gz extension to get directory name
            dir_name = archive_name.replace(".tar.gz", "")
            extracted_dir = os.path.join(data_dir, dir_name)
            
            # Skip extraction if directory already exists
            if os.path.exists(extracted_dir) and os.path.isdir(extracted_dir):
                print(f"✓ {archive_name} already extracted to {extracted_dir}, skipping")
                extracted_dirs.append(extracted_dir)
                continue
            
            print(f"Extracting {archive_name}...")
            with tarfile.open(archive_path, "r:gz") as tar:
                tar.extractall(path=data_dir)
            
            if os.path.exists(extracted_dir):
                extracted_dirs.append(extracted_dir)
                print(f"✓ Extracted to {extracted_dir}")
        
        return {
            "status": "success",
            "extracted_dirs": extracted_dirs,
            "message": f"Extracted {len(extracted_dirs)} archives"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Error extracting archives: {str(e)}"
        }


def process_musicxml_for_search(
    mxl_path: str,
    metadata_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Process a MusicXML file into a searchable document format.
    
    Args:
        mxl_path: Path to MusicXML (.mxl) file
        metadata_path: Optional path to metadata JSON file
        
    Returns:
        Dictionary with processed document data
    """
    try:
        from tools.musicxml_parser import parse_musicxml_to_json
        
        # Extract XML from MXL if needed
        if mxl_path.endswith(".mxl"):
            import zipfile
            with zipfile.ZipFile(mxl_path, 'r') as zip_ref:
                xml_files = [f for f in zip_ref.namelist() if f.endswith('.xml')]
                if xml_files:
                    xml_content = zip_ref.read(xml_files[0]).decode('utf-8')
                    # Save temporarily
                    temp_xml = mxl_path.replace(".mxl", "_temp.xml")
                    with open(temp_xml, 'w') as f:
                        f.write(xml_content)
                    xml_path = temp_xml
                else:
                    return {
                        "status": "error",
                        "error_message": "No XML file found in MXL archive"
                    }
        else:
            xml_path = mxl_path
        
        # Parse MusicXML
        parsed_data = parse_musicxml_to_json(xml_path)
        
        if parsed_data.get("status") != "success":
            return parsed_data
        
        # Load metadata if available
        metadata = {}
        if metadata_path and os.path.exists(metadata_path):
            try:
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
            except:
                pass
        
        # Create searchable document
        document = {
            "id": os.path.basename(mxl_path).replace(".mxl", "").replace(".xml", ""),
            "title": parsed_data.get("piece_name", ""),
            "composer": parsed_data.get("composer", ""),
            "key": parsed_data.get("key", ""),
            "tempo": parsed_data.get("tempo", ""),
            "measure_count": len(parsed_data.get("measures", [])),
            "content": json.dumps(parsed_data),  # Full JSON as searchable content
            "metadata": metadata,
            "file_path": mxl_path
        }
        
        # Clean up temp file
        if mxl_path.endswith(".mxl") and os.path.exists(xml_path):
            os.remove(xml_path)
        
        return {
            "status": "success",
            "document": document
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Error processing MusicXML: {str(e)}"
        }


def create_vertex_search_datastore(
    project_id: str,
    location: str,
    data_store_id: str,
    gcs_bucket: str,
    pdmx_csv_path: str,
    pdmx_data_dir: str,
    sample_size: Optional[int] = None
) -> Dict[str, Any]:
    """
    Process PDMX dataset and upload to GCS for Vertex AI Search.
    
    Note: After uploading, you need to create the datastore manually via:
    1. Google Cloud Console: https://console.cloud.google.com/ai/applications
    2. Or use gcloud CLI (see PDMX_DATASTORE_SETUP.md)
    
    Args:
        project_id: Google Cloud project ID
        location: GCP location (e.g., "us-central1")
        data_store_id: ID for the new datastore (for reference)
        gcs_bucket: GCS bucket name for storing documents
        pdmx_csv_path: Path to PDMX.csv file
        pdmx_data_dir: Directory containing extracted PDMX data
        sample_size: Optional limit on number of documents to process
        
    Returns:
        Dictionary with status and upload information
    """
    if not STORAGE_AVAILABLE:
        return {
            "status": "error",
            "error_message": "Google Cloud Storage libraries not installed. Install with: pip install google-cloud-storage"
        }
    
    try:
        # Initialize storage client
        storage_client = storage.Client(project=project_id)
        
        # Read PDMX CSV
        print(f"Reading PDMX CSV: {pdmx_csv_path}")
        documents = []
        processed_count = 0
        skipped_count = 0
        
        with open(pdmx_csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for idx, row in enumerate(reader):
                # Continue processing until we have enough successful documents
                if sample_size and len(documents) >= sample_size:
                    break
                
                # Get paths - try both '_mxl' and 'mxl' column names
                mxl_path = row.get('_mxl') or row.get('mxl', '')
                metadata_path = row.get('metadata', '')
                
                if mxl_path == 'N/A' or not mxl_path:
                    skipped_count += 1
                    continue
                
                # Resolve paths relative to pdmx_data_dir
                full_mxl_path = os.path.join(pdmx_data_dir, mxl_path.lstrip('./'))
                if metadata_path:
                    full_metadata_path = os.path.join(pdmx_data_dir, metadata_path.lstrip('./'))
                else:
                    full_metadata_path = None
                
                if not os.path.exists(full_mxl_path):
                    skipped_count += 1
                    continue
                
                # Process MusicXML
                result = process_musicxml_for_search(full_mxl_path, full_metadata_path)
                if result.get("status") == "success":
                    documents.append(result["document"])
                    processed_count += 1
                else:
                    skipped_count += 1
                
                # Show progress every 100 rows processed
                if (idx + 1) % 100 == 0:
                    print(f"Rows processed: {idx + 1}, Successful documents: {len(documents)}, Skipped: {skipped_count}")
        
        print(f"\nFinal: {len(documents)} documents successfully processed from {idx + 1} rows")
        if skipped_count > 0:
            print(f"Skipped {skipped_count} rows (missing files or processing errors)")
        
        # Upload documents to GCS as JSON
        bucket = storage_client.bucket(gcs_bucket)
        if not bucket.exists():
            bucket.create(location=location)
        
        gcs_paths = []
        
        print(f"Uploading documents to GCS bucket: {gcs_bucket}")
        for doc in documents:
            blob_name = f"pdmx_documents/{doc['id']}.json"
            blob = bucket.blob(blob_name)
            blob.upload_from_string(
                json.dumps(doc, indent=2),
                content_type='application/json'
            )
            gcs_paths.append(f"gs://{gcs_bucket}/{blob_name}")
        
        print(f"Uploaded {len(gcs_paths)} documents to GCS")
        
        return {
            "status": "success",
            "data_store_id": data_store_id,
            "documents_processed": len(documents),
            "gcs_bucket": gcs_bucket,
            "gcs_path": f"gs://{gcs_bucket}/pdmx_documents/",
            "gcs_paths_count": len(gcs_paths),
            "next_steps": [
                "1. Go to https://console.cloud.google.com/ai/applications",
                "2. Click 'Data Stores' > 'Create data store'",
                f"3. Select 'Cloud Storage' and choose bucket: {gcs_bucket}",
                "4. Set data type to 'Unstructured'",
                f"5. Use data store ID: {data_store_id}",
                "6. Wait for ingestion to complete"
            ],
            "message": f"Uploaded {len(documents)} documents to GCS. Next: Create datastore in console."
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Error processing and uploading: {str(e)}"
        }


def setup_pdmx_datastore(
    project_id: str,
    location: str = "us-central1",
    data_store_id: str = "pdmx-musicxml",
    gcs_bucket: str = None,
    download_dir: str = "./pdmx_data",
    sample_size: Optional[int] = 100
) -> Dict[str, Any]:
    """
    Complete setup: Download PDMX, process, and create Vertex AI Search datastore.
    
    Args:
        project_id: Google Cloud project ID
        location: GCP location
        data_store_id: ID for the datastore
        gcs_bucket: GCS bucket name (will create if not provided)
        download_dir: Directory for downloaded files
        sample_size: Number of documents to process (None for all)
        
    Returns:
        Dictionary with setup status and information
    """
    try:
        # Step 1: Download dataset (CSV only for metadata)
        print("Step 1: Downloading PDMX dataset...")
        download_result = download_pdmx_dataset(download_dir, download_csv_only=True)
        if download_result.get("status") != "success":
            return download_result
        
        # Step 2: Extract archives
        print("\nStep 2: Extracting archives...")
        extract_result = extract_pdmx_archives(download_dir)
        if extract_result.get("status") != "success":
            return extract_result
        
        # Step 3: Create GCS bucket if needed
        if not STORAGE_AVAILABLE:
            return {
                "status": "error",
                "error_message": "Google Cloud libraries required. Install: pip install google-cloud-storage google-cloud-discoveryengine"
            }
        
        storage_client = storage.Client(project=project_id)
        
        if not gcs_bucket:
            gcs_bucket = f"{project_id}-pdmx-datastore"
        
        bucket = storage_client.bucket(gcs_bucket)
        if not bucket.exists():
            print(f"\nStep 3: Creating GCS bucket: {gcs_bucket}")
            bucket.create(location=location)
        else:
            print(f"\nStep 3: Using existing GCS bucket: {gcs_bucket}")
        
        # Step 4: Process and create datastore
        print("\nStep 4: Processing documents and creating datastore...")
        csv_path = os.path.join(download_dir, "PDMX.csv")
        
        result = create_vertex_search_datastore(
            project_id=project_id,
            location=location,
            data_store_id=data_store_id,
            gcs_bucket=gcs_bucket,
            pdmx_csv_path=csv_path,
            pdmx_data_dir=download_dir,
            sample_size=sample_size
        )
        
        return result
        
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Error in setup: {str(e)}"
        }

