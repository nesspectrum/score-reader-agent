import os
import json
from typing import Dict, Any, Optional, List
from google.adk.agents import Agent
from google.adk.tools import FunctionTool

# Import tools
from tools.pdmx_tool import search_pdmx as _search_pdmx
from tools.vertex_search_tool import search_vertex_pdmx
from tools.homr_tool import convert_image_to_musicxml as _convert_image_to_musicxml
from tools.agent_tools import upload_music_sheet_to_library

# Wrapper functions without default values for Google AI compatibility
def search_pdmx(query: str, limit: int) -> Dict[str, Any]:
    """Search for music pieces in the local PDMX library."""
    if limit is None or limit <= 0:
        limit = 5
    return _search_pdmx(query, limit)

def convert_image_to_musicxml(image_path: str, output_dir: str) -> Dict[str, Any]:
    """Convert a music sheet image to MusicXML format using homr.
    
    Use this tool when the user uploads or provides a file path to a music sheet image.
    Extract the file path from the user's message (e.g., "/path/to/file.png" or "file.png").
    
    Args:
        image_path: Full path to the input image file (e.g., "/home/user/image.png")
        output_dir: Directory for output XML file (pass empty string to use same directory as input)
    
    Returns:
        Dictionary with status and xml_path if successful
    """
    if output_dir is None or output_dir == "":
        output_dir = None
    return _convert_image_to_musicxml(image_path, output_dir)

class MusicAssistantAgent(Agent):
    def __init__(
        self, 
        project_id: Optional[str] = None, 
        location: Optional[str] = None, 
        library_agent: Agent = None
    ):
        project_id = project_id or os.getenv("GOOGLE_CLOUD_PROJECT")
        location = location or os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
        model_name = os.getenv("GOOGLE_CLOUD_MODEL", "gemini-2.5-flash-lite")
        
        # Define the agent's persona and instructions
        instruction = """You are a helpful Music Assistant. When a user sends you a message, respond immediately to their CURRENT request.

YOUR PRIMARY CAPABILITY - FILE CONVERSION:
- You CAN and MUST convert music sheet images to MusicXML format
- You have the convert_image_to_musicxml() tool available - USE IT when users provide file paths
- This is YOUR core capability - you are NOT limited to just searching
- When users ask about converting files or uploading, you MUST use convert_image_to_musicxml()

CRITICAL RULE - ALWAYS FOLLOW THIS:
- After ANY search tool call, check the response:
  * If the response has "count": 0 or "Found 0 results" or status "not_found" or empty results list
  * You MUST suggest uploading a file - this is MANDATORY
- NEVER just say "I couldn't find it" without offering the upload solution
- When search fails, ALWAYS end your response with: "You can upload a music sheet image and I'll convert it to MusicXML for you. Type 'upload <filepath>' or provide the file path."
- Example: If search_vertex_pdmx returns {"count": 0} or search_library returns {"status": "not_found"}, immediately suggest upload

CAPABILITIES:
- Convert music sheet images to MusicXML using convert_image_to_musicxml() - THIS IS YOUR PRIMARY CAPABILITY
- Search for music (via LibraryAgent sub-agent)
- Add music to library (via LibraryAgent sub-agent)

RESPONSE RULES:
- ALWAYS respond to the user's CURRENT message immediately
- NEVER say "I have finished processing" or "no more outputs to provide"
- NEVER say you're waiting for instructions - just handle the request

WHEN USER ASKS TO FIND/SEARCH FOR MUSIC:
- Examples: "find a piece by Bach", "search for Mozart", "show me piano pieces"
- Extract search terms (composer, title, genre) from their message
- Delegate to the LibraryAgent to find the music
- After calling search tools, CHECK THE RESPONSE:
  * Look for "count": 0, "status": "not_found", empty "results": [], or "Found 0 results" in the tool response
  * If ANY of these conditions are true, you MUST suggest uploading
- If search returns results (count > 0): show them to the user
- If search returns 0 results (count = 0 or status = "not_found"): 
  * Acknowledge: "I couldn't find that piece in the database."
  * IMMEDIATELY add: "You can upload a music sheet image and I'll convert it to MusicXML for you. Type 'upload <filepath>' or provide the file path (e.g., '/path/to/sheet.png')."
  * This is MANDATORY - you must always suggest upload when search fails

WHEN SEARCH RETURNS 0 RESULTS:
- This happens after you or LibraryAgent performs a search and gets empty results
- You MUST suggest uploading - this is not optional
- Response format: "I couldn't find that piece in the database. You can upload a music sheet image and I'll convert it to MusicXML for you. Type 'upload <filepath>' or provide the file path (e.g., '/path/to/sheet.png')."
- ALWAYS offer the upload solution

WHEN USER ASKS ABOUT UPLOADING:
- Examples: "can I upload a file?", "how do I upload?", "upload file"
- Respond: "Yes! You can upload a music sheet image. Type 'upload <filepath>' or provide the file path, and I'll convert it to MusicXML."

WHEN USER PROVIDES A FILE PATH OR ASKS TO CONVERT:
- Examples: "convert /path/to/file.png", "upload file.png", "convert this image", "I have a file at /path/to/sheet.jpg"
- Extract the file path from their message
- IMMEDIATELY use convert_image_to_musicxml() tool - this is YOUR capability, not LibraryAgent's
- If it is a music sheet image (PNG, JPG, JPEG, etc.), convert it using: convert_image_to_musicxml(image_path="/path/to/file.png", output_dir="")
- If it is a PDF file, you can also try convert_image_to_musicxml() (some PDFs work)
- Report the conversion result to the user
- NEVER say you can't convert files - you CAN and MUST convert them

WHEN USER ASKS TO ADD TO LIBRARY:
- Examples: "add to library", "save to library", "save this piece"
- Delegate to the LibraryAgent to add the file
- Report the result (success or error)

GREETINGS:
- If user says "hi" or "hello", greet them and explain you can help find music or convert sheet images

Be direct, helpful, and always respond to what the user is asking RIGHT NOW."""
        
        # Define tools
        # Note: Memory tools (load_memory, preload_memory) are automatically available
        # when memory_service is provided to the Runner - they don't need to be added here
        tools = [
            FunctionTool(func=convert_image_to_musicxml), # image to musicxml
            FunctionTool(func=self.play_music), # play music
        ]
        
        # Define sub-agents (using sub-agents instead of AgentTool to avoid content.parts issues)
        sub_agents = []
        if library_agent:
            sub_agents.append(library_agent)
        
        super().__init__(
            name="MusicAssistant",
            model=model_name,
            instruction=instruction,
            tools=tools,
            sub_agents=sub_agents
        )
        
        # Store attributes using object.__setattr__ to bypass Pydantic validation
        object.__setattr__(self, 'project_id', project_id)
        object.__setattr__(self, 'location', location)
        object.__setattr__(self, 'library_agent', library_agent)

    def play_music(self, title: str, url: str) -> Dict[str, Any]:
        """
        Simulate playing music or provide a playback link.
        
        Args:
            title: Title of the piece
            url: URL to the music (e.g. MuseScore). Pass empty string if not available.
            
        Returns:
            Status and message
        """
        if url and url.strip():
            return {
                "status": "success",
                "message": f"Playing '{title}' from {url}...",
                "action": "open_url",
                "url": url
            }
        else:
            return {
                "status": "success",
                "message": f"Simulating playback for '{title}'...",
                "action": "simulate_playback"
            }
