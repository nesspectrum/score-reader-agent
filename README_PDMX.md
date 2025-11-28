# PDMX Dataset Integration

This project includes tools to convert the [PDMX dataset](https://zenodo.org/records/15571083) (Public Domain MusicXML) into a Vertex AI Search datastore.

## Quick Start

1. **Setup the datastore**:
   ```bash
   python setup_pdmx_datastore.py \
       --project-id YOUR_PROJECT_ID \
       --sample-size 1000
   ```

2. **Create datastore in Console**:
   - Follow instructions printed by the script
   - Or see [PDMX_DATASTORE_SETUP.md](./PDMX_DATASTORE_SETUP.md)

3. **Use in your agent**:
   ```python
   from google.adk.tools import VertexAiSearchTool
   
   search_tool = VertexAiSearchTool(
       project_id="your-project-id",
       location="us-central1",
       data_store_id="pdmx-musicxml"
   )
   ```

## Files

- `tools/pdmx_datastore.py` - Core processing functions
- `setup_pdmx_datastore.py` - Setup script
- `PDMX_DATASTORE_SETUP.md` - Detailed setup guide
- `examples/pdmx_search_example.py` - Usage examples

## Dataset Information

PDMX contains **250K+ public domain MusicXML scores** with:
- Composer information
- Key signatures
- Tempo markings
- Measure counts
- Ratings and metadata

See: https://zenodo.org/records/15571083



