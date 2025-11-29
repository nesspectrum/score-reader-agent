#!/usr/bin/env python3
"""
Upload 100 PDMX samples to Google Cloud Storage.

This script processes 100 samples from the PDMX dataset and uploads them to GCS
for use with Vertex AI Search.
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

from tools.pdmx_datastore import setup_pdmx_datastore

def main():
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
    
    if not project_id:
        print("Error: GOOGLE_CLOUD_PROJECT not set in environment")
        print("Please set it in your .env file or export it:")
        print("  export GOOGLE_CLOUD_PROJECT=kaggle-capstone-112025")
        return 1
    
    print("=" * 60)
    print("Uploading 100 PDMX Samples to Google Cloud Storage")
    print("=" * 60)
    print(f"Project ID: {project_id}")
    print(f"Location: {location}")
    print(f"Sample Size: 100")
    print("=" * 60)
    print()
    
    # Run the setup with 100 samples
    result = setup_pdmx_datastore(
        project_id=project_id,
        location=location,
        data_store_id="pdmx-musicxml",
        download_dir="./pdmx_data",  # Uses the symlinked directory
        sample_size=100  # Upload 100 samples
    )
    
    if result.get("status") == "success":
        print("\n" + "=" * 60)
        print("✓ Upload Complete!")
        print("=" * 60)
        print(f"Documents Processed: {result.get('documents_processed')}")
        print(f"GCS Bucket: {result.get('gcs_bucket')}")
        print(f"GCS Path: {result.get('gcs_path')}")
        print("\nNext Steps:")
        for step in result.get('next_steps', []):
            print(f"  {step}")
        return 0
    else:
        print("\n" + "=" * 60)
        print("✗ Upload Failed")
        print("=" * 60)
        print(f"Error: {result.get('error_message')}")
        return 1

if __name__ == "__main__":
    sys.exit(main())

