#!/usr/bin/env python3
"""
Test validation with chords (multiple notes playing together)
"""

import json
from tools.measure_validator import validate_measure, validate_all_measures

# Test with chords (multiple notes in notes array)
test_chord_measure = {
    "id": 1,
    "right_hand": [
        {
            "notes": ["C4", "E4", "G4"],  # C major chord
            "duration": "quarter"
        },
        {
            "notes": ["F4", "A4", "C5"],  # F major chord
            "duration": "quarter"
        },
        {
            "notes": ["G4", "B4", "D5"],  # G major chord
            "duration": "quarter"
        },
        {
            "notes": ["C4", "E4", "G4"],  # C major chord
            "duration": "quarter"
        }
    ],
    "left_hand": [
        {
            "notes": ["C3"],  # Single bass note
            "duration": "half"
        },
        {
            "notes": ["G2"],  # Single bass note
            "duration": "half"
        }
    ]
}

print("Testing measure with chords:")
print("="*70)
result = validate_measure(test_chord_measure)
print(json.dumps(result, indent=2))

# Test with mixed single notes and chords
test_mixed_measure = {
    "id": 2,
    "right_hand": [
        {
            "notes": ["C4"],  # Single note
            "duration": "eighth"
        },
        {
            "notes": ["E4", "G4"],  # Two-note chord
            "duration": "eighth"
        },
        {
            "notes": ["C5", "E5", "G5", "C6"],  # Four-note chord
            "duration": "quarter"
        },
        {
            "notes": ["Rest"],  # Rest
            "duration": "eighth"
        },
        {
            "notes": ["G4", "B4", "D5"],  # Three-note chord
            "duration": "quarter"
        },
        {
            "notes": ["C5"],  # Single note
            "duration": "eighth"
        }
    ],
    "left_hand": [
        {
            "notes": ["C3", "E3"],  # Two-note chord in left hand
            "duration": "half"
        },
        {
            "notes": ["G2", "B2"],  # Two-note chord in left hand
            "duration": "half"
        }
    ]
}

print("\n\nTesting measure with mixed single notes and chords:")
print("="*70)
result2 = validate_measure(test_mixed_measure)
print(json.dumps(result2, indent=2))

# Test with full music data
test_music_data = {
    "piece_name": "Chord Test Piece",
    "key": "C Major",
    "tempo": "120",
    "time_signature": {"numerator": 4, "denominator": 4},
    "measures": [test_chord_measure, test_mixed_measure]
}

print("\n\nTesting full music data with chords:")
print("="*70)
full_result = validate_all_measures(test_music_data)
print(f"Status: {full_result.get('status')}")
print(f"All Valid: {full_result.get('all_valid')}")
print(f"Valid Measures: {full_result.get('valid_measures')}/{full_result.get('total_measures')}")

