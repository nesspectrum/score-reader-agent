import os
import sys
from dotenv import load_dotenv
from google.cloud import discoveryengine_v1 as discoveryengine
from google.api_core.client_options import ClientOptions

# Load environment variables
load_dotenv()

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "global")
DATA_STORE_ID = os.getenv("DATA_STORE_ID", "pdmx-musicxml")
# Default to 'pdmx' if not set, based on discovery
GCS_BUCKET = os.getenv("GCS_BUCKET_NAME", "pdmx") 

def import_documents():
    if not PROJECT_ID:
        print("Error: GOOGLE_CLOUD_PROJECT not found in .env")
        return

    print(f"Importing data into '{DATA_STORE_ID}' from 'gs://{GCS_BUCKET}/*.json'...")

    client_options = (
        ClientOptions(api_endpoint=f"{LOCATION}-discoveryengine.googleapis.com")
        if LOCATION != "global"
        else None
    )

    client = discoveryengine.DocumentServiceClient(client_options=client_options)
    parent = f"projects/{PROJECT_ID}/locations/{LOCATION}/collections/default_collection/dataStores/{DATA_STORE_ID}/branches/default_branch"

    gcs_source = discoveryengine.GcsSource(
        input_uris=[f"gs://{GCS_BUCKET}/**/*.json"],
        data_schema="custom"
    )

    request = discoveryengine.ImportDocumentsRequest(
        parent=parent,
        gcs_source=gcs_source,
        reconciliation_mode=discoveryengine.ImportDocumentsRequest.ReconciliationMode.INCREMENTAL
    )

    try:
        operation = client.import_documents(request=request)
        print("Import operation started successfully.")
        print(f"Operation Name: {operation.operation.name}")
        print("You can check the status in the Google Cloud Console.")
    except Exception as e:
        print(f"Error starting import: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        GCS_BUCKET = sys.argv[1]
    import_documents()
