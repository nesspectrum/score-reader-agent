#!/usr/bin/env python3
"""
Create Vertex AI Search Datastore from GCS Bucket

This script creates a Vertex AI Search (Discovery Engine) datastore from files
already uploaded to a Google Cloud Storage bucket.
"""

import os
import argparse
import time
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

try:
    from google.cloud import discoveryengine_v1beta as discoveryengine
    DISCOVERY_ENGINE_AVAILABLE = True
except ImportError:
    DISCOVERY_ENGINE_AVAILABLE = False
    print("Warning: google-cloud-discoveryengine not installed. Install with:")
    print("  pip install google-cloud-discoveryengine")

try:
    from googleapiclient import discovery as service_discovery
    from google.oauth2 import service_account
    import google.auth
    SERVICE_USAGE_AVAILABLE = True
except ImportError:
    SERVICE_USAGE_AVAILABLE = False


def enable_discovery_engine_api(project_id: str) -> Dict[str, Any]:
    """
    Enable the Discovery Engine API for a project.
    
    Args:
        project_id: GCP project ID
    
    Returns:
        Dictionary with status
    """
    if not SERVICE_USAGE_AVAILABLE:
        return {
            "status": "error",
            "error_message": "google-api-python-client not installed. Install with: pip install google-api-python-client"
        }
    
    try:
        credentials, _ = google.auth.default()
        service = service_discovery.build('serviceusage', 'v1', credentials=credentials)
        
        service_name = f'projects/{project_id}/services/discoveryengine.googleapis.com'
        
        request = service.services().enable(name=service_name)
        request.execute()
        
        print(f"✓ Discovery Engine API enabled for project {project_id}")
        print("  Waiting 30 seconds for API to propagate...")
        time.sleep(30)
        
        return {
            "status": "success",
            "message": "Discovery Engine API enabled"
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Error enabling API: {str(e)}"
        }


def create_datastore_from_gcs(
    project_id: str,
    datastore_display_name: str,
    gcs_uri: str,
    location: str = "us-central1",
    datastore_id: Optional[str] = None,
    solution_types: Optional[list] = None,
    auto_enable_api: bool = True
) -> Dict[str, Any]:
    """
    Create a new datastore from GCS bucket
    
    Args:
        project_id: Your GCP project ID
        datastore_display_name: Display name for your datastore
        gcs_uri: GCS URI (e.g., gs://bucket/metadata.jsonl or gs://bucket/pdf/)
        location: Location of the datastore (default: us-central1)
        datastore_id: Optional datastore ID (will be generated from display_name if not provided)
        solution_types: List of solution types (default: ["SOLUTION_TYPE_SEARCH"])
    
    Returns:
        Dictionary with status and datastore information
    """
    if not DISCOVERY_ENGINE_AVAILABLE:
        return {
            "status": "error",
            "error_message": "google-cloud-discoveryengine library not installed. Install with: pip install google-cloud-discoveryengine"
        }
    
    try:
        client = discoveryengine.DataStoreServiceClient()
        
        # Generate datastore_id from display_name if not provided
        if not datastore_id:
            datastore_id = datastore_display_name.lower().replace(' ', '-').replace('_', '-')
            # Remove special characters
            datastore_id = ''.join(c for c in datastore_id if c.isalnum() or c == '-')
        
        # Construct the parent
        parent = f"projects/{project_id}/locations/{location}/collections/default_collection"
        
        # Set default solution types
        if solution_types is None:
            solution_types = [discoveryengine.SolutionType.SOLUTION_TYPE_SEARCH]
        
        # Create datastore configuration
        datastore = discoveryengine.DataStore(
            display_name=datastore_display_name,
            industry_vertical=discoveryengine.IndustryVertical.GENERIC,
            content_config=discoveryengine.DataStore.ContentConfig.CONTENT_REQUIRED,
            solution_types=solution_types,
        )
        
        request = discoveryengine.CreateDataStoreRequest(
            parent=parent,
            data_store=datastore,
            data_store_id=datastore_id,
            create_advanced_site_search=False
        )
        
        print(f"Creating datastore '{datastore_display_name}' (ID: {datastore_id})...")
        print(f"GCS URI: {gcs_uri}")
        print(f"Location: {location}")
        
        # Try to create the datastore, handle API not enabled error
        try:
            operation = client.create_data_store(request=request)
        except Exception as api_error:
            # Check if it's an API not enabled error
            error_str = str(api_error)
            if "SERVICE_DISABLED" in error_str or "discoveryengine.googleapis.com" in error_str:
                if auto_enable_api and SERVICE_USAGE_AVAILABLE:
                    print("\nDiscovery Engine API not enabled. Attempting to enable...")
                    enable_result = enable_discovery_engine_api(project_id)
                    if enable_result.get("status") == "success":
                        # Retry after enabling
                        print("Retrying datastore creation...")
                        operation = client.create_data_store(request=request)
                    else:
                        return {
                            "status": "error",
                            "error_message": f"API not enabled. Please enable manually:\n"
                                           f"  gcloud services enable discoveryengine.googleapis.com --project={project_id}\n"
                                           f"  Or visit: https://console.developers.google.com/apis/api/discoveryengine.googleapis.com/overview?project={project_id}"
                        }
                else:
                    return {
                        "status": "error",
                        "error_message": f"Discovery Engine API not enabled for project '{project_id}'. Enable it with:\n"
                                       f"  gcloud services enable discoveryengine.googleapis.com --project={project_id}\n"
                                       f"  Or visit: https://console.developers.google.com/apis/api/discoveryengine.googleapis.com/overview?project={project_id}\n\n"
                                       f"Note: If you see a different project ID in the error, check your authentication:\n"
                                       f"  gcloud auth application-default login\n"
                                       f"  gcloud config set project {project_id}"
                    }
            else:
                raise  # Re-raise if it's a different error
        
        print("Waiting for datastore creation to complete...")
        response = operation.result(timeout=300)  # 5 minute timeout
        
        datastore_name = response.name
        
        print(f"✓ Datastore created: {datastore_name}")
        
        # Import data from GCS
        import_result = import_gcs_data(
            project_id=project_id,
            datastore_name=datastore_name,
            gcs_uri=gcs_uri,
            location=location
        )
        
        return {
            "status": "success",
            "datastore_id": datastore_id,
            "datastore_name": datastore_name,
            "display_name": datastore_display_name,
            "gcs_uri": gcs_uri,
            "location": location,
            "import_status": import_result.get("status"),
            "import_operation": import_result.get("operation_name")
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Error creating datastore: {str(e)}"
        }


