#!/usr/bin/env python3
"""
Test script for measure validation tool
"""

import json
from tools.measure_validator import validate_measure, validate_all_measures

# Test with actual extracted data format
test_measure = {
    "id": 1,
    "right_hand": [
        {"notes": ["C5"], "duration": "eighth"},
        {"notes": ["E5"], "duration": "eighth"},
        {"notes": ["G5"], "duration": "eighth"},
        {"notes": ["C6"], "duration": "eighth"},
        {"notes": ["B5"], "duration": "eighth"},
        {"notes": ["G5"], "duration": "eighth"},
        {"notes": ["E5"], "duration": "eighth"},
        {"notes": ["C5"], "duration": "eighth"}
    ],
    "left_hand": [
        {"notes": ["C3"], "duration": "quarter"},
        {"notes": ["Rest"], "duration": "quarter"},
        {"notes": ["C3"], "duration": "quarter"},
        {"notes": ["Rest"], "duration": "quarter"}
    ]
}

# Test validation
print("Testing single measure validation:")
result = validate_measure(test_measure)
print(json.dumps(result, indent=2))

# Test with full music data
test_music_data = {
    "piece_name": "Test Piece",
    "key": "C Major",
    "tempo": "120",
    "time_signature": {"numerator": 4, "denominator": 4},
    "measures": [test_measure]
}

print("\n\nTesting full music data validation:")
full_result = validate_all_measures(test_music_data)
print(json.dumps(full_result, indent=2))

