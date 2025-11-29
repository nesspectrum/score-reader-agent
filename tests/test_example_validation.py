#!/usr/bin/env python3
"""
Test validation of example JSON files
"""

import json
import os
from tools.measure_validator import validate_all_measures

def test_example_file(file_path: str):
    """Test validation of a single example file."""
    print(f"\n{'='*80}")
    print(f"Testing: {file_path}")
    print(f"{'='*80}")
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return
    
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        result = validate_all_measures(data)
        
        if result.get('status') == 'error':
            print(f"❌ Error: {result.get('error_message')}")
            return
        
        print(f"\n📊 Validation Results:")
        print(f"   Time Signature: {result.get('time_signature')}")
        print(f"   Total Measures: {result.get('total_measures')}")
        print(f"   Valid Measures: {result.get('valid_measures')}")
        print(f"   Invalid Measures: {result.get('invalid_measures')}")
        print(f"   All Valid: {'✅ YES' if result.get('all_valid') else '❌ NO'}")
        
        summary = result.get('summary', {})
        print(f"\n📈 Summary:")
        print(f"   Right Hand Valid: {summary.get('right_hand_valid_count')}/{result.get('total_measures')}")
        print(f"   Left Hand Valid: {summary.get('left_hand_valid_count')}/{result.get('total_measures')}")
        print(f"   Avg RH Error: {summary.get('average_right_hand_error', 0):.4f} beats")
        print(f"   Avg LH Error: {summary.get('average_left_hand_error', 0):.4f} beats")
        
        # Show details for invalid measures
        invalid_measures = [r for r in result.get('measure_results', []) if not r.get('both_valid')]
        if invalid_measures:
            print(f"\n⚠️  Invalid Measures Details:")
            for r in invalid_measures:
                print(f"\n   Measure {r.get('measure_id')}:")
                print(f"      Expected: {r.get('expected_duration')} beats")
                if not r.get('right_hand_valid'):
                    print(f"      Right Hand: {r.get('right_hand_duration')} beats (error: {r.get('right_hand_error'):.4f})")
                if not r.get('left_hand_valid'):
                    print(f"      Left Hand: {r.get('left_hand_duration')} beats (error: {r.get('left_hand_error'):.4f})")
        else:
            print(f"\n✅ All measures are valid!")
        
    except Exception as e:
        print(f"❌ Error processing file: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Test all example files."""
    examples = [
        "resources/example1.json",
        "resources/example2.json",
        "resources/example3.json"
    ]
    
    for example in examples:
        test_example_file(example)
    
    print(f"\n{'='*80}")
    print("Validation Complete")
    print(f"{'='*80}")


if __name__ == "__main__":
    main()