def import_gcs_data(
    project_id: str,
    datastore_name: str,
    gcs_uri: str,
    location: str = "global"
) -> Dict[str, Any]:
    """
    Import data from GCS into the datastore.
    
    Args:
        project_id: GCP project ID
        datastore_name: Full name of the datastore (e.g., projects/.../locations/.../dataStores/...)
        gcs_uri: GCS URI pointing to the data
        location: Location of the datastore
    
    Returns:
        Dictionary with import status
    """
    try:
        from google.cloud import discoveryengine_v1beta as discoveryengine
        
        import_client = discoveryengine.ImportServiceClient()
        
        # Determine data format from URI
        # For unstructured data (JSON/JSONL files)
        gcs_source = discoveryengine.GcsSource(
            input_uris=[gcs_uri],
            data_schema="document"  # or "custom" for custom schemas
        )
        
        import_config = discoveryengine.ImportDocumentsRequest.ImportConfig(
            gcs_source=gcs_source,
            reconciliation_mode=discoveryengine.ImportDocumentsRequest.ReconciliationMode.INCREMENTAL
        )
        
        request = discoveryengine.ImportDocumentsRequest(
            parent=datastore_name,
            import_config=import_config,
            error_config=discoveryengine.ImportErrorConfig(
                gcs_prefix=f"{gcs_uri}/errors"
            )
        )
        
        print(f"\nImporting data from {gcs_uri}...")
        operation = import_client.import_documents(request=request)
        
        print("Waiting for import to complete (this may take several minutes)...")
        response = operation.result(timeout=600)  # 10 minute timeout
        
        print(f"✓ Import completed")
        print(f"  Imported documents: {response.get('success_count', 'N/A')}")
        if response.get('failure_count', 0) > 0:
            print(f"  Failed documents: {response.get('failure_count')}")
        
        return {
            "status": "success",
            "operation_name": operation.operation.name,
            "success_count": response.get('success_count', 0),
            "failure_count": response.get('failure_count', 0)
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Error importing data: {str(e)}"
        }


