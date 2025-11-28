# Create Datastore from GCS Bucket

This guide explains how to create a Vertex AI Search (Discovery Engine) datastore from files already uploaded to a Google Cloud Storage bucket.

## Prerequisites

1. **Google Cloud Project** with billing enabled
2. **Required APIs enabled**:
   ```bash
   gcloud services enable discoveryengine.googleapis.com --project=YOUR_PROJECT_ID
   ```
3. **Authentication**:
   ```bash
   gcloud auth application-default login
   ```
4. **Python packages**:
   ```bash
   pip install google-cloud-discoveryengine
   ```

## Usage

### Basic Usage

Create a datastore from a GCS bucket:

```bash
python create_datastore_from_gcs.py \
    --project-id kaggle-capstone-112025 \
    --display-name "PDMX MusicXML Dataset" \
    --gcs-uri "gs://kaggle-capstone-112025-pdmx-datastore/pdmx_documents/"
```

### With Custom Datastore ID

```bash
python create_datastore_from_gcs.py \
    --project-id kaggle-capstone-112025 \
    --display-name "PDMX MusicXML Dataset" \
    --gcs-uri "gs://kaggle-capstone-112025-pdmx-datastore/pdmx_documents/" \
    --datastore-id pdmx-musicxml \
    --location us-central1
```

### List Existing Datastores

```bash
python create_datastore_from_gcs.py \
    --project-id kaggle-capstone-112025 \
    --list
```

## Using as Python Module

```python
from create_datastore_from_gcs import create_datastore_from_gcs

result = create_datastore_from_gcs(
    project_id="kaggle-capstone-112025",
    datastore_display_name="PDMX MusicXML Dataset",
    gcs_uri="gs://kaggle-capstone-112025-pdmx-datastore/pdmx_documents/",
    location="us-central1",
    datastore_id="pdmx-musicxml"
)

if result["status"] == "success":
    print(f"Datastore created: {result['datastore_name']}")
    print(f"Datastore ID: {result['datastore_id']}")
```

## GCS URI Format

The GCS URI should point to:
- **Directory**: `gs://bucket-name/path/to/documents/` (all files in directory)
- **File pattern**: `gs://bucket-name/path/to/*.json` (specific pattern)
- **Single file**: `gs://bucket-name/path/to/file.jsonl` (single file)

For PDMX data, use:
```
gs://kaggle-capstone-112025-pdmx-datastore/pdmx_documents/
```

## What Happens

1. **Creates the datastore** in Vertex AI Search
2. **Imports data** from the GCS bucket
3. **Waits for completion** (may take several minutes)
4. **Returns datastore information** for use with VertexAiSearchTool

## Using the Created Datastore

Once created, use it with `VertexAiSearchTool`:

```python
from google.adk.tools import VertexAiSearchTool

search_tool = VertexAiSearchTool(
    project_id="kaggle-capstone-112025",
    location="us-central1",
    data_store_id="pdmx-musicxml"  # The datastore_id you used
)
```

## Troubleshooting

### Error: "API not enabled"

Enable the Discovery Engine API:
```bash
gcloud services enable discoveryengine.googleapis.com --project=YOUR_PROJECT_ID
```

### Error: "Permission denied"

Grant necessary permissions:
```bash
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="user:$(gcloud config get-value account)" \
    --role="roles/discoveryengine.admin"
```

### Error: "Datastore already exists"

Use `--list` to see existing datastores, or use a different `--datastore-id`.

### Import Takes Too Long

Large datasets can take 30+ minutes to import. The script will wait up to 10 minutes. For longer imports, check status in the Google Cloud Console.

## Example: Complete Workflow

```bash
# 1. Upload data to GCS (already done)
# gs://kaggle-capstone-112025-pdmx-datastore/pdmx_documents/

# 2. Create datastore
python create_datastore_from_gcs.py \
    --project-id kaggle-capstone-112025 \
    --display-name "PDMX MusicXML Dataset" \
    --gcs-uri "gs://kaggle-capstone-112025-pdmx-datastore/pdmx_documents/" \
    --datastore-id pdmx-musicxml

# 3. Use in your code
python examples/pdmx_search_example.py
```

## Function Reference

### `create_datastore_from_gcs()`

Creates a datastore and imports data from GCS.

**Parameters:**
- `project_id` (str): GCP project ID
- `datastore_display_name` (str): Display name for the datastore
- `gcs_uri` (str): GCS URI pointing to the data
- `location` (str): GCP location (default: "us-central1")
- `datastore_id` (str, optional): Custom datastore ID
- `solution_types` (list, optional): Solution types (default: ["SOLUTION_TYPE_SEARCH"])

**Returns:**
- Dictionary with status and datastore information

### `import_gcs_data()`

Imports data from GCS into an existing datastore.

**Parameters:**
- `project_id` (str): GCP project ID
- `datastore_name` (str): Full datastore name
- `gcs_uri` (str): GCS URI pointing to the data
- `location` (str): GCP location

**Returns:**
- Dictionary with import status

### `list_datastores()`

Lists all datastores in a project.

**Parameters:**
- `project_id` (str): GCP project ID
- `location` (str): GCP location

**Returns:**
- Dictionary with list of datastores

