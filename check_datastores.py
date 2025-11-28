from google.cloud import discoveryengine_v1 as discoveryengine
import os

def list_datastores(project_id, location="global"):
    client = discoveryengine.DataStoreServiceClient()
    parent = f"projects/{project_id}/locations/{location}/collections/default_collection"
    
    try:
        print(f"Listing datastores in {parent}...")
        response = client.list_data_stores(parent=parent)
        for ds in response:
            print(f" - {ds.name} ({ds.display_name})")
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    if project_id:
        list_datastores(project_id)
    else:
        print("Please set GOOGLE_CLOUD_PROJECT env var")
