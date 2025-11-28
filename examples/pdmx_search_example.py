"""
Example: Using Vertex AI Search with PDMX datastore

This example shows how to use the PDMX datastore with Vertex AI Search
using Gemini models with grounding.
"""

import os
import sys
import asyncio
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

load_dotenv()

try:
    import vertexai
    from vertexai.generative_models import (
        GenerativeModel,
        Tool,
        grounding
    )
    VERTEX_AI_AVAILABLE = True
except ImportError as e:
    VERTEX_AI_AVAILABLE = False
    print("=" * 60)
    print("ERROR: vertexai module not found")
    print("=" * 60)
    print("Please install: pip install google-cloud-aiplatform")
    sys.exit(1)

try:
    from google.cloud import discoveryengine_v1beta as discoveryengine
    DISCOVERY_ENGINE_AVAILABLE = True
except ImportError:
    DISCOVERY_ENGINE_AVAILABLE = False
    print("Warning: google-cloud-discoveryengine not installed")


def search_with_grounding_vertex_search(project_id: str, datastore_id: str, query: str):
    """
    Use Vertex AI Search as a grounding source for Gemini (Method 1 - Recommended)
    """
    location = "us-central1"  # Location for Vertex AI initialization
    
    # Initialize Vertex AI
    vertexai.init(project=project_id, location=location)
    
    # Create the grounding tool with Vertex AI Search
    tool = Tool.from_retrieval(
        grounding.Retrieval(
            grounding.VertexAISearch(
                datastore=f"projects/{project_id}/locations/global/collections/default_collection/dataStores/{datastore_id}"
            )
        )
    )
    
    # Initialize model with grounding
    model = GenerativeModel(
        "gemini-2.0-flash-lite",  # Supports grounding/retrieval
        tools=[tool]
    )
    
    # Generate content with grounding
    response = model.generate_content(query)
    
    print("Response:")
    print(response.text)
    print("\n" + "="*80 + "\n")
    
    # Check grounding metadata
    if hasattr(response, 'grounding_metadata') and response.grounding_metadata:
        print("Grounding Sources:")
        if hasattr(response.grounding_metadata, 'grounding_chunks'):
            for chunk in response.grounding_metadata.grounding_chunks:
                if hasattr(chunk, 'retrieval_metadata'):
                    print(f"  - Retrieved from datastore")
                elif hasattr(chunk, 'web'):
                    print(f"  - {chunk.web.uri}")
    
    return response


def direct_vertex_search(project_id: str, datastore_id: str, query: str):
    """
    Query Vertex AI Search directly without Gemini generation (Method 3)
    """
    if not DISCOVERY_ENGINE_AVAILABLE:
        print("Error: google-cloud-discoveryengine not installed")
        return None
    
    client = discoveryengine.SearchServiceClient()
    
    serving_config = f"projects/{project_id}/locations/global/collections/default_collection/dataStores/{datastore_id}/servingConfigs/default_config"
    
    request = discoveryengine.SearchRequest(
        serving_config=serving_config,
        query=query,
        page_size=10
    )
    
    response = client.search(request)
    
    print("Search Results:")
    for i, result in enumerate(response.results, 1):
        document = result.document
        struct_data = document.struct_data if hasattr(document, 'struct_data') else {}
        print(f"\n{i}. Title: {struct_data.get('title', 'N/A')}")
        print(f"   Composer: {struct_data.get('composer', 'N/A')}")
        print(f"   Key: {struct_data.get('key', 'N/A')}")
        print(f"   Tempo: {struct_data.get('tempo', 'N/A')}")
        print(f"   Measures: {struct_data.get('measure_count', 'N/A')}")
    
    return response


