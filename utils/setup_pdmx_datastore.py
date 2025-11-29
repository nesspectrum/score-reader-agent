#!/usr/bin/env python3
"""
Setup script for creating Vertex AI Search datastore from PDMX dataset.

Usage:
    python setup_pdmx_datastore.py --project-id YOUR_PROJECT_ID [options]

Example:
    python setup_pdmx_datastore.py \
        --project-id my-project \
        --location us-central1 \
        --data-store-id pdmx-musicxml \
        --sample-size 1000
"""

import argparse
import os
from dotenv import load_dotenv
from tools.pdmx_datastore import setup_pdmx_datastore

load_dotenv()


def main():
    parser = argparse.ArgumentParser(
        description="Setup Vertex AI Search datastore from PDMX dataset"
    )
    parser.add_argument(
        "--project-id",
        required=True,
        help="Google Cloud project ID"
    )
    parser.add_argument(
        "--location",
        default="us-central1",
        help="GCP location (default: us-central1)"
    )
    parser.add_argument(
        "--data-store-id",
        default="pdmx-musicxml",
        help="ID for the Vertex AI Search datastore (default: pdmx-musicxml)"
    )
    parser.add_argument(
        "--gcs-bucket",
        default=None,
        help="GCS bucket name (will create if not provided)"
    )
    parser.add_argument(
        "--download-dir",
        default="./pdmx_data",
        help="Directory for downloaded files (default: ./pdmx_data)"
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=None,
        help="Number of documents to process (default: all)"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("PDMX to Vertex AI Search Datastore Setup")
    print("=" * 60)
    print(f"Project ID: {args.project_id}")
    print(f"Location: {args.location}")
    print(f"Data Store ID: {args.data_store_id}")
    print(f"Sample Size: {args.sample_size or 'All documents'}")
    print("=" * 60)
    print()
    
    result = setup_pdmx_datastore(
        project_id=args.project_id,
        location=args.location,
        data_store_id=args.data_store_id,
        gcs_bucket=args.gcs_bucket,
        download_dir=args.download_dir,
        sample_size=args.sample_size
    )
    
    if result.get("status") == "success":
        print("\n" + "=" * 60)
        print("✓ Setup Complete!")
        print("=" * 60)
        print(f"Datastore Name: {result.get('datastore_name')}")
        print(f"Datastore ID: {result.get('datastore_id')}")
        print(f"Documents Processed: {result.get('documents_processed')}")
        print(f"GCS Bucket: {result.get('gcs_bucket')}")
        print("\nYou can now use VertexAiSearchTool with this datastore!")
    else:
        print("\n" + "=" * 60)
        print("✗ Setup Failed")
        print("=" * 60)
        print(f"Error: {result.get('error_message')}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())

