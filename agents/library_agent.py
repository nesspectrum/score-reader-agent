import os
import json
from typing import Optional, Dict, Any, List
from google.adk.agents import Agent
from google.adk.tools import FunctionTool
from tools.library_manager import LibraryManager
from tools.vertex_search_tool import search_vertex_pdmx

class LibraryAgent(Agent):
    """
    An LLM-based agent that manages the music library.
    It uses LibraryManager to perform actual file operations.
    """
    def __init__(
        self, 
        library_manager: LibraryManager,
        model_name: str = "gemini-2.5-flash-lite",
        output_key: Optional[str] = None
    ):        
        instruction = """You are a helpful Library Agent responsible for managing a digital music sheet library.
        
        Your capabilities:
        1. Search the library for music pieces.
        2. Add new music sheets to the library.
        3. Search the Vertex AI Datastore for music using `search_vertex_pdmx`.
        4. Manage user preferences.
        
        When asked to find something:
        - Use the `search_library` tool.
        - If found, provide details about the piece (title, composer, key, etc.).
        - You can also use `search_vertex_pdmx` to search the cloud datastore if local search fails or if requested.
        - If not found, clearly state that.
        
        When asked to add something:
        - Use the `add_to_library` tool.
        - You need a file path and metadata (title, composer, etc.).
        
        When asked about preferences:
        - Use `get_user_preferences` to retrieve them.
        - Use `update_preference` to change them.
        
        Be concise and helpful.
        """
        
        tools = [
            FunctionTool(func=self.search_library),
            FunctionTool(func=search_vertex_pdmx),
            FunctionTool(func=self.add_to_library),
            FunctionTool(func=self.get_user_preferences),
            FunctionTool(func=self.update_preference)
        ]
        
        super().__init__(
            name="LibraryAgent",
            model=model_name,
            instruction=instruction,
            tools=tools,
            output_key=output_key
        )
        
        # Store library_manager
        object.__setattr__(self, 'library_manager', library_manager)

    def search_library(self, query: str) -> Dict[str, Any]:
        """
        Search the library for music sheets matching the query.
        
        Args:
            query: Search terms (composer, title, etc.)
            
        Returns:
            Dict with status and results. Status can be 'found', 'not_found', or 'error'.
            If status is 'not_found', the parent agent should try alternative search methods.
        """
        # This is a simple implementation. In a real system, we'd use a proper search index.
        # For now, we'll iterate through cached JSON files in the library directory.
        results = []
        try:
            for filename in os.listdir(self.library_manager.library_dir):
                if filename.endswith(".json") and filename != "user_preferences.json":
                    filepath = os.path.join(self.library_manager.library_dir, filename)
                    try:
                        with open(filepath, 'r') as f:
                            entry = json.load(f)
                            data = entry.get('data', {})
                            
                            # Simple string matching
                            search_text = f"{data.get('piece_name', '')} {data.get('composer', '')} {data.get('key', '')}".lower()
                            if query.lower() in search_text:
                                results.append(entry)
                    except Exception:
                        continue
        except Exception as e:
            print(f"Error searching library: {e}")
            return {
                "status": "error",
                "message": f"Error searching library: {e}",
                "results": []
            }
        
        if results:
            return {
                "status": "found",
                "count": len(results),
                "results": results
            }
        else:
            return {
                "status": "not_found",
                "message": f"No results found in local library for '{query}'. Try searching the cloud datastore or uploading a new sheet.",
                "results": []
            }

    def add_to_library(self, file_path: str, metadata: Dict[str, Any], user_id: Optional[str] = None) -> str:
        """
        Add a music sheet to the library.
        
        Args:
            file_path: Path to the file
            metadata: Metadata dictionary (must include 'data' key with extraction results)
            user_id: Optional user ID
            
        Returns:
            Success message or error
        """
        # Ensure metadata has 'data' key as expected by LibraryManager
        data = metadata.get('data', metadata)
        
        success = self.library_manager.save_to_library(file_path, data, user_id)
        if success:
            return f"Successfully added {os.path.basename(file_path)} to library."
        else:
            return "Failed to add file to library."

    def get_user_preferences(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get user preferences."""
        return self.library_manager.get_user_preferences(user_id)

    def update_preference(self, preference_type: str, value: Any, user_id: Optional[str] = None) -> str:
        """
        Update a user preference.
        
        Args:
            preference_type: Type of preference ('tempo', 'hand')
            value: New value
            user_id: Optional user ID
            
        Returns:
            Success message
        """
        self.library_manager.update_preference(preference_type, value, user_id)
        return f"Updated preference '{preference_type}' to '{value}'."
