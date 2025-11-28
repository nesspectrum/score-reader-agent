"""
Golden Data Manager
Manages golden test datasets for evaluation
"""

import os
import json
import hashlib
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path


class GoldenDataManager:
    def __init__(self, golden_data_dir: str = "golden_data"):
        self.golden_data_dir = golden_data_dir
        self.test_cases_file = os.path.join(golden_data_dir, "test_cases.json")
        
        # Create directory if it doesn't exist
        os.makedirs(golden_data_dir, exist_ok=True)
        
        # Load test cases registry
        self.test_cases = self._load_test_cases()
    
    def _load_test_cases(self) -> List[Dict[str, Any]]:
        """Load test cases registry."""
        if os.path.exists(self.test_cases_file):
            try:
                with open(self.test_cases_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Could not load test cases: {e}")
        return []
    
    def _save_test_cases(self):
        """Save test cases registry."""
        try:
            with open(self.test_cases_file, 'w') as f:
                json.dump(self.test_cases, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save test cases: {e}")
    
    def create_test_case(
        self,
        test_id: str,
        source_file: str,
        extracted_data: Dict[str, Any],
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new test case from extracted data.
        
        Args:
            test_id: Unique test case identifier
            source_file: Path to source music sheet file
            extracted_data: Extracted music data
            description: Optional description
        
        Returns:
            Test case metadata
        """
        test_dir = os.path.join(self.golden_data_dir, test_id)
        os.makedirs(test_dir, exist_ok=True)
        
        # Save extracted data
        extracted_file = os.path.join(test_dir, "extracted.json")
        with open(extracted_file, 'w') as f:
            json.dump(extracted_data, f, indent=2)
        
        # Create metadata
        metadata = {
            "test_id": test_id,
            "source_file": source_file,
            "description": description or f"Test case {test_id}",
            "created_at": datetime.now().isoformat(),
            "extracted_file": extracted_file,
            "golden_file": None,
            "has_golden": False,
            "measures_count": len(extracted_data.get('measures', [])),
            "key": extracted_data.get('key'),
            "tempo": extracted_data.get('tempo'),
            "time_signature": extracted_data.get('time_signature')
        }
        
        metadata_file = os.path.join(test_dir, "metadata.json")
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Add to registry
        test_case_entry = {
            "test_id": test_id,
            "description": metadata["description"],
            "created_at": metadata["created_at"],
            "has_golden": False,
            "source_file": source_file
        }
        
        # Remove if exists, then add
        self.test_cases = [tc for tc in self.test_cases if tc["test_id"] != test_id]
        self.test_cases.append(test_case_entry)
        self._save_test_cases()
        
        return metadata
    
    def save_golden_data(
        self,
        test_id: str,
        golden_data: Dict[str, Any],
        corrections: Optional[Dict[str, Any]] = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Save golden (corrected) data for a test case.
        
        Args:
            test_id: Test case identifier
            golden_data: Corrected music data
            corrections: Dictionary of corrections made
            notes: Optional notes about corrections
        
        Returns:
            Updated metadata
        """
        test_dir = os.path.join(self.golden_data_dir, test_id)
        if not os.path.exists(test_dir):
            raise ValueError(f"Test case {test_id} does not exist")
        
        # Save golden data
        golden_file = os.path.join(test_dir, "golden.json")
        with open(golden_file, 'w') as f:
            json.dump(golden_data, f, indent=2)
        
        # Update metadata
        metadata_file = os.path.join(test_dir, "metadata.json")
        if os.path.exists(metadata_file):
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
        else:
            metadata = {"test_id": test_id}
        
        metadata.update({
            "golden_file": golden_file,
            "has_golden": True,
            "golden_created_at": datetime.now().isoformat(),
            "corrections": corrections or {},
            "notes": notes,
            "golden_measures_count": len(golden_data.get('measures', [])),
            "golden_key": golden_data.get('key'),
            "golden_tempo": golden_data.get('tempo')
        })
        
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Update registry
        for tc in self.test_cases:
            if tc["test_id"] == test_id:
                tc["has_golden"] = True
                break
        self._save_test_cases()
        
        return metadata
    
    def get_test_case(self, test_id: str) -> Optional[Dict[str, Any]]:
        """Get test case metadata."""
        test_dir = os.path.join(self.golden_data_dir, test_id)
        metadata_file = os.path.join(test_dir, "metadata.json")
        
        if not os.path.exists(metadata_file):
            return None
        
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        # Load extracted data
        if os.path.exists(metadata.get("extracted_file")):
            with open(metadata["extracted_file"], 'r') as f:
                metadata["extracted_data"] = json.load(f)
        
        # Load golden data if exists
        if metadata.get("has_golden") and os.path.exists(metadata.get("golden_file")):
            with open(metadata["golden_file"], 'r') as f:
                metadata["golden_data"] = json.load(f)
        
        return metadata
    
    def list_test_cases(self) -> List[Dict[str, Any]]:
        """List all test cases."""
        return self.test_cases.copy()
    
    def get_golden_data(self, test_id: str) -> Optional[Dict[str, Any]]:
        """Get golden data for a test case."""
        test_case = self.get_test_case(test_id)
        if test_case and test_case.get("has_golden"):
            return test_case.get("golden_data")
        return None
    
    def get_extracted_data(self, test_id: str) -> Optional[Dict[str, Any]]:
        """Get extracted data for a test case."""
        test_case = self.get_test_case(test_id)
        if test_case:
            return test_case.get("extracted_data")
        return None
    
    def compare_extracted_vs_golden(self, test_id: str) -> Dict[str, Any]:
        """
        Compare extracted data with golden data.
        
        Returns:
            Comparison metrics
        """
        test_case = self.get_test_case(test_id)
        if not test_case or not test_case.get("has_golden"):
            return {"error": "Golden data not available"}
        
        extracted = test_case.get("extracted_data", {})
        golden = test_case.get("golden_data", {})
        
        # Compare key fields
        metrics = {
            "key_match": extracted.get("key") == golden.get("key"),
            "tempo_match": extracted.get("tempo") == golden.get("tempo"),
            "composer_match": extracted.get("composer") == golden.get("composer"),
            "piece_name_match": extracted.get("piece_name") == golden.get("piece_name"),
            "measures_count_match": len(extracted.get("measures", [])) == len(golden.get("measures", [])),
            "extracted_measures": len(extracted.get("measures", [])),
            "golden_measures": len(golden.get("measures", []))
        }
        
        # Calculate accuracy score
        matches = sum([
            metrics["key_match"],
            metrics["tempo_match"],
            metrics["composer_match"],
            metrics["piece_name_match"],
            metrics["measures_count_match"]
        ])
        metrics["accuracy_score"] = matches / 5.0 if matches > 0 else 0.0
        
        return metrics

