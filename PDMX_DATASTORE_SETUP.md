# PDMX to Vertex AI Search Datastore Setup

This guide explains how to convert the [PDMX dataset](https://zenodo.org/records/15571083) (Public Domain MusicXML) into a Vertex AI Search datastore for use with `VertexAiSearchTool`.

## Overview

The PDMX dataset contains over 250K public domain MusicXML scores from MuseScore. This tool:
1. Downloads the PDMX dataset metadata
2. Processes MusicXML files into searchable documents
3. Uploads documents to Google Cloud Storage
4. Creates a Vertex AI Search datastore

## Prerequisites

1. **Google Cloud Project** with billing enabled
2. **Required APIs enabled**:
   ```bash
   gcloud services enable discoveryengine.googleapis.com
   gcloud services enable storage.googleapis.com
   ```
3. **Authentication**:
   ```bash
   gcloud auth application-default login
   ```
4. **Python packages**:
   ```bash
   pip install google-cloud-storage
   ```
5. **Download tools**: `wget` or `curl` installed

## Quick Start

### Option 1: Using the Setup Script

```bash
python setup_pdmx_datastore.py \
    --project-id YOUR_PROJECT_ID \
    --location us-central1 \
    --data-store-id pdmx-musicxml \
    --sample-size 1000
```

### Option 2: Using Python API

```python
from tools.pdmx_datastore import setup_pdmx_datastore

result = setup_pdmx_datastore(
    project_id="your-project-id",
    location="us-central1",
    data_store_id="pdmx-musicxml",
    sample_size=1000  # Process first 1000 documents
)

if result["status"] == "success":
    print(f"Datastore created: {result['datastore_name']}")
```

## Step-by-Step Process

### 1. Download PDMX Dataset

The tool downloads:
- `PDMX.csv` - Metadata file with all song information
- `data.tar.gz` - MusicRender JSON files
- `metadata.tar.gz` - Metadata JSON files
- `mxl.tar.gz` - Compressed MusicXML files
- `subset_paths.tar.gz` - Subset definitions

**Note**: The full dataset is ~14GB. For testing, you can use `--sample-size` to limit processing.

### 2. Extract Archives

All `.tar.gz` files are automatically extracted to the download directory.

### 3. Process MusicXML Files

Each MusicXML file is:
- Parsed into structured JSON format
- Enriched with metadata (composer, title, key, tempo, etc.)
- Converted to searchable document format

### 4. Upload to Google Cloud Storage

Documents are uploaded as JSON files to a GCS bucket:
- Default bucket: `{project-id}-pdmx-datastore`
- Path: `gs://{bucket}/pdmx_documents/{document_id}.json`

### 5. Create Vertex AI Search Datastore

**Important**: After uploading to GCS, create the datastore manually:

1. Go to [Google Cloud Console - AI Applications](https://console.cloud.google.com/ai/applications)
2. Click "Data Stores" > "Create data store"
3. Select "Cloud Storage" as data source
4. Choose your GCS bucket: `gs://{bucket}/pdmx_documents/`
5. Set data type to "Unstructured"
6. Enter your data store ID (e.g., `pdmx-musicxml`)
7. Wait for ingestion to complete (check Activity tab)

Alternatively, use gcloud CLI:
```bash
gcloud alpha discovery-engine data-stores create \
    --data-store-id=pdmx-musicxml \
    --display-name="PDMX MusicXML Dataset" \
    --solution-types=SOLUTION_TYPE_SEARCH \
    --location=us-central1
```

## Using the Datastore

Once created, you can use `VertexAiSearchTool` in your agents:

```python
from google.adk.tools import VertexAiSearchTool

# Initialize the search tool
search_tool = VertexAiSearchTool(
    project_id="your-project-id",
    location="us-central1",
    data_store_id="pdmx-musicxml"
)

# Use in an agent
from google.adk.agents import Agent
from google.adk.tools import FunctionTool

agent = Agent(
    name="MusicSearchAgent",
    model="gemini-2.5-flash-lite",
    tools=[search_tool]
)

# Search for music
result = await agent.run("Find piano pieces in C Major by Bach")
```

## Document Structure

Each document in the datastore contains:

```json
{
  "id": "unique-document-id",
  "title": "Piece Name",
  "composer": "Composer Name",
  "key": "C Major",
  "tempo": "120",
  "measure_count": 24,
  "content": "{full JSON representation}",
  "metadata": {
    "rating": 4.5,
    "genres": ["Classical", "Piano"],
    "n_views": 1000,
    ...
  },
  "file_path": "path/to/file.mxl"
}
```

## Configuration Options

### Sample Size

Process a subset for testing:
```bash
--sample-size 100  # Process first 100 documents
```

### Custom GCS Bucket

```bash
--gcs-bucket my-custom-bucket-name
```

### Custom Download Directory

```bash
--download-dir /path/to/pdmx/data
```

## Performance Considerations

- **Full dataset**: ~250K documents, ~14GB download, several hours to process
- **Sample (1000 docs)**: ~50MB download, ~10-15 minutes to process
- **Storage**: ~1-2GB per 10K documents in GCS

## Troubleshooting

### Download Fails

Ensure `wget` or `curl` is installed:
```bash
# Ubuntu/Debian
sudo apt-get install wget

# macOS
brew install wget
```

### GCS Permission Errors

Ensure your account has Storage Admin role:
```bash
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="user:YOUR_EMAIL" \
    --role="roles/storage.admin"
```

### Discovery Engine API Not Enabled

```bash
gcloud services enable discoveryengine.googleapis.com
```

## Dataset Information

The PDMX dataset includes:
- **250K+ public domain scores**
- **Multiple formats**: MusicXML, PDF, MIDI
- **Rich metadata**: Ratings, genres, tags, composer info
- **Quality filters**: Rated, deduplicated subsets

For more information, see: https://zenodo.org/records/15571083

## Citation

If you use PDMX in your research, please cite:

```bibtex
@dataset{pdmx_2025,
  title={PDMX: A Large-Scale Public Domain MusicXML Dataset},
  author={Long, Phillip and Novack, Zachary and McAuley, Julian and Berg-Kirkpatrick, Taylor},
  year={2025},
  publisher={Zenodo},
  doi={10.5281/zenodo.15571083}
}
```

