# What does `pdmx_datastore.py` do?

## Overview

`pdmx_datastore.py` is a tool that processes the **PDMX (Public Domain MusicXML) dataset** and prepares it for use with **Google Cloud Vertex AI Search**. It converts music scores into searchable documents that can be queried using natural language.

## Main Functions

### 1. **Download PDMX Dataset** (`download_pdmx_dataset`)
- Downloads the PDMX dataset from Zenodo (record ID: 15571083)
- Downloads files:
  - `PDMX.csv` - Metadata file with all song information
  - `data.tar.gz` - MusicRender JSON files
  - `metadata.tar.gz` - Metadata JSON files  
  - `mxl.tar.gz` - Compressed MusicXML files
  - `subset_paths.tar.gz` - Subset definitions
- **Smart**: Skips files that already exist locally

### 2. **Extract Archives** (`extract_pdmx_archives`)
- Extracts all `.tar.gz` archives
- Creates directories: `data/`, `metadata/`, `mxl/`, `subset_paths/`
- **Smart**: Skips extraction if directories already exist

### 3. **Process MusicXML Files** (`process_musicxml_for_search`)
- Converts MusicXML files (`.mxl` or `.xml`) into searchable JSON documents
- Extracts metadata:
  - Title, composer, key signature, tempo
  - Measure count
  - Full music structure (notes, measures, etc.)
- Enriches with additional metadata from JSON files

### 4. **Upload to Google Cloud Storage** (`create_vertex_search_datastore`)
- Processes MusicXML files from the CSV metadata
- Converts each file into a JSON document
- Uploads documents to a GCS bucket: `gs://{bucket}/pdmx_documents/{id}.json`
- Creates the bucket if it doesn't exist

### 5. **Complete Setup** (`setup_pdmx_datastore`)
- Orchestrates all steps:
  1. Downloads dataset (or uses existing)
  2. Extracts archives (or uses existing)
  3. Creates GCS bucket
  4. Processes and uploads documents
- Returns instructions for creating Vertex AI Search datastore

## Workflow

```
PDMX Dataset (Zenodo)
    ↓
Download & Extract
    ↓
Process MusicXML → JSON Documents
    ↓
Upload to GCS
    ↓
Create Vertex AI Search Datastore (manual step)
    ↓
Searchable Music Database!
```

## Document Structure

Each uploaded document contains:

```json
{
  "id": "unique-document-id",
  "title": "Piece Name",
  "composer": "Composer Name",
  "key": "C Major",
  "tempo": "120",
  "measure_count": 24,
  "content": "{full JSON representation of music}",
  "metadata": {
    "rating": 4.5,
    "genres": ["Classical", "Piano"],
    ...
  },
  "file_path": "path/to/file.mxl"
}
```

## Usage Examples

### Upload 100 Samples

```bash
# Using the convenience script
python upload_pdmx_samples.py

# Or using the setup script directly
python setup_pdmx_datastore.py \
    --project-id kaggle-capstone-112025 \
    --sample-size 100 \
    --download-dir ./pdmx_data
```

### Upload All Documents (250K+)

```bash
python setup_pdmx_datastore.py \
    --project-id kaggle-capstone-112025 \
    --sample-size 0  # 0 or omit for all
```

### Using Python API

```python
from tools.pdmx_datastore import setup_pdmx_datastore

result = setup_pdmx_datastore(
    project_id="kaggle-capstone-112025",
    location="us-central1",
    data_store_id="pdmx-musicxml",
    download_dir="./pdmx_data",
    sample_size=100  # Upload 100 samples
)

if result["status"] == "success":
    print(f"Uploaded {result['documents_processed']} documents")
    print(f"GCS Bucket: {result['gcs_bucket']}")
```

## Key Features

✅ **Resumable**: Skips already downloaded/extracted files  
✅ **Configurable**: Control sample size, bucket name, location  
✅ **Error Handling**: Returns detailed error messages  
✅ **Progress Tracking**: Shows progress every 100 documents  
✅ **Smart Processing**: Only processes files that exist  

## What Happens After Upload?

After uploading to GCS, you need to create the Vertex AI Search datastore:

1. Go to [Google Cloud Console - AI Applications](https://console.cloud.google.com/ai/applications)
2. Click "Data Stores" > "Create data store"
3. Select "Cloud Storage" as data source
4. Choose your GCS bucket: `gs://{project-id}-pdmx-datastore/pdmx_documents/`
5. Set data type to "Unstructured"
6. Enter data store ID: `pdmx-musicxml`
7. Wait for ingestion to complete

## Storage Requirements

- **100 samples**: ~50MB download, ~10-15 minutes processing, ~10-20MB in GCS
- **Full dataset**: ~14GB download, several hours processing, ~1-2GB per 10K documents in GCS

## Current Status

Your setup:
- ✅ Data directory: `./pdmx_data` (symlinked to external drive)
- ✅ Archives extracted: `data/`, `metadata/`, `mxl/`, `subset_paths/`
- ✅ CSV metadata: `PDMX.csv` available
- ✅ Ready to process and upload!

