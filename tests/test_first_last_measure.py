#!/usr/bin/env python3
"""
Test validation with first and last measure exceptions (incomplete measures)
"""

import json
from tools.measure_validator import validate_measure, validate_all_measures

# Test with incomplete first measure (anacrusis/pickup) - should sum to 1
test_first_measure = {
    "id": 1,
    "right_hand": [
        {"notes": ["C4"], "duration": "quarter"}  # Only 1 beat instead of 4
    ],
    "left_hand": [
        {"notes": ["C3"], "duration": "quarter"}  # Only 1 beat instead of 4
    ]
}

# Test with incomplete last measure - should sum to 1
test_last_measure = {
    "id": 3,
    "right_hand": [
        {"notes": ["C4"], "duration": "quarter"}  # Only 1 beat instead of 4
    ],
    "left_hand": [
        {"notes": ["C3"], "duration": "quarter"}  # Only 1 beat instead of 4
    ]
}

# Test with normal middle measure - should sum to 4
test_middle_measure = {
    "id": 2,
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
}

print("Testing first measure (incomplete - should allow 1 beat):")
print("="*70)
result1 = validate_measure(test_first_measure, is_first=True)
print(json.dumps(result1, indent=2))
print(f"Valid: {result1['both_valid']}")

print("\n\nTesting last measure (incomplete - should allow 1 beat):")
print("="*70)
result2 = validate_measure(test_last_measure, is_last=True)
print(json.dumps(result2, indent=2))
print(f"Valid: {result2['both_valid']}")

print("\n\nTesting middle measure (should require full 4 beats):")
print("="*70)
result3 = validate_measure(test_middle_measure, is_first=False, is_last=False)
print(json.dumps(result3, indent=2))
print(f"Valid: {result3['both_valid']}")

# Test with full music data
test_music_data = {
    "piece_name": "Test Piece with Incomplete Measures",
    "key": "C Major",
    "tempo": "120",
    "time_signature": {"numerator": 4, "denominator": 4},
    "measures": [test_first_measure, test_middle_measure, test_last_measure]
}

print("\n\nTesting full music data with incomplete first and last measures:")
print("="*70)
full_result = validate_all_measures(test_music_data)
print(f"Status: {full_result.get('status')}")
print(f"All Valid: {full_result.get('all_valid')}")
print(f"Valid Measures: {full_result.get('valid_measures')}/{full_result.get('total_measures')}")
print(f"\nMeasure Results:")
for r in full_result.get('measure_results', []):
    print(f"  Measure {r.get('measure_id')}: Valid={r.get('both_valid')}, "
          f"RH={r.get('right_hand_duration')}, LH={r.get('left_hand_duration')}, "
          f"First={r.get('is_first')}, Last={r.get('is_last')}")

