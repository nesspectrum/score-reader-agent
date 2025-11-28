import os
import json
import hashlib
import time
from typing import Optional, Dict, Any

class LibraryManager:
    """
    Manages the music library file operations and user preferences.
    This class contains the core logic previously in LibraryAgent.
    """
    def __init__(self, library_dir="library"):
        self.library_dir = library_dir
        if not os.path.exists(self.library_dir):
            os.makedirs(self.library_dir)
        
        # User preferences storage
        self.preferences_file = os.path.join(self.library_dir, "user_preferences.json")
        self._load_preferences()

    def _calculate_hash(self, file_path):
        """Calculates SHA256 hash of the file."""
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                # Read in chunks to handle large files
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except FileNotFoundError:
            return None

    def get_cached_data(self, file_path):
        """
        Checks if the file has already been processed.
        Returns the cached data if found, otherwise None.
        """
        file_hash = self._calculate_hash(file_path)
        if not file_hash:
            return None
            
        cache_path = os.path.join(self.library_dir, f"{file_hash}.json")
        if os.path.exists(cache_path):
            try:
                with open(cache_path, "r") as f:
                    cached_record = json.load(f)
                    print(f"Found cached data for {os.path.basename(file_path)} (Hash: {file_hash[:8]}...)")
                    return cached_record.get("data")
            except Exception as e:
                print(f"Error reading cache: {e}")
                return None
        
        return None
    
    def get_cached_xml(self, file_path):
        """
        Checks if there's a corresponding MusicXML file in the library.
        Returns the path to the XML file if found, otherwise None.
        """
        file_hash = self._calculate_hash(file_path)
        if not file_hash:
            return None
        
        # Check for XML file with same hash
        xml_path = os.path.join(self.library_dir, f"{file_hash}.musicxml")
        if os.path.exists(xml_path):
            print(f"Found cached MusicXML for {os.path.basename(file_path)} (Hash: {file_hash[:8]}...)")
            return xml_path
        
        # Also check in the same directory as the input file
        input_dir = os.path.dirname(file_path)
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        xml_path = os.path.join(input_dir, f"{base_name}.musicxml")
        if os.path.exists(xml_path):
            print(f"Found MusicXML file: {xml_path}")
            return xml_path
        
        return None
    
    def save_xml_to_library(self, file_path, xml_path, user_id: Optional[str] = None):
        """
        Saves a MusicXML file to the library with the same hash as the source image.
        
        Args:
            file_path: Path to the original image file
            xml_path: Path to the MusicXML file to save
            user_id: Optional user identifier
        """
        file_hash = self._calculate_hash(file_path)
        if not file_hash:
            return False
        
        library_xml_path = os.path.join(self.library_dir, f"{file_hash}.musicxml")
        
        try:
            import shutil
            shutil.copy2(xml_path, library_xml_path)
            print(f"Saved MusicXML to library: {library_xml_path}")
            return True
        except Exception as e:
            print(f"Error saving XML to library: {e}")
            return False

    def _load_preferences(self):
        """Load user preferences from disk."""
        self.user_preferences = {
            "default_tempo": None,
            "preferred_hand": "both",
            "correction_patterns": [],
            "extraction_preferences": {}
        }
        
        if os.path.exists(self.preferences_file):
            try:
                with open(self.preferences_file, "r") as f:
                    self.user_preferences = json.load(f)
            except Exception as e:
                print(f"Warning: Could not load preferences: {e}")
    
    def _save_preferences(self):
        """Save user preferences to disk."""
        try:
            with open(self.preferences_file, "w") as f:
                json.dump(self.user_preferences, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save preferences: {e}")
    
    def get_user_preferences(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get user preferences."""
        preferences = self.user_preferences.copy()
        return preferences
    
    def update_preference(self, preference_type: str, value: Any, user_id: Optional[str] = None):
        """Update a user preference."""
        if preference_type == 'tempo':
            self.user_preferences['default_tempo'] = value
        elif preference_type == 'hand':
            self.user_preferences['preferred_hand'] = value
        
        self._save_preferences()
    
    def record_correction_pattern(self, original: Dict[str, Any], corrected: Dict[str, Any], user_id: Optional[str] = None):
        """Record a correction pattern to learn user preferences."""
        pattern = {
            "original_key": original.get('key'),
            "corrected_key": corrected.get('key'),
            "original_tempo": original.get('tempo'),
            "corrected_tempo": corrected.get('tempo'),
            "timestamp": time.time()
        }
        
        self.user_preferences['correction_patterns'].append(pattern)
        # Keep only last 50 patterns
        if len(self.user_preferences['correction_patterns']) > 50:
            self.user_preferences['correction_patterns'] = self.user_preferences['correction_patterns'][-50:]
        
        self._save_preferences()

    def save_to_library(self, file_path, data, user_id: Optional[str] = None):
        """
        Saves the extracted data to the library.
        """
        file_hash = self._calculate_hash(file_path)
        if not file_hash:
            return False
            
        cache_path = os.path.join(self.library_dir, f"{file_hash}.json")
        
        record = {
            "original_filename": os.path.basename(file_path),
            "timestamp": time.time(),
            "hash": file_hash,
            "data": data,
            "user_id": user_id
        }
        
        try:
            with open(cache_path, "w") as f:
                json.dump(record, f, indent=2)
            print(f"Saved to library: {cache_path}")
            return True
        except Exception as e:
            print(f"Error saving to library: {e}")
            return False
