from typing import List, Dict, Any, Optional
import os

try:
    from google.cloud import discoveryengine_v1beta as discoveryengine
    from google.api_core.client_options import ClientOptions
    VERTEX_SEARCH_AVAILABLE = True
except ImportError:
    VERTEX_SEARCH_AVAILABLE = False

class VertexSearchTool:
    def __init__(
        self, 
        project_id: str, 
        location: Optional[str] = None, 
        data_store_id: Optional[str] = None
    ):
        self.project_id = project_id
        # Get from environment if not provided
        self.location = location or os.getenv("GOOGLE_CLOUD_LOCATION", "global")
        self.data_store_id = data_store_id or os.getenv("PDMX_DATASTORE_ID", "pdmx-musicxml")
        self.client = None
        
    def _get_client(self):
        if not VERTEX_SEARCH_AVAILABLE:
            raise ImportError("google-cloud-discoveryengine is not installed.")
            
        if not self.client:
            client_options = (
                ClientOptions(api_endpoint=f"{self.location}-discoveryengine.googleapis.com")
                if self.location != "global"
                else None
            )
            self.client = discoveryengine.SearchServiceClient(client_options=client_options)
        return self.client

    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search the Vertex AI Datastore.
        """
        if not VERTEX_SEARCH_AVAILABLE:
            print("Error: google-cloud-discoveryengine is not installed")
            return []
            
        try:
            client = self._get_client()
            
            # Construct serving config path manually for v1beta
            serving_config = (
                f"projects/{self.project_id}/locations/{self.location}/"
                f"collections/default_collection/dataStores/{self.data_store_id}/"
                f"servingConfigs/default_config"
            )
            
            # Only print if query is meaningful (not empty or system instruction)
            if query and query.strip() and not query.startswith("Handle the requests"):
                print(f"Searching datastore: {self.data_store_id} in {self.location}")
                print(f"Query: {query}")

            request = discoveryengine.SearchRequest(
                serving_config=serving_config,
                query=query,
                page_size=limit,
                content_search_spec=discoveryengine.SearchRequest.ContentSearchSpec(
                    snippet_spec=discoveryengine.SearchRequest.ContentSearchSpec.SnippetSpec(
                        return_snippet=True
                    )
                ),
            )

            response = client.search(request)
            
            print(f"Found {len(response.results)} results")
            
            results = []
            for result in response.results:
                data = {}
                # Extract structured data if available
                if hasattr(result.document, 'struct_data') and result.document.struct_data:
                    # Convert proto to dict
                    try:
                        import proto
                        data = proto.Message.to_dict(result.document.struct_data)
                    except:
                        # Fallback: manually extract fields
                        struct_data = result.document.struct_data
                        if hasattr(struct_data, 'fields'):
                            for key, value in struct_data.fields.items():
                                # Extract value from proto Value type
                                if hasattr(value, 'string_value'):
                                    data[key] = value.string_value
                                elif hasattr(value, 'number_value'):
                                    data[key] = value.number_value
                                elif hasattr(value, 'list_value'):
                                    data[key] = [v.string_value for v in value.list_value.values]
                
                # Add document ID and title
                data['id'] = result.document.id
                if 'title' not in data:
                    data['title'] = result.document.id
                
                # Add snippet if available
                if hasattr(result, 'document_snippets') and result.document_snippets:
                    snippets = []
                    for snippet in result.document_snippets:
                        if hasattr(snippet, 'snippet') and snippet.snippet:
                            snippets.append(snippet.snippet)
                    if snippets:
                        data['snippet'] = ' '.join(snippets)
                
                results.append(data)
                
            return results
            
        except Exception as e:
            print(f"Vertex Search Error: {e}")
            import traceback
            traceback.print_exc()
            return []

def search_vertex_pdmx(query: str) -> Dict[str, Any]:
    """
    Search the PDMX library in Vertex AI Search.
    
    Args:
        query: Search query
        
    Returns:
        Dictionary with search results
    """
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    if not project_id:
        return {"status": "error", "error_message": "GOOGLE_CLOUD_PROJECT not set"}
    
    location = os.getenv("GOOGLE_CLOUD_LOCATION", "global")
    data_store_id = os.getenv("PDMX_DATASTORE_ID", "pdmx-musicxml")
        
    tool = VertexSearchTool(
        project_id=project_id,
        location=location,
        data_store_id=data_store_id
    )
    results = tool.search(query)
    
    return {
        "status": "success",
        "source": "vertex_ai_search",
        "count": len(results),
        "results": results
    }
