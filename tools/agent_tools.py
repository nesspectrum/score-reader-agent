"""
Agent Tools - Wrappers for tools to be used as FunctionTools in ADK agents
"""

from typing import Dict, Any, Optional, List
import json

# Import tool classes
from .audio_tool import AudioTool
from .correction_tool import CorrectionTool
from .evaluation_system import EvaluationSystem


# ============================================================================
# Audio Tool Functions
# ============================================================================

def get_note_frequency(pitch: str) -> Dict[str, Any]:
    """
    Get the frequency of a musical note.
    
    Args:
        pitch: Note name (e.g., "C4", "A4", "Rest")
        
    Returns:
        Dictionary with frequency in Hz or status
    """
    try:
        audio_tool = AudioTool()
        freq = audio_tool.get_freq(pitch)
        
        if freq == 0 and pitch != "Rest":
            return {
                "status": "error",
                "error_message": f"Unknown pitch: {pitch}"
            }
        
        return {
            "status": "success",
            "pitch": pitch,
            "frequency_hz": freq
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": str(e)
        }


def generate_tone(frequency_hz: float, duration_sec: float) -> Dict[str, Any]:
    """
    Generate a tone at a specific frequency and duration.
    
    Args:
        frequency_hz: Frequency in Hz
        duration_sec: Duration in seconds
        
    Returns:
        Dictionary with status and audio data info
    """
    try:
        audio_tool = AudioTool()
        tone = audio_tool.generate_tone(frequency_hz, duration_sec)
        
        return {
            "status": "success",
            "frequency_hz": frequency_hz,
            "duration_sec": duration_sec,
            "samples": len(tone),
            "sample_rate": audio_tool.sample_rate,
            "message": f"Generated {len(tone)} samples at {audio_tool.sample_rate}Hz"
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": str(e)
        }


