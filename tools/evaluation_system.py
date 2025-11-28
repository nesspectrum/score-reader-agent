"""
Human-in-the-Loop Evaluation System for Music Sheet Extraction
Collects user feedback and preferences to improve agent performance
"""

import os
import json
import time
from typing import Dict, Any, List, Optional
from datetime import datetime

class EvaluationSystem:
    def __init__(self, library_agent=None, evaluation_dir="evaluations"):
        self.library_agent = library_agent
        self.evaluation_dir = evaluation_dir
        
        if not os.path.exists(self.evaluation_dir):
            os.makedirs(self.evaluation_dir)
        
        self.evaluation_file = os.path.join(self.evaluation_dir, "evaluations.json")
        self.evaluations = self._load_evaluations()
    
    def _load_evaluations(self) -> List[Dict[str, Any]]:
        """Load past evaluations from disk."""
        if os.path.exists(self.evaluation_file):
            try:
                with open(self.evaluation_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Could not load evaluations: {e}")
        return []
    
    def _save_evaluations(self):
        """Save evaluations to disk."""
        try:
            with open(self.evaluation_file, "w") as f:
                json.dump(self.evaluations, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save evaluations: {e}")
    
    def create_evaluation_dataset(self) -> Dict[str, Any]:
        """
        Create an evaluation dataset with test cases.
        
        Returns:
            Dictionary containing test scenarios
        """
        return {
            "test_cases": [
                {
                    "id": "test_001",
                    "file_path": None,  # User provides
                    "description": "Basic piano sheet with clear notation",
                    "expected_key": None,  # User provides
                    "expected_tempo": None,  # User provides
                    "difficulty": "easy"
                },
                {
                    "id": "test_002",
                    "file_path": None,
                    "description": "Complex polyphonic piece with multiple voices",
                    "expected_key": None,
                    "expected_tempo": None,
                    "difficulty": "hard"
                },
                {
                    "id": "test_003",
                    "file_path": None,
                    "description": "Sheet with ambiguous tempo markings",
                    "expected_key": None,
                    "expected_tempo": None,
                    "difficulty": "medium"
                }
            ],
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "version": "1.0"
            }
        }
    
    def evaluate_extraction(
        self,
        file_path: str,
        extracted_data: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Conduct human-in-the-loop evaluation of extraction results.
        
        Args:
            file_path: Path to the music sheet file
            extracted_data: Data extracted by the agent
            user_id: Optional user identifier
            
        Returns:
            Evaluation results dictionary
        """
        print("\n" + "=" * 80)
        print("HUMAN-IN-THE-LOOP EVALUATION")
        print("=" * 80)
        
        print(f"\nFile: {os.path.basename(file_path)}")
        print(f"Extracted Key: {extracted_data.get('key', 'N/A')}")
        print(f"Extracted Tempo: {extracted_data.get('tempo', 'N/A')}")
        print(f"Number of Measures: {len(extracted_data.get('measures', []))}")
        
        # Collect user feedback
        print("\n--- Accuracy Assessment ---")
        key_accuracy = self._rate_accuracy("Key signature", extracted_data.get('key'))
        tempo_accuracy = self._rate_accuracy("Tempo", extracted_data.get('tempo'))
        notes_accuracy = self._rate_accuracy("Notes extraction", "overall")
        
        # Collect corrections
        print("\n--- Corrections ---")
        corrections = self._collect_corrections(extracted_data)
        
        # Collect preferences
        print("\n--- Preference Collection ---")
        preferences = self._collect_preferences(user_id)
        
        # Overall rating
        overall_rating = input("\nOverall extraction quality (1-5, 5=excellent): ").strip()
        try:
            overall_rating = int(overall_rating)
        except ValueError:
            overall_rating = 3
        
        # Create evaluation record
        evaluation = {
            "id": f"eval_{int(time.time())}",
            "timestamp": datetime.now().isoformat(),
            "file_path": file_path,
            "user_id": user_id,
            "extracted_data": extracted_data,
            "corrections": corrections,
            "ratings": {
                "key_accuracy": key_accuracy,
                "tempo_accuracy": tempo_accuracy,
                "notes_accuracy": notes_accuracy,
                "overall": overall_rating
            },
            "preferences": preferences,
            "feedback": input("\nAdditional feedback (optional): ").strip() or None
        }
        
        # Store evaluation
        self.evaluations.append(evaluation)
        self._save_evaluations()
        
        # Store in memory service
        # Memory service integration removed
        
        # Update library agent with preferences
        if self.library_agent and preferences:
            self._update_preferences_from_evaluation(preferences, user_id)
        
        print("\n✓ Evaluation saved!")
        return evaluation
    
    def _rate_accuracy(self, aspect: str, value: Any) -> int:
        """Rate the accuracy of a specific aspect."""
        print(f"{aspect}: {value}")
        rating = input(f"  Accuracy (1-5, 5=perfect): ").strip()
        try:
            return int(rating)
        except ValueError:
            return 3
    
    def _collect_corrections(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """Collect corrections from the user."""
        corrections = {}
        
        correct_key = input(f"Correct key (current: {extracted_data.get('key', 'N/A')}, or press Enter): ").strip()
        if correct_key:
            corrections['key'] = correct_key
        
        correct_tempo = input(f"Correct tempo (current: {extracted_data.get('tempo', 'N/A')}, or press Enter): ").strip()
        if correct_tempo:
            corrections['tempo'] = correct_tempo
        
        return corrections
    
    def _collect_preferences(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Collect user preferences during evaluation."""
        preferences = {}
        
        print("Collecting preferences for future extractions...")
        
        # Tempo preference
        tempo_pref = input("Preferred default tempo (BPM, or press Enter to skip): ").strip()
        if tempo_pref:
            try:
                preferences['default_tempo'] = int(tempo_pref)
            except ValueError:
                pass
        
        # Hand preference
        hand_pref = input("Preferred hand (left/right/both, or press Enter to skip): ").strip().lower()
        if hand_pref in ['left', 'right', 'both']:
            preferences['preferred_hand'] = hand_pref
        
        # Extraction style preference
        style_pref = input("Prefer detailed or simplified extraction? (detailed/simplified, or press Enter): ").strip().lower()
        if style_pref in ['detailed', 'simplified']:
            preferences['extraction_style'] = style_pref
        
        return preferences
    
    def _store_evaluation_in_memory(self, evaluation: Dict[str, Any]):
        """Store evaluation results in memory service."""
        pass
    
    def _update_preferences_from_evaluation(self, preferences: Dict[str, Any], user_id: Optional[str]):
        """Update library agent with preferences from evaluation."""
        if not self.library_agent:
            return
        
        for pref_type, value in preferences.items():
            if pref_type == 'default_tempo':
                self.library_agent.update_preference('tempo', value, user_id)
            elif pref_type == 'preferred_hand':
                self.library_agent.update_preference('hand', value, user_id)
    
    def get_evaluation_summary(self) -> Dict[str, Any]:
        """Get summary statistics from all evaluations."""
        if not self.evaluations:
            return {
                "total_evaluations": 0,
                "average_ratings": {},
                "common_corrections": {}
            }
        
        total = len(self.evaluations)
        avg_overall = sum(e.get('ratings', {}).get('overall', 3) for e in self.evaluations) / total
        avg_key = sum(e.get('ratings', {}).get('key_accuracy', 3) for e in self.evaluations) / total
        avg_tempo = sum(e.get('ratings', {}).get('tempo_accuracy', 3) for e in self.evaluations) / total
        avg_notes = sum(e.get('ratings', {}).get('notes_accuracy', 3) for e in self.evaluations) / total
        
        # Count common corrections
        key_corrections = {}
        tempo_corrections = {}
        for eval in self.evaluations:
            corrections = eval.get('corrections', {})
            if corrections.get('key'):
                key_corrections[corrections['key']] = key_corrections.get(corrections['key'], 0) + 1
            if corrections.get('tempo'):
                tempo_corrections[corrections['tempo']] = tempo_corrections.get(corrections['tempo'], 0) + 1
        
        return {
            "total_evaluations": total,
            "average_ratings": {
                "overall": round(avg_overall, 2),
                "key_accuracy": round(avg_key, 2),
                "tempo_accuracy": round(avg_tempo, 2),
                "notes_accuracy": round(avg_notes, 2)
            },
            "common_corrections": {
                "keys": dict(sorted(key_corrections.items(), key=lambda x: x[1], reverse=True)[:5]),
                "tempos": dict(sorted(tempo_corrections.items(), key=lambda x: x[1], reverse=True)[:5])
            }
        }
    
    def print_evaluation_summary(self):
        """Print a summary of evaluation results."""
        summary = self.get_evaluation_summary()
        
        print("\n" + "=" * 80)
        print("EVALUATION SUMMARY")
        print("=" * 80)
        print(f"Total Evaluations: {summary['total_evaluations']}")
        print(f"\nAverage Ratings:")
        for aspect, rating in summary['average_ratings'].items():
            print(f"  {aspect.replace('_', ' ').title()}: {rating}/5")
        
        if summary['common_corrections']['keys'] or summary['common_corrections']['tempos']:
            print(f"\nCommon Corrections:")
            if summary['common_corrections']['keys']:
                print("  Keys:")
                for key, count in summary['common_corrections']['keys'].items():
                    print(f"    {key}: {count} times")
            if summary['common_corrections']['tempos']:
                print("  Tempos:")
                for tempo, count in summary['common_corrections']['tempos'].items():
                    print(f"    {tempo}: {count} times")
        print("=" * 80)
    
    def evaluate_with_golden_data(
        self,
        test_id: str,
        extracted_data: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Evaluate extraction against golden data.
        
        Args:
            test_id: Test case identifier
            extracted_data: Data extracted by the agent
            user_id: Optional user identifier
            
        Returns:
            Evaluation results with comparison metrics
        """
        try:
            from tools.golden_data_manager import GoldenDataManager
            golden_manager = GoldenDataManager()
            
            golden_data = golden_manager.get_golden_data(test_id)
            if not golden_data:
                return {
                    "status": "error",
                    "error_message": f"No golden data found for test case {test_id}"
                }
            
            # Compare extracted vs golden
            comparison = golden_manager.compare_extracted_vs_golden(test_id)
            
            # Create evaluation record
            evaluation = {
                "id": f"eval_{int(time.time())}",
                "timestamp": datetime.now().isoformat(),
                "test_id": test_id,
                "user_id": user_id,
                "extracted_data": extracted_data,
                "golden_data": golden_data,
                "comparison": comparison,
                "ratings": {
                    "key_accuracy": 5 if comparison.get("key_match") else 1,
                    "tempo_accuracy": 5 if comparison.get("tempo_match") else 1,
                    "notes_accuracy": int(comparison.get("accuracy_score", 0) * 5),
                    "overall": int(comparison.get("accuracy_score", 0) * 5)
                }
            }
            
            # Store evaluation
            self.evaluations.append(evaluation)
            self._save_evaluations()
            
            # Memory service integration removed
            
            return evaluation
            
        except Exception as e:
            return {
                "status": "error",
                "error_message": str(e)
            }

