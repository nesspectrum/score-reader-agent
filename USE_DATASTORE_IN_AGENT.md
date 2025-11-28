# How to Use Your Datastore in the Agent

Your datastore has been created successfully:
- **Datastore ID**: `pdmx`
- **Location**: `global`
- **Full Path**: `projects/520427885790/locations/global/collections/default_collection/dataStores/pdmx`

## Quick Start

### 1. Set Environment Variables

Add to your `.env` file:

```bash
GOOGLE_CLOUD_PROJECT=kaggle-capstone-112025
GOOGLE_CLOUD_LOCATION=global
PDMX_DATASTORE_ID=pdmx
```

### 2. Use in Your Agent Code

```python
import os
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.tools import VertexAiSearchTool

load_dotenv()

# Initialize the search tool with your datastore
search_tool = VertexAiSearchTool(
    project_id=os.getenv("GOOGLE_CLOUD_PROJECT"),
    location="global",  # Must be "global" for Discovery Engine
    data_store_id="pdmx"  # Your datastore ID
)

# Create an agent with search capability
agent = Agent(
    name="MusicSearchAgent",
    model="gemini-2.5-flash-lite",
    tools=[search_tool],
    instruction="""
    You are a music search assistant with access to a large database of public domain music.
    Help users find music pieces by composer, key, tempo, or other characteristics.
    
    IMPORTANT: Always begin your response by clearly stating whether records were found:
    - If records are found: Start with "STATUS: Records found" and indicate how many.
    - If no records are found: Start with "STATUS: No records found".
    
    When records are found, provide detailed information about the pieces.
    When no records are found, suggest alternative search terms or uploading music sheets.
    """
)

# Use the agent
import asyncio

async def search_music(query: str):
    response = await agent.run(query)
    return response

# Example usage
result = asyncio.run(search_music("Find piano pieces in C Major by Bach"))
print(result)
```

## Complete Example

See `examples/pdmx_search_example.py` for a complete working example:

```bash
python examples/pdmx_search_example.py
```

## Integration with Library Agent

You can combine the search tool with your library agent:

```python
from google.adk.agents import Agent
from google.adk.tools import VertexAiSearchTool, FunctionTool
from agents.library_agent import LibraryAgent
from agents.memory_service import SimpleMemoryService
from tools.agent_tools import upload_music_sheet_to_library, get_user_preferences

# Initialize search tool
search_tool = VertexAiSearchTool(
    project_id="kaggle-capstone-112025",
    location="global",
    data_store_id="pdmx"
)

# Initialize library agent
memory_service = SimpleMemoryService()
library_agent = LibraryAgent(memory_service=memory_service)

# Create library tools
def upload_to_library(file_path: str, user_id: str = "default_user") -> dict:
    return upload_music_sheet_to_library(file_path, user_id, library_agent)

library_tools = [
    FunctionTool(func=upload_to_library),
    FunctionTool(func=lambda user_id="default_user": get_user_preferences(user_id, library_agent))
]

# Create agent with both search and library capabilities
agent = Agent(
    name="MusicSearchAgent",
    model="gemini-2.5-flash-lite",
    tools=[search_tool] + library_tools,
    instruction="..."  # Your instruction
)
```

## Direct Search (Without Agent)

You can also use the search tool directly:

```python
from google.adk.tools import VertexAiSearchTool
import asyncio

search_tool = VertexAiSearchTool(
    project_id="kaggle-capstone-112025",
    location="global",
    data_store_id="pdmx"
)

async def search():
    results = await search_tool("Bach piano pieces in C Major")
    print(f"Found {len(results.get('results', []))} results")
    for result in results.get('results', [])[:5]:
        print(f"- {result.get('title')} by {result.get('composer')}")

asyncio.run(search())
```

## Important Notes

1. **Location**: Must be `"global"` (not `"us-central1"`) for Discovery Engine API
2. **Datastore ID**: Use `"pdmx"` (the ID you created)
3. **Project ID**: Use your project ID (`kaggle-capstone-112025`)
4. **Data Import**: Make sure data has been imported into the datastore before searching

## Troubleshooting

### Error: "Datastore not found"
- Verify the datastore ID is correct: `pdmx`
- Check that location is `"global"`
- Ensure the datastore exists in your project

### Error: "No results found"
- Check if data has been imported into the datastore
- Verify the GCS bucket contains JSON/JSONL files
- Wait for import to complete (check Google Cloud Console)

### Error: "Permission denied"
- Ensure your account has Discovery Engine User role
- Check IAM permissions for the project

## Next Steps

1. **Import Data**: If you haven't imported data yet, use the import script or Google Cloud Console
2. **Test Search**: Run `python examples/pdmx_search_example.py` to test
3. **Integrate**: Add the search tool to your main application