def validate_music_data(music_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate extracted music data structure.
    
    Args:
        music_data: Dictionary containing music data
        
    Returns:
        Dictionary with validation results
    """
    try:
        errors = []
        warnings = []
        
        # Check required fields
        if 'measures' not in music_data and 'notes' not in music_data:
            errors.append("Missing 'measures' or 'notes' field")
        
        # Validate measures structure
        if 'measures' in music_data:
            measures = music_data['measures']
            if not isinstance(measures, list):
                errors.append("'measures' must be a list")
            else:
                for i, measure in enumerate(measures):
                    if not isinstance(measure, dict):
                        errors.append(f"Measure {i} is not a dictionary")
                        continue
                    
                    if 'id' not in measure:
                        warnings.append(f"Measure {i} missing 'id' field")
                    
                    for hand in ['right_hand', 'left_hand']:
                        if hand in measure:
                            events = measure[hand]
                            if not isinstance(events, list):
                                errors.append(f"Measure {i} {hand} is not a list")
                            else:
                                for j, event in enumerate(events):
                                    if not isinstance(event, dict):
                                        errors.append(f"Measure {i} {hand} event {j} is not a dictionary")
                                    else:
                                        if 'notes' not in event:
                                            warnings.append(f"Measure {i} {hand} event {j} missing 'notes'")
                                        if 'duration' not in event:
                                            warnings.append(f"Measure {i} {hand} event {j} missing 'duration'")
        
        # Check key and tempo
        if 'key' not in music_data:
            warnings.append("Missing 'key' field")
        
        if 'tempo' not in music_data:
            warnings.append("Missing 'tempo' field")
        
        return {
            "status": "success" if not errors else "error",
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "measure_count": len(music_data.get('measures', [])),
            "has_key": 'key' in music_data,
            "has_tempo": 'tempo' in music_data
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": str(e)
        }


def get_music_statistics(music_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate statistics about extracted music data.
    
    Args:
        music_data: Dictionary containing music data
        
    Returns:
        Dictionary with statistics
    """
    try:
        stats = {
            "key": music_data.get('key', 'Unknown'),
            "tempo": music_data.get('tempo', 'Unknown'),
            "measure_count": len(music_data.get('measures', [])),
            "total_events": 0,
            "right_hand_events": 0,
            "left_hand_events": 0,
            "unique_pitches": set(),
            "duration_types": {}
        }
        
        measures = music_data.get('measures', [])
        for measure in measures:
            for hand in ['right_hand', 'left_hand']:
                events = measure.get(hand, [])
                if hand == 'right_hand':
                    stats['right_hand_events'] += len(events)
                else:
                    stats['left_hand_events'] += len(events)
                
                stats['total_events'] += len(events)
                
                for event in events:
                    notes = event.get('notes', [])
                    for note in notes:
                        if note != "Rest":
                            stats['unique_pitches'].add(note)
                    
                    duration = event.get('duration', 'unknown')
                    stats['duration_types'][duration] = stats['duration_types'].get(duration, 0) + 1
        
        stats['unique_pitches'] = sorted(list(stats['unique_pitches']))
        stats['unique_pitch_count'] = len(stats['unique_pitches'])
        
        return {
            "status": "success",
            "statistics": stats
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": str(e)
        }


# ============================================================================
# Correction Tool Functions (for agent use)
# ============================================================================

def suggest_corrections(music_data: Dict[str, Any], user_preferences: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Suggest corrections based on common patterns and user preferences.
    This is a non-interactive version for agent use.
    
    Args:
        music_data: Extracted music data
        user_preferences: Optional user preferences dictionary
        
    Returns:
        Dictionary with suggested corrections
    """
    try:
        suggestions = {}
        
        # Suggest tempo if missing and user has preference
        if not music_data.get('tempo') and user_preferences:
            if user_preferences.get('default_tempo'):
                suggestions['tempo'] = {
                    "suggested_value": user_preferences['default_tempo'],
                    "reason": "User preference"
                }
        
        # Validate key format
        key = music_data.get('key', '')
        if key and not any(word in key.lower() for word in ['major', 'minor', 'key']):
            suggestions['key'] = {
                "current": key,
                "suggestion": f"{key} Major" if key else "C Major",
                "reason": "Key format may be incomplete"
            }
        
        # Check for empty measures
        measures = music_data.get('measures', [])
        empty_measures = []
        for measure in measures:
            right_empty = len(measure.get('right_hand', [])) == 0
            left_empty = len(measure.get('left_hand', [])) == 0
            if right_empty and left_empty:
                empty_measures.append(measure.get('id', 'unknown'))
        
        if empty_measures:
            suggestions['empty_measures'] = {
                "measure_ids": empty_measures,
                "reason": "These measures have no notes"
            }
        
        return {
            "status": "success",
            "suggestions": suggestions,
            "has_suggestions": len(suggestions) > 0
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": str(e)
        }


# ============================================================================
# Library/Preference Functions
# ============================================================================

def get_user_preferences(user_id: str, library_agent=None) -> Dict[str, Any]:
    """
    Get user preferences from library agent.
    
    Args:
        user_id: User identifier
        library_agent: LibraryAgent instance (optional)
        
    Returns:
        Dictionary with user preferences
    """
    try:
        if not library_agent:
            return {
                "status": "error",
                "error_message": "Library agent not provided"
            }
        
        preferences = library_agent.get_user_preferences(user_id)
        return {
            "status": "success",
            "user_id": user_id,
            "preferences": preferences
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": str(e)
        }


def upload_music_sheet_to_library(file_path: str, user_id: str = "default_user", library_agent=None) -> Dict[str, Any]:
    """
    Upload a music sheet (PDF or image) to the library for processing and storage.
    
    Args:
        file_path: Path to the music sheet file (PDF or image)
        user_id: User identifier
        library_agent: LibraryAgent instance (optional)
        
    Returns:
        Dictionary with upload status and processing information
    """
    try:
        if not library_agent:
            return {
                "status": "error",
                "error_message": "Library agent not provided. Cannot upload to library."
            }
        
        import os
        if not os.path.exists(file_path):
            return {
                "status": "error",
                "error_message": f"File not found: {file_path}"
            }
        
        # Check if file is already in library
        cached_data = library_agent.get_cached_data(file_path)
        if cached_data:
            return {
                "status": "success",
                "message": "File already exists in library",
                "file_path": file_path,
                "cached": True,
                "data": cached_data
            }
        
        # File needs to be processed - return instructions
        return {
            "status": "pending",
            "message": "File uploaded to library. Use convert_image_to_musicxml_tool to process it.",
            "file_path": file_path,
            "cached": False,
            "next_step": "Process the file using convert_image_to_musicxml_tool, then save the result to library"
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": str(e)
        }


# ============================================================================
# Measure Validation Functions
# ============================================================================

def validate_measure_duration(measure: Dict[str, Any], time_signature: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Validate that a measure's duration matches the time signature.
    
    Args:
        measure: Measure dictionary with "id", "right_hand", "left_hand"
        time_signature: Optional time signature dict (default: 4/4)
    
    Returns:
        Dictionary with validation results
    """
    try:
        from tools.measure_validator import validate_measure
        
        if time_signature is None:
            time_signature = {"numerator": 4, "denominator": 4}
        
        result = validate_measure(measure, time_signature)
        
        return {
            "status": "success",
            "valid": result["both_valid"],
            "measure_id": result["measure_id"],
            "time_signature": result["time_signature"],
            "expected_duration": result["expected_duration"],
            "right_hand": {
                "duration": result["right_hand_duration"],
                "valid": result["right_hand_valid"],
                "error": result["right_hand_error"]
            },
            "left_hand": {
                "duration": result["left_hand_duration"],
                "valid": result["left_hand_valid"],
                "error": result["left_hand_error"]
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": str(e)
        }


def validate_all_measures(music_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate all measures in extracted music data.
    
    Args:
        music_data: Extracted music data with "measures" list
    
    Returns:
        Dictionary with validation results for all measures
    """
    try:
        from tools.measure_validator import validate_all_measures as validate_all
        
        result = validate_all(music_data)
        
        return result
    except Exception as e:
        return {
            "status": "error",
            "error_message": str(e)
        }


# ============================================================================
# HOMR Tool Functions
# ============================================================================

def convert_image_to_musicxml_tool(image_path: str, output_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    Convert a music sheet image to MusicXML format using homr.
    
    Args:
        image_path: Path to the input image file (PNG, JPG, etc.)
        output_dir: Optional directory for output XML file (defaults to same as input)
        
    Returns:
        Dictionary with status and path to generated XML file
    """
    from tools.homr_tool import convert_image_to_musicxml
    return convert_image_to_musicxml(image_path, output_dir)


# ============================================================================
# PDMX Datastore Functions
# ============================================================================

def setup_pdmx_vertex_search(
    project_id: str,
    location: str = "us-central1",
    data_store_id: str = "pdmx-musicxml",
    sample_size: Optional[int] = 1000
) -> Dict[str, Any]:
    """
    Setup Vertex AI Search datastore from PDMX dataset.
    
    Args:
        project_id: Google Cloud project ID
        location: GCP location (default: us-central1)
        data_store_id: ID for the datastore (default: pdmx-musicxml)
        sample_size: Number of documents to process (default: 1000, None for all)
        
    Returns:
        Dictionary with setup status and datastore information
    """
    from tools.pdmx_datastore import setup_pdmx_datastore
    return setup_pdmx_datastore(
        project_id=project_id,
        location=location,
        data_store_id=data_store_id,
        gcs_bucket=None,  # Will auto-create
        download_dir="./pdmx_data",
        sample_size=sample_size
    )


# ============================================================================
# Music Search Functions
# ============================================================================

def search_sample_music(piece_name: str, composer: Optional[str] = None) -> Dict[str, Any]:
    """
    Search for sample music/audio files for a given piece.
    
    Args:
        piece_name: Name of the music piece (e.g., "Prelude in C Major")
        composer: Optional composer name (e.g., "Bach")
        
    Returns:
        Dictionary with search results and links to sample music
    """
    try:
        # Build search query
        query_parts = [piece_name]
        if composer:
            query_parts.append(composer)
        query = " ".join(query_parts) + " piano sheet music audio sample midi"
        
        # Use Google Search tool if available
        # Note: google_search is typically used within agent context, so we provide
        # a search query that can be used manually or by the agent
        try:
            from google.adk.tools import google_search
            
            # Note: google_search tool is designed to be called by agents, not directly
            # We'll return a structured query that the agent can use
            results = {
                "status": "success",
                "piece_name": piece_name,
                "composer": composer,
                "query": query,
                "search_tool_available": True,
                "message": "Use google_search tool with this query to find sample music",
                "results": [],
                "search_url": f"https://www.google.com/search?q={query.replace(' ', '+')}",
                "suggested_sites": [
                    "https://imslp.org",
                    "https://musescore.com",
                    "https://www.pianostreet.com",
                    "https://www.free-scores.com"
                ]
            }
            
            return results
            
        except ImportError:
            # Fallback: return search query for manual search
            return {
                "status": "success",
                "piece_name": piece_name,
                "composer": composer,
                "query": query,
                "message": "Google Search tool not available. Use this query to search manually:",
                "search_url": f"https://www.google.com/search?q={query.replace(' ', '+')}",
                "suggested_sites": [
                    "https://imslp.org",
                    "https://musescore.com",
                    "https://www.pianostreet.com",
                    "https://www.free-scores.com"
                ]
            }
            
    except Exception as e:
        return {
            "status": "error",
            "error_message": str(e)
        }