def list_datastores(
    project_id: str,
    location: str = "global"
) -> Dict[str, Any]:
    """
    List all datastores in a project.
    
    Args:
        project_id: GCP project ID
        location: Location to list datastores from
    
    Returns:
        Dictionary with list of datastores
    """
    if not DISCOVERY_ENGINE_AVAILABLE:
        return {
            "status": "error",
            "error_message": "google-cloud-discoveryengine library not installed"
        }
    
    try:
        client = discoveryengine.DataStoreServiceClient()
        parent = f"projects/{project_id}/locations/{location}/collections/default_collection"
        
        request = discoveryengine.ListDataStoresRequest(parent=parent)
        response = client.list_data_stores(request=request)
        
        datastores = []
        for datastore in response:
            datastores.append({
                "name": datastore.name,
                "display_name": datastore.display_name,
                "data_store_id": datastore.name.split("/")[-1],
                "solution_types": [st.name for st in datastore.solution_types],
                "industry_vertical": datastore.industry_vertical.name
            })
        
        return {
            "status": "success",
            "datastores": datastores,
            "count": len(datastores)
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Error listing datastores: {str(e)}"
        }


def main():
    parser = argparse.ArgumentParser(
        description="Create Vertex AI Search datastore from GCS bucket"
    )
    parser.add_argument(
        "--project-id",
        default=os.getenv("GOOGLE_CLOUD_PROJECT"),
        help="Google Cloud project ID (default: from GOOGLE_CLOUD_PROJECT env var)"
    )
    parser.add_argument(
        "--display-name",
        required=True,
        help="Display name for the datastore"
    )
    parser.add_argument(
        "--gcs-uri",
        required=True,
        help="GCS URI (e.g., gs://bucket-name/path/to/data/)"
    )
    parser.add_argument(
        "--location",
        default="global",
        help="GCP location (default: global - required for Discovery Engine API)"
    )
    parser.add_argument(
        "--datastore-id",
        default=None,
        help="Datastore ID (will be generated from display-name if not provided)"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all existing datastores instead of creating one"
    )
    
    args = parser.parse_args()
    
    if args.list:
        if not args.project_id:
            print("Error: --project-id required for listing datastores")
            return 1
        
        print(f"Listing datastores in project: {args.project_id}")
        result = list_datastores(args.project_id, args.location)
        
        if result.get("status") == "success":
            print(f"\nFound {result['count']} datastore(s):\n")
            for ds in result["datastores"]:
                print(f"  ID: {ds['data_store_id']}")
                print(f"  Display Name: {ds['display_name']}")
                print(f"  Solutions: {', '.join(ds['solution_types'])}")
                print(f"  Industry: {ds['industry_vertical']}")
                print()
        else:
            print(f"Error: {result.get('error_message')}")
            return 1
        
        return 0
    
    if not args.project_id:
        print("Error: --project-id required (or set GOOGLE_CLOUD_PROJECT env var)")
        return 1
    
    print("=" * 60)
    print("Create Vertex AI Search Datastore from GCS")
    print("=" * 60)
    print(f"Project ID: {args.project_id}")
    print(f"Display Name: {args.display_name}")
    print(f"GCS URI: {args.gcs_uri}")
    print(f"Location: {args.location}")
    print("=" * 60)
    print()
    
    result = create_datastore_from_gcs(
        project_id=args.project_id,
        datastore_display_name=args.display_name,
        gcs_uri=args.gcs_uri,
        location=args.location,
        datastore_id=args.datastore_id
    )
    
    if result.get("status") == "success":
        print("\n" + "=" * 60)
        print("✓ Datastore Created Successfully!")
        print("=" * 60)
        print(f"Datastore ID: {result.get('datastore_id')}")
        print(f"Datastore Name: {result.get('datastore_name')}")
        print(f"GCS URI: {result.get('gcs_uri')}")
        print(f"\nImport Status: {result.get('import_status')}")
        if result.get('import_operation'):
            print(f"Import Operation: {result.get('import_operation')}")
        print("\nYou can now use this datastore with VertexAiSearchTool!")
        return 0
    else:
        print("\n" + "=" * 60)
        print("✗ Failed to Create Datastore")
        print("=" * 60)
        print(f"Error: {result.get('error_message')}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())

