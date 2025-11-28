import os
import time
from dotenv import load_dotenv
from google.cloud import discoveryengine_v1 as discoveryengine
from google.api_core.client_options import ClientOptions

# Load environment variables
load_dotenv()

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "global")
DATA_STORE_ID = os.getenv("DATA_STORE_ID", "pdmx-musicxml")
GCS_BUCKET = os.getenv("GCS_BUCKET_NAME")

def create_data_store():
    if not PROJECT_ID:
        print("Error: GOOGLE_CLOUD_PROJECT not found in .env")
        return

    print(f"Creating Data Store '{DATA_STORE_ID}' in project '{PROJECT_ID}' ({LOCATION})...")

    # Client options for location (if not global)
    client_options = (
        ClientOptions(api_endpoint=f"{LOCATION}-discoveryengine.googleapis.com")
        if LOCATION != "global"
        else None
    )

    # 1. Create Data Store
    ds_client = discoveryengine.DataStoreServiceClient(client_options=client_options)
    parent = f"projects/{PROJECT_ID}/locations/{LOCATION}/collections/default_collection"
    
    data_store = discoveryengine.DataStore(
        display_name="PDMX MusicXML Library",
        industry_vertical=discoveryengine.IndustryVertical.GENERIC,
        solution_types=[discoveryengine.SolutionType.SOLUTION_TYPE_SEARCH],
        content_config=discoveryengine.DataStore.ContentConfig.CONTENT_REQUIRED,
    )

    try:
        operation = ds_client.create_data_store(
            parent=parent,
            data_store_id=DATA_STORE_ID,
            data_store=data_store,
        )
        print("Waiting for Data Store creation...")
        response = operation.result()
        print(f"Data Store created: {response.name}")
    except Exception as e:
        if "already exists" in str(e):
            print(f"Data Store '{DATA_STORE_ID}' already exists.")
        else:
            print(f"Error creating Data Store: {e}")
            return

    # 2. Import Data from GCS
    if GCS_BUCKET:
        print(f"Importing data from gs://{GCS_BUCKET}...")
        import_client = discoveryengine.DocumentServiceClient(client_options=client_options)
        parent_ds = f"projects/{PROJECT_ID}/locations/{LOCATION}/collections/default_collection/dataStores/{DATA_STORE_ID}/branches/default_branch"
        
        gcs_source = discoveryengine.GcsSource(
            input_uris=[f"gs://{GCS_BUCKET}/*.json"],
            data_schema="custom" # or "content" depending on your JSON structure
        )
        
        input_config = discoveryengine.ImportDocumentsRequest.InlineSource(
            documents=[] # We are using GcsSource, but the API structure is slightly different in v1
        )
        
        # Correct way for v1 GcsSource
        request = discoveryengine.ImportDocumentsRequest(
            parent=parent_ds,
            gcs_source=gcs_source,
            reconciliation_mode=discoveryengine.ImportDocumentsRequest.ReconciliationMode.INCREMENTAL
        )

        try:
            operation = import_client.import_documents(request=request)
            print("Started import operation. This may take a while.")
            print(f"Operation: {operation.operation.name}")
            # We won't wait for it to finish in this script to avoid blocking
        except Exception as e:
            print(f"Error importing documents: {e}")
    else:
        print("Skipping import: GCS_BUCKET_NAME not set in .env")

if __name__ == "__main__":
    create_data_store()