def search_then_generate(project_id: str, datastore_id: str, query: str):
    """
    First search Vertex AI Search, then use results with Gemini (Method 4 - Recommended for detailed responses)
    """
    if not DISCOVERY_ENGINE_AVAILABLE:
        print("Error: google-cloud-discoveryengine not installed")
        return None
    
    location = "us-central1"
    vertexai.init(project=project_id, location=location)
    
    # Step 1: Search Vertex AI Search
    search_client = discoveryengine.SearchServiceClient()
    serving_config = f"projects/{project_id}/locations/global/collections/default_collection/dataStores/{datastore_id}/servingConfigs/default_config"
    
    search_request = discoveryengine.SearchRequest(
        serving_config=serving_config,
        query=query,
        page_size=5
    )
    
    search_response = search_client.search(search_request)
    
    # Step 2: Extract relevant information
    context = []
    for result in search_response.results:
        doc = result.document
        struct_data = doc.struct_data if hasattr(doc, 'struct_data') else {}
        context.append({
            'title': struct_data.get('title', 'Unknown'),
            'composer': struct_data.get('composer', 'Unknown'),
            'key': struct_data.get('key', 'Unknown'),
            'tempo': struct_data.get('tempo', 'Unknown'),
            'measures': struct_data.get('measure_count', 'Unknown'),
        })
    
    if not context:
        print("STATUS: No records found in the dataset")
        return None
    
    # Step 3: Generate with Gemini using search results as context
    model = GenerativeModel("gemini-1.5-flash-002")
    
    prompt = f"""Based on the following search results from the PDMX music dataset:

{context}

IMPORTANT: Always begin your response by clearly stating whether records were found:
- If records are found: Start with "STATUS: Records found" and indicate how many records match the search.
- If no records are found: Start with "STATUS: No records found"

When records are found, provide detailed information about the pieces including composer, title, key, tempo, and measure count.
When no records are found, suggest alternative search terms or criteria that might help find what the user is looking for.

User query: {query}

Provide a helpful response:"""
    
    response = model.generate_content(prompt)
    
    print("Generated Response:")
    print(response.text)
    
    return response


async def example_search():
    """Example of searching the PDMX datastore using grounding."""
    
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    datastore_id = os.getenv("PDMX_DATASTORE_ID", "pdmx")
    
    if not project_id:
        print("Error: GOOGLE_CLOUD_PROJECT not set")
        return
    
    print("=" * 60)
    print("PDMX Search Example - Using Vertex AI Search Grounding")
    print("=" * 60)
    print(f"Project ID: {project_id}")
    print(f"Datastore ID: {datastore_id}")
    print("=" * 60)
    print()
    
    # Example queries
    queries = [
        "Find piano pieces in C Major by Bach",
        "Show me slow tempo pieces (tempo less than 100)",
        "Find pieces with more than 20 measures",
        "Search for pieces by Chopin in minor keys"
    ]
    
    for query in queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print('='*60)
        
        try:
            # Use Method 1: Grounding with Vertex AI Search (Recommended)
            print("\nMethod 1: Grounding with Vertex AI Search")
            print("-" * 60)
            search_with_grounding_vertex_search(project_id, datastore_id, query)
            
            # Also show Method 4: Search then Generate for comparison
            print("\nMethod 4: Search then Generate")
            print("-" * 60)
            search_then_generate(project_id, datastore_id, query)
            
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()


async def example_direct_search():
    """Example of using Vertex AI Search directly."""
    
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    datastore_id = os.getenv("PDMX_DATASTORE_ID", "pdmx")
    
    if not project_id:
        print("Error: GOOGLE_CLOUD_PROJECT not set")
        return
    
    query = "Bach piano pieces in C Major"
    print(f"\n{'='*60}")
    print("Direct Vertex AI Search Example")
    print("=" * 60)
    print(f"Query: {query}")
    print("=" * 60)
    
    try:
        direct_vertex_search(project_id, datastore_id, query)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("PDMX Search Example")
    print("=" * 60)
    
    if not VERTEX_AI_AVAILABLE:
        print("ERROR: Required packages not installed")
        print("Install with: pip install google-cloud-aiplatform google-cloud-discoveryengine")
        sys.exit(1)
    
    # Run direct search example
    print("\n1. Direct Search Example")
    asyncio.run(example_direct_search())
    
    # Run agent-based search example
    print("\n\n2. Search with Grounding Example")
    asyncio.run(example_search())
