#!/usr/bin/env python3
"""
Test validation with different time signatures
"""

import json
from tools.measure_validator import validate_measure, validate_all_measures

# Test with 3/4 time signature
test_34_measure = {
    "id": 1,
    "time_signature": {"numerator": 3, "denominator": 4},
    "right_hand": [
        {"notes": ["C4"], "duration": "quarter"},
        {"notes": ["D4"], "duration": "quarter"},
        {"notes": ["E4"], "duration": "quarter"}
    ],
    "left_hand": [
        {"notes": ["C3"], "duration": "half"},
        {"notes": ["G2"], "duration": "quarter"}
    ]
}

# Test with 2/4 time signature
test_24_measure = {
    "id": 2,
    "time_signature": "2/4",
    "right_hand": [
        {"notes": ["C4"], "duration": "quarter"},
        {"notes": ["D4"], "duration": "quarter"}
    ],
    "left_hand": [
        {"notes": ["C3"], "duration": "half"}
    ]
}

# Test with 6/8 time signature
test_68_measure = {
    "id": 3,
    "time_signature": {"numerator": 6, "denominator": 8},
    "right_hand": [
        {"notes": ["C4"], "duration": "eighth"},
        {"notes": ["D4"], "duration": "eighth"},
        {"notes": ["E4"], "duration": "eighth"},
        {"notes": ["F4"], "duration": "eighth"},
        {"notes": ["G4"], "duration": "eighth"},
        {"notes": ["A4"], "duration": "eighth"}
    ],
    "left_hand": [
        {"notes": ["C3"], "duration": "quarter"},
        {"notes": ["G2"], "duration": "quarter"}
    ]
}

print("Testing 3/4 time signature measure:")
print("="*70)
result1 = validate_measure(test_34_measure)
print(json.dumps(result1, indent=2))
print(f"Valid: {result1['both_valid']} (Expected: 3 beats)")

print("\n\nTesting 2/4 time signature measure:")
print("="*70)
result2 = validate_measure(test_24_measure)
print(json.dumps(result2, indent=2))
print(f"Valid: {result2['both_valid']} (Expected: 2 beats)")

print("\n\nTesting 6/8 time signature measure:")
print("="*70)
result3 = validate_measure(test_68_measure)
print(json.dumps(result3, indent=2))
print(f"Valid: {result3['both_valid']} (Expected: 6/8 = 3 beats)")

# Test with time signature changes mid-piece
test_music_data = {
    "piece_name": "Test Piece with Time Signature Changes",
    "key": "C Major",
    "tempo": "120",
    "time_signature": {"numerator": 4, "denominator": 4},  # Global default
    "measures": [
        {
            "id": 1,
            "time_signature": {"numerator": 4, "denominator": 4},  # Explicit 4/4
            "right_hand": [
                {"notes": ["C4"], "duration": "quarter"},
                {"notes": ["D4"], "duration": "quarter"},
                {"notes": ["E4"], "duration": "quarter"},
                {"notes": ["F4"], "duration": "quarter"}
            ],
            "left_hand": [
                {"notes": ["C3"], "duration": "half"},
                {"notes": ["G2"], "duration": "half"}
            ]
        },
        {
            "id": 2,
            "time_signature": "3/4",  # Changes to 3/4
            "right_hand": [
                {"notes": ["C4"], "duration": "quarter"},
                {"notes": ["D4"], "duration": "quarter"},
                {"notes": ["E4"], "duration": "quarter"}
            ],
            "left_hand": [
                {"notes": ["C3"], "duration": "half"},
                {"notes": ["G2"], "duration": "quarter"}
            ]
        },
        {
            "id": 3,
            # No time signature - uses previous (3/4)
            "right_hand": [
                {"notes": ["C4"], "duration": "quarter"},
                {"notes": ["D4"], "duration": "quarter"},
                {"notes": ["E4"], "duration": "quarter"}
            ],
            "left_hand": [
                {"notes": ["C3"], "duration": "half"},
                {"notes": ["G2"], "duration": "quarter"}
            ]
        },
        {
            "id": 4,
            "time_signature": {"numerator": 2, "denominator": 4},  # Changes to 2/4
            "right_hand": [
                {"notes": ["C4"], "duration": "quarter"},
                {"notes": ["D4"], "duration": "quarter"}
            ],
            "left_hand": [
                {"notes": ["C3"], "duration": "half"}
            ]
        }
    ]
}

print("\n\nTesting piece with time signature changes:")
print("="*70)
full_result = validate_all_measures(test_music_data)
print(f"Status: {full_result.get('status')}")
print(f"All Valid: {full_result.get('all_valid')}")
print(f"Valid Measures: {full_result.get('valid_measures')}/{full_result.get('total_measures')}")
print(f"\nMeasure Results:")
for r in full_result.get('measure_results', []):
    print(f"  Measure {r.get('measure_id')}: Valid={r.get('both_valid')}, "
          f"Time Signature={r.get('time_signature')}, "
          f"RH={r.get('right_hand_duration')}, LH={r.get('left_hand_duration')}")

