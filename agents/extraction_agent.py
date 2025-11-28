import os
import json
from typing import Optional, Dict, Any, List
from google.adk.agents import Agent
from google.adk.tools import FunctionTool

# Import tool functions
from tools.agent_tools import (
    get_note_frequency,
    generate_tone,
    validate_music_data,
    get_music_statistics,
    suggest_corrections,
    get_user_preferences,
    search_sample_music,
    validate_measure_duration,
    validate_all_measures
)
from tools.homr_tool import convert_image_to_musicxml
from tools.musicxml_parser import parse_musicxml_to_json
from tools.pdmx_tool import search_pdmx

class ExtractionAgent(Agent):
    def __init__(
        self, 
        project_id=None, 
        location="us-central1", 
        session_service=None,
        library_agent=None,
        enable_tools: bool = True
    ):
        project_id = project_id or os.getenv("GOOGLE_CLOUD_PROJECT")
        location = location or os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
        model_name = os.getenv("GOOGLE_CLOUD_MODEL", "gemini-2.5-flash-lite")
        
        # Initialize ADK Agent with memory-aware instructions
        instruction = """You are a music sheet analysis expert. Your task is to extract structured information from music sheets.
        Extract the following information in JSON format:
        1. "piece_name": The name/title of the piece (e.g., "Prelude in C Major", "Moonlight Sonata")
        2. "composer": The composer's name if visible (e.g., "Bach", "Beethoven")
        3. "key": Key signature (e.g., "C Major").
        4. "tempo": Tempo indication (e.g., "120"), or null.
        5. "measures": A list of measures. Each measure has:
            - "id": Measure number.
            - "right_hand": List of events. Each event has:
                - "notes": List of pitches (e.g., ["C4", "E4"]). Use ["C4", "E4"]). Use ["Rest"] for rests.
                - "duration": Duration (e.g., "quarter", "half").
            - "left_hand": List of events (same structure as right_hand).
        
        Learn from past extractions and user corrections to improve accuracy. Consider common patterns 
        and user preferences when extracting similar music sheets.
        
        You have access to tools for:
        - Validating extracted music data
        - Getting note frequencies
        - Calculating music statistics
        - Suggesting corrections based on patterns
        - Accessing user preferences
        - Searching for sample music files
        - Searching the PDMX library for ground truth data
        
        After extraction, use the search_sample_music tool to find sample audio files for the piece.
        Use search_pdmx to check if the piece exists in the local library and verify metadata (key, composer, etc.)."""
        
        # Prepare tools
        tools = []
        if enable_tools:
            # Create tool instances with bound library_agent for get_user_preferences
            # Note: We'll bind library_agent after initialization
            tools = [
                FunctionTool(func=validate_music_data),
                FunctionTool(func=get_music_statistics),
                FunctionTool(func=get_note_frequency),
                FunctionTool(func=suggest_corrections),
                FunctionTool(func=search_sample_music),
                FunctionTool(func=validate_measure_duration),
                FunctionTool(func=validate_all_measures),
                FunctionTool(func=convert_image_to_musicxml),
                FunctionTool(func=search_pdmx),
            ]
            
            # Add Google Search tool if available
            try:
                from google.adk.tools import google_search
                tools.append(google_search)
            except ImportError:
                pass  # Google Search not available, continue without it
        
        # Initialize parent Agent (Pydantic model)
        super().__init__(
            name="MusicSheetExtractor",
            model=model_name,
            instruction=instruction,
            tools=tools if tools else None
        )
        
        # Store additional attributes using object.__setattr__ to bypass Pydantic validation
        object.__setattr__(self, 'project_id', project_id)
        object.__setattr__(self, 'location', location)
        object.__setattr__(self, 'session_service', session_service)
        object.__setattr__(self, 'library_agent', library_agent)
        object.__setattr__(self, 'extraction_history', [])
        object.__setattr__(self, 'enable_tools', enable_tools)
        
        # Add get_user_preferences tool if library_agent is available
        if enable_tools and library_agent:
            def get_user_prefs_wrapper(user_id: str) -> Dict[str, Any]:
                return get_user_preferences(user_id, self.library_agent)
            
            # Add to tools list
            if self.tools:
                self.tools.append(FunctionTool(func=get_user_prefs_wrapper))
            else:
                object.__setattr__(self, 'tools', [FunctionTool(func=get_user_prefs_wrapper)])

    def _load_extraction_memory(self) -> str:
        """Load relevant extraction patterns from memory."""
        return ""
    
    def _get_user_preferences_context(self) -> str:
        """Get user preferences from memory to guide extraction."""
        return ""
    
    async def extract(self, file_path, user_id: Optional[str] = None):
        print(f"Extracting notes from {file_path}...")
        
        # Step 1: Check library for existing XML file
        if self.library_agent:
            xml_path = self.library_agent.get_cached_xml(file_path)
            if xml_path:
                print(f"Found existing MusicXML file: {xml_path}")
                print("Parsing MusicXML to JSON format...")
                parsed_data = parse_musicxml_to_json(xml_path)
                
                if parsed_data.get("status") == "success":
                    # Remove status field and return data
                    extracted_data = {k: v for k, v in parsed_data.items() if k != "status"}
                    
                    # Validate and process the extracted data
                    if self.enable_tools:
                        validation_result = validate_music_data(extracted_data)
                        if not validation_result.get('valid'):
                            print(f"Warning: Validation found issues: {validation_result.get('errors', [])}")
                        else:
                            print("✓ Extraction structure validated successfully")
                    
                    # Store extraction pattern in memory
                    if self.memory_service and user_id:
                        self._store_extraction_pattern(file_path, extracted_data, user_id)
                    
                    return extracted_data
                else:
                    print(f"Warning: Failed to parse XML: {parsed_data.get('error_message')}")
                    print("Falling back to image extraction...")
        
        # Step 2: If no XML found, try to convert image to XML using homr
        # Check if file is an image (not PDF)
        is_image = file_path.lower().endswith((".png", ".jpg", ".jpeg"))
        
        if is_image:
            print("No XML found in library. Attempting to convert image to MusicXML using homr...")
            homr_result = convert_image_to_musicxml(file_path)
            
            if homr_result.get("status") == "success":
                xml_path = homr_result.get("xml_path")
                print(f"Successfully converted to MusicXML: {xml_path}")
                
                # Save XML to library for future use
                if self.library_agent:
                    self.library_agent.save_xml_to_library(file_path, xml_path, user_id)
                
                # Parse XML to JSON
                print("Parsing MusicXML to JSON format...")
                parsed_data = parse_musicxml_to_json(xml_path)
                
                if parsed_data.get("status") == "success":
                    # Remove status field and return data
                    extracted_data = {k: v for k, v in parsed_data.items() if k != "status"}
                    
                    # Validate and process the extracted data
                    if self.enable_tools:
                        validation_result = validate_music_data(extracted_data)
                        if not validation_result.get('valid'):
                            print(f"Warning: Validation found issues: {validation_result.get('errors', [])}")
                        else:
                            print("✓ Extraction structure validated successfully")
                        
                        # Search for sample music if piece name is available
                        piece_name = extracted_data.get('piece_name', '')
                        composer = extracted_data.get('composer', '')
                        if piece_name:
                            print(f"\n🔍 Searching for sample music: {piece_name}")
                            try:
                                search_results = search_sample_music(piece_name, composer)
                                if search_results.get('status') == 'success':
                                    extracted_data['sample_music_search'] = search_results
                            except Exception as e:
                                print(f"   ⚠️  Error searching for sample music: {e}")
                    
                    # Store extraction pattern in memory
                    # Memory service integration removed
                    
                    return extracted_data
                else:
                    print(f"Warning: Failed to parse XML: {parsed_data.get('error_message')}")
                    print("Falling back to image extraction...")
            else:
                print(f"Warning: homr conversion failed: {homr_result.get('error_message')}")
                print("Falling back to image extraction...")
        
        # Step 3: Fall back to original image-based extraction
        print("Using image-based extraction (Gemini vision model)...")
        
        # Load the file
        try:
            with open(file_path, "rb") as f:
                file_content = f.read()
        except FileNotFoundError:
            print(f"Error: File not found at {file_path}")
            return None

        # Determine mime type
        mime_type = "image/jpeg" # Default
        if file_path.lower().endswith(".png"):
            mime_type = "image/png"
        elif file_path.lower().endswith(".pdf"):
            mime_type = "application/pdf"
        
        # Load memory context
        memory_context = self._load_extraction_memory()
        preferences_context = self._get_user_preferences_context()
        
        # Create the prompt with memory context
        prompt = f"""
        Analyze this music sheet (piano/grand staff). Extract the information in JSON format:
        1. "piece_name": The name/title of the piece (e.g., "Prelude in C Major", "Moonlight Sonata"). Extract from the sheet if visible.
        2. "composer": The composer's name if visible on the sheet (e.g., "Bach", "Beethoven", "Chopin").
        3. "key": Key signature (e.g., "C Major").
        4. "tempo": Tempo indication (e.g., "120"), or null.
        5. "measures": A list of measures. Each measure has:
            - "id": Measure number.
            - "right_hand": List of events. Each event has:
                - "notes": List of pitches (e.g., ["C4", "E4"]). Use ["Rest"] for rests.
                - "duration": Duration (e.g., "quarter", "half").
            - "left_hand": List of events (same structure as right_hand).
        
        Example:
        {{
            "piece_name": "Prelude in C Major",
            "composer": "Bach",
            "key": "C Major",
            "tempo": "120",
            "measures": [
                {{
                    "id": 1,
                    "right_hand": [
                        {{"notes": ["C4", "E4"], "duration": "quarter"}},
                        {{"notes": ["G4"], "duration": "quarter"}}
                    ],
                    "left_hand": [
                        {{"notes": ["C3"], "duration": "half"}}
                    ]
                }}
            ]
        }}
        {memory_context}
        {preferences_context}
        Return ONLY the JSON.
        """

        # Generate content using the model directly
        try:
            from google import generativeai as genai
            import os
            
            # Configure API key if available
            api_key = os.getenv("GOOGLE_API_KEY")
            if api_key:
                genai.configure(api_key=api_key)
            
            # Get the model name from agent config
            model_name = self.model if hasattr(self, 'model') else "gemini-2.5-flash-lite"
            
            # Get the model
            model = genai.GenerativeModel(model_name=model_name)
            
            # Create content parts - for PDFs, we need to use upload_file or handle differently
            if mime_type == "application/pdf":
                # For PDFs, upload the file first
                uploaded_file = genai.upload_file(
                    path=file_path,
                    mime_type=mime_type
                )
                content_parts = [prompt, uploaded_file]
            else:
                # For images, use inline data
                import base64
                content_parts = [
                    prompt,
                    {
                        "mime_type": mime_type,
                        "data": base64.b64encode(file_content).decode('utf-8')
                    }
                ]
            
            # Generate content
            response = model.generate_content(
                content_parts,
                generation_config={"response_mime_type": "application/json"}
            )
            
            json_text = response.text
            # Clean up potential markdown code blocks
            if json_text.startswith("```json"):
                json_text = json_text[7:-3]
            elif json_text.startswith("```"):
                json_text = json_text[3:-3]
                
            extracted_data = json.loads(json_text)
            
            # Extract piece name and composer for searching
            piece_name = extracted_data.get('piece_name', '')
            composer = extracted_data.get('composer', '')
            
            # Use tools to validate and improve extraction (if enabled)
            if self.enable_tools:
                # Validate the extracted data structure
                validation_result = validate_music_data(extracted_data)
                if not validation_result.get('valid'):
                    print(f"Warning: Validation found issues: {validation_result.get('errors', [])}")
                else:
                    print("✓ Extraction structure validated successfully")
                
                # Validate measure durations
                measure_validation = validate_all_measures(extracted_data)
                if measure_validation.get('status') == 'success':
                    if measure_validation.get('all_valid'):
                        print(f"✓ All {measure_validation.get('total_measures', 0)} measures have correct durations")
                    else:
                        invalid = measure_validation.get('invalid_measures', 0)
                        total = measure_validation.get('total_measures', 0)
                        print(f"⚠️  {invalid}/{total} measures have incorrect durations")
                        
                        # Show details for invalid measures
                        for result in measure_validation.get('measure_results', []):
                            if not result.get('both_valid'):
                                m_id = result.get('measure_id', '?')
                                rh_err = result.get('right_hand_error', 0)
                                lh_err = result.get('left_hand_error', 0)
                                if rh_err > 0.01:
                                    print(f"   Measure {m_id}: Right hand off by {rh_err:.3f} beats")
                                if lh_err > 0.01:
                                    print(f"   Measure {m_id}: Left hand off by {lh_err:.3f} beats")
                
                # Get user preferences for suggestions
                if self.library_agent and user_id:
                    preferences = self.library_agent.get_user_preferences(user_id)
                    suggestions = suggest_corrections(extracted_data, preferences)
                    if suggestions.get('has_suggestions'):
                        print(f"Suggestions available: {list(suggestions.get('suggestions', {}).keys())}")
                
                # Search for sample music if piece name is available
                if piece_name:
                    print(f"\n🔍 Searching for sample music: {piece_name}")
                    if composer:
                        print(f"   Composer: {composer}")
                    
                    try:
                        search_results = search_sample_music(piece_name, composer)
                        if search_results.get('status') == 'success':
                            extracted_data['sample_music_search'] = search_results
                            
                            # Print search results
                            results = search_results.get('results', [])
                            if results:
                                print(f"   ✓ Found {len(results)} results:")
                                for i, result in enumerate(results[:3], 1):  # Show top 3
                                    title = result.get('title', result.get('raw_result', 'Result'))
                                    url = result.get('url', result.get('search_url', ''))
                                    if url:
                                        print(f"      {i}. {title}")
                                        print(f"         {url}")
                                    else:
                                        print(f"      {i}. {title}")
                            else:
                                search_url = search_results.get('search_url', '')
                                if search_url:
                                    print(f"   → Manual search: {search_url}")
                        else:
                            print(f"   ⚠️  Search failed: {search_results.get('error_message', 'Unknown error')}")
                    except Exception as e:
                        print(f"   ⚠️  Error searching for sample music: {e}")
                else:
                    print("   ⚠️  Piece name not found, skipping sample music search")
            
            return extracted_data

        except Exception as e:
            print(f"Error during extraction: {e}")
            return None
    
    def _store_extraction_pattern(self, file_path: str, extracted_data: Dict[str, Any], user_id: str):
        """Store extraction pattern in memory for future learning."""
        pass
    
    def learn_from_correction(self, original_data: Dict[str, Any], corrected_data: Dict[str, Any], user_id: str):
        """Learn from user corrections to improve future extractions."""
        pass
