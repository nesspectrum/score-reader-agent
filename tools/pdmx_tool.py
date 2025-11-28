import os
import csv
import json
from typing import List, Dict, Any, Optional

class PDMXSearchTool:
    def __init__(self, pdmx_dir: str = "./pdmx_data"):
        self.pdmx_dir = pdmx_dir
        self.csv_path = os.path.join(pdmx_dir, "PDMX.csv")
        self._index: List[Dict[str, str]] = []
        self._loaded = False

    def _load_index(self):
        """Load the PDMX CSV index into memory."""
        if self._loaded:
            return

        if not os.path.exists(self.csv_path):
            print(f"Warning: PDMX CSV not found at {self.csv_path}")
            return

        try:
            with open(self.csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                # We only keep essential columns to save memory if needed, 
                # but for 200MB we can probably keep it all or just what we need for search.
                # Let's keep relevant fields for search and identification.
                for row in reader:
                    self._index.append({
                        'title': row.get('title', ''),
                        'song_name': row.get('song_name', ''),
                        'composer_name': row.get('composer_name', ''),
                        'artist_name': row.get('artist_name', ''),
                        'genres': row.get('genres', ''),
                        'metadata_path': row.get('metadata', ''),
                        'mxl_path': row.get('mxl', ''),
                        'pdf_path': row.get('pdf', ''),
                        'complexity': row.get('complexity', '0'),
                        'rating': row.get('rating', '0')
                    })
            self._loaded = True
            print(f"Loaded {len(self._index)} items from PDMX index.")
        except Exception as e:
            print(f"Error loading PDMX index: {e}")

    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search the PDMX library for music pieces.
        
        Args:
            query: Search query (title, composer, etc.)
            limit: Maximum number of results
            
        Returns:
            List of matching results with metadata
        """
        self._load_index()
        if not self._index:
            return []

        query = query.lower()
        results = []
        
        # Simple keyword search
        # Rank matches: exact title > title contains > composer contains > others
        
        # We can do a single pass and score them
        scored_results = []
        
        for item in self._index:
            score = 0
            title = item['title'].lower()
            song = item['song_name'].lower()
            composer = item['composer_name'].lower()
            artist = item['artist_name'].lower()
            
            if query == title or query == song:
                score += 100
            elif query in title or query in song:
                score += 50
            
            if query in composer or query in artist:
                score += 30
                
            if score > 0:
                scored_results.append((score, item))
        
        # Sort by score desc
        scored_results.sort(key=lambda x: x[1]['rating'], reverse=True) # Secondary sort by rating
        scored_results.sort(key=lambda x: x[0], reverse=True)
        
        top_results = [item for score, item in scored_results[:limit]]
        
        # Enrich with full path
        for res in top_results:
            # Resolve paths relative to pdmx_dir
            if res['metadata_path']:
                res['full_metadata_path'] = os.path.join(self.pdmx_dir, res['metadata_path'].lstrip('./'))
            if res['mxl_path']:
                res['full_mxl_path'] = os.path.join(self.pdmx_dir, res['mxl_path'].lstrip('./'))
                
        return top_results

    def get_details(self, metadata_path: str) -> Dict[str, Any]:
        """
        Get full details from the metadata JSON file.
        """
        full_path = metadata_path
        if not os.path.isabs(full_path):
             full_path = os.path.join(self.pdmx_dir, metadata_path.lstrip('./'))
             
        if os.path.exists(full_path):
            try:
                with open(full_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                return {"error": str(e)}
        return {"error": "File not found"}

# Global instance
_pdmx_tool = None

def get_pdmx_tool():
    global _pdmx_tool
    if _pdmx_tool is None:
        _pdmx_tool = PDMXSearchTool()
    return _pdmx_tool

def search_pdmx(query: str, limit: int) -> Dict[str, Any]:
    """
    Search for music pieces in the local PDMX library.
    
    Args:
        query: Search terms (title, composer, etc.)
        limit: Max results to return
        
    Returns:
        Dictionary with search results
    """
    try:
        print(f"Searching local PDMX database for: '{query}'")
        tool = get_pdmx_tool()
        
        # Check if index is loaded
        if not tool._loaded:
            tool._load_index()
        
        if not tool._index:
            print(f"Warning: PDMX index is empty. CSV file: {tool.csv_path}")
            return {
                "status": "error",
                "error_message": f"PDMX index not loaded. Check if CSV exists at {tool.csv_path}",
                "query": query,
                "count": 0,
                "results": []
            }
        
        print(f"PDMX index loaded: {len(tool._index)} items")
        # Use default limit of 5 if not provided or invalid
        if limit is None or limit <= 0:
            limit = 5
        results = tool.search(query, limit)
        print(f"Found {len(results)} results")
        
        return {
            "status": "success",
            "query": query,
            "count": len(results),
            "results": results
        }
    except Exception as e:
        import traceback
        print(f"Error in search_pdmx: {e}")
        traceback.print_exc()
        return {
            "status": "error",
            "error_message": str(e),
            "query": query,
            "count": 0,
            "results": []
        }
