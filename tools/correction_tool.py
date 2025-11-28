import json
from typing import Optional, Dict, Any

class CorrectionTool:
    def __init__(self, library_agent=None, user_id: Optional[str] = None):
        self.library_agent = library_agent
        self.user_id = user_id
        self.original_data = None
    
    def review_and_correct(self, music_data, user_id: Optional[str] = None):
        """
        Presents the extracted data to the user and allows for corrections.
        Stores corrections in memory for learning.
        """
        if not music_data:
            return None

        self.original_data = json.loads(json.dumps(music_data))  # Deep copy
        self.user_id = user_id or self.user_id
        
        # Load user preferences to suggest defaults
        preferences = {}
        if self.library_agent:
            preferences = self.library_agent.get_user_preferences(user_id)
        
        print("\n--- Review Extracted Data ---")
        print(f"Key: {music_data.get('key')}")
        print(f"Tempo: {music_data.get('tempo')}")
        
        # Show measure count
        measures = music_data.get('measures', [])
        if measures:
            print(f"Number of measures: {len(measures)}")
        else:
            print(f"Number of notes: {len(music_data.get('notes', []))}")
        
        # Show user preferences if available
        if preferences.get('default_tempo') and not music_data.get('tempo'):
            print(f"\nSuggested tempo (from preferences): {preferences.get('default_tempo')}")
        
        # In a real app, we might show a GUI or a more complex CLI.
        # For now, we'll just ask if they want to proceed or edit raw JSON.
        
        choice = input("\nDo you want to (P)roceed, (E)dit JSON, or (Q)uick edit [key/tempo]? [P/e/q]: ").strip().lower()
        
        if choice == 'e':
            # Simple JSON editing via input (could be improved with opening an editor)
            print("\nCurrent JSON:")
            print(json.dumps(music_data, indent=2))
            print("\nPaste the corrected JSON below (one line) or press Enter to cancel editing:")
            new_json = input()
            if new_json.strip():
                try:
                    music_data = json.loads(new_json)
                    print("JSON updated.")
                    self._record_corrections(music_data)
                except json.JSONDecodeError:
                    print("Invalid JSON. Keeping original data.")
        
        elif choice == 'q':
            # Quick edit mode for common corrections
            music_data = self._quick_edit(music_data, preferences)
            self._record_corrections(music_data)
        
        return music_data
    
    def _quick_edit(self, music_data: Dict[str, Any], preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Quick edit mode for common corrections."""
        print("\n--- Quick Edit Mode ---")
        
        # Edit key
        current_key = music_data.get('key', '')
        new_key = input(f"Key signature [{current_key}]: ").strip()
        if new_key:
            music_data['key'] = new_key
        
        # Edit tempo
        current_tempo = music_data.get('tempo', '')
        suggested = preferences.get('default_tempo', '')
        prompt = f"Tempo [{current_key}]"
        if suggested:
            prompt += f" (suggested: {suggested})"
        prompt += ": "
        
        new_tempo = input(prompt).strip()
        if new_tempo:
            music_data['tempo'] = new_tempo
        elif suggested and not current_tempo:
            music_data['tempo'] = suggested
            print(f"Using suggested tempo: {suggested}")
        
        return music_data
    
    def _record_corrections(self, corrected_data: Dict[str, Any]):
        """Record corrections for learning."""
        if not self.original_data or not self.library_agent:
            return
        
        # Check if anything was corrected
        key_changed = self.original_data.get('key') != corrected_data.get('key')
        tempo_changed = self.original_data.get('tempo') != corrected_data.get('tempo')
        
        if key_changed or tempo_changed:
            self.library_agent.record_correction_pattern(
                self.original_data,
                corrected_data,
                self.user_id
            )
            print("Correction pattern recorded for future learning.")
