"""
Measure Validation Tool
Validates that extracted measures have correct durations based on time signature.
"""

import json
from fractions import Fraction
from typing import Dict, Any, List, Optional


# Duration mapping to fractional beat values
DURATION_VALUES = {
    "whole": Fraction(4, 1),
    "half": Fraction(2, 1),
    "quarter": Fraction(1, 1),
    "eighth": Fraction(1, 2),
    "sixteenth": Fraction(1, 4),
    "thirty_second": Fraction(1, 8),
    "rest": Fraction(0, 1),  # Rest needs duration specified separately
    # Dotted durations
    "dotted whole": Fraction(6, 1),
    "dotted half": Fraction(3, 1),
    "dotted quarter": Fraction(3, 2),
    "dotted eighth": Fraction(3, 4),
    "dotted sixteenth": Fraction(3, 8),
    # Common typos/variations
    "eigths": Fraction(1, 2),  # Common typo for "eighths"
    "eigth": Fraction(1, 2),   # Common typo for "eighth"
}


def parse_duration(duration_input) -> Fraction:
    """
    Parse duration which can be:
    - String: "quarter", "eighth", "half", "half, sixteenth", "seven sixteenth"
    - Array: ["half", "sixteenth"] - for overlapping notes, use only the last element (gap duration)
    - Complex: "7 * sixteenth"
    
    Note: For array format like ["half", "sixteenth"], this represents:
    - A sustained note for "half" duration
    - A gap of "sixteenth" before the next note starts
    - For sequential calculation, we use the gap duration (last element)
    """
    # Handle array/list format
    if isinstance(duration_input, list):
        if len(duration_input) == 0:
            return Fraction(0, 1)
        # For overlapping notes, use the last element (gap duration) for sequential calculation
        # This represents when the next note starts
        return parse_duration(duration_input[-1])
    
    # Handle None or empty
    if not duration_input:
        return Fraction(0, 1)
    
    # Convert to string if not already
    if not isinstance(duration_input, str):
        duration_input = str(duration_input)
    
    duration_str = duration_input.strip().lower()
    
    if not duration_str:
        return Fraction(0, 1)
    
    # Handle addition (comma-separated)
    if ',' in duration_str:
        parts = duration_str.split(',')
        return sum(parse_duration(part.strip()) for part in parts)
    
    # Handle multiplication with *
    if '*' in duration_str:
        parts = duration_str.split('*')
        multiplier = int(parts[0].strip())
        duration_type = parts[1].strip()
        return multiplier * DURATION_VALUES.get(duration_type, Fraction(0, 1))
    
    # Handle written numbers like "seven sixteenth", "three eighths"
    number_words = {
        "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
        "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10
    }
    
    words = duration_str.split()
    if len(words) >= 2 and words[0] in number_words:
        multiplier = number_words[words[0]]
        # Handle "three eighths", "three eigths" (typo), etc.
        duration_type = words[1].lower()
        # Normalize common typos
        if duration_type in ["eigths", "eigth"]:
            duration_type = "eighth"
        elif duration_type == "sixteenths":
            duration_type = "sixteenth"
        base_duration = DURATION_VALUES.get(duration_type, Fraction(0, 1))
        return multiplier * base_duration
    
    # Simple duration
    return DURATION_VALUES.get(duration_str, Fraction(0, 1))


def calculate_measure_duration_events(events: List[Dict[str, Any]], time_signature: Dict[str, int], 
                                     is_left_hand: bool = False) -> Fraction:
    """
    Calculate the total duration of events in a measure.
    Works with extraction agent format: {"notes": [...], "duration": "..."} or {"notes": [...], "duration": [...]}
    
    For left hand with array durations like ["half", "sixteenth"]:
    - This format indicates overlapping/sustained notes
    - The first element is the sustained note duration
    - Subsequent elements are gaps/rests before the next sequential note
    - For measure validation, we need to track when each voice ends
    - The measure duration is when the last voice finishes
    
    Args:
        events: List of events with "notes" and "duration" fields
        time_signature: Dict with "numerator" and "denominator"
        is_left_hand: Whether this is left hand (can have overlapping notes)
    
    Returns:
        Total duration as Fraction in terms of quarter notes
    """
    if not events:
        return Fraction(0, 1)
    
    # For both hands, events are sequential
    # Each event has a duration, and events happen one after another
    total = Fraction(0, 1)
    
    for event in events:
        duration_input = event.get("duration", "quarter")
        duration = parse_duration(duration_input)
        total += duration
    
    return total


def validate_measure(measure: Dict[str, Any], time_signature: Optional[Dict[str, int]] = None) -> Dict[str, Any]:
    """
    Validate that a measure's duration equals exactly one measure
    based on the time signature.
    
    Args:
        measure: Measure dict with "id", "right_hand", "left_hand", optionally "time_signature"
        time_signature: Global time signature dict with "numerator" and "denominator" (default: 4/4)
                       Will be overridden by measure-specific time_signature if present
    
    Returns:
        Validation results dictionary
    """
    # Use measure-specific time signature if present, otherwise use global
    measure_time_signature = measure.get("time_signature")
    if measure_time_signature is not None:
        # Handle both dict and string formats
        if isinstance(measure_time_signature, str):
            # Parse "4/4" format
            parts = measure_time_signature.split('/')
            if len(parts) == 2:
                time_signature = {"numerator": int(parts[0]), "denominator": int(parts[1])}
            else:
                time_signature = time_signature or {"numerator": 4, "denominator": 4}
        elif isinstance(measure_time_signature, dict):
            time_signature = measure_time_signature
        else:
            time_signature = time_signature or {"numerator": 4, "denominator": 4}
    else:
        # Use global time signature or default
        if time_signature is None:
            time_signature = {"numerator": 4, "denominator": 4}
    
    expected_duration = Fraction(time_signature["numerator"], time_signature["denominator"]) * 4
    
    right_hand_events = measure.get("right_hand", [])
    left_hand_events = measure.get("left_hand", [])
    
    right_hand_duration = calculate_measure_duration_events(
        right_hand_events,
        time_signature,
        is_left_hand=False
    )
    
    left_hand_duration = calculate_measure_duration_events(
        left_hand_events,
        time_signature,
        is_left_hand=True
    )
    
    measure_id = measure.get("id", "?")
    
    # Allow small tolerance for floating point errors
    tolerance = Fraction(1, 1000)
    
    # Check against expected duration
    right_valid = abs(right_hand_duration - expected_duration) <= tolerance
    left_valid = abs(left_hand_duration - expected_duration) <= tolerance
    
    # Calculate errors
    right_error = float(abs(right_hand_duration - expected_duration))
    left_error = float(abs(left_hand_duration - expected_duration))
    
    results = {
        "measure_id": measure_id,
        "time_signature": f"{time_signature['numerator']}/{time_signature['denominator']}",
        "expected_duration": float(expected_duration),
        "right_hand_duration": float(right_hand_duration),
        "left_hand_duration": float(left_hand_duration),
        "right_hand_valid": right_valid,
        "left_hand_valid": left_valid,
        "both_valid": right_valid and left_valid,
        "right_hand_error": right_error,
        "left_hand_error": left_error
    }
    
    return results


def validate_all_measures(music_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate all measures in extracted music data.
    
    Args:
        music_data: Extracted music data with "measures" list
    
    Returns:
        Validation results for all measures
    """
    # Extract time signature (default to 4/4)
    time_signature = music_data.get("time_signature", {"numerator": 4, "denominator": 4})
    
    # Handle legacy format where time_signature might be a string
    if isinstance(time_signature, str):
        # Parse "4/4" format
        parts = time_signature.split('/')
        if len(parts) == 2:
            time_signature = {"numerator": int(parts[0]), "denominator": int(parts[1])}
        else:
            time_signature = {"numerator": 4, "denominator": 4}
    
    measures = music_data.get("measures", [])
    
    if not measures:
        return {
            "status": "error",
            "error_message": "No measures found in music data"
        }
    
    results = []
    all_valid = True
    
    total_measures = len(measures)
    
    # Track the current time signature (may change per measure)
    current_time_signature = time_signature
    
    for i, measure in enumerate(measures):
        # Use measure-specific time signature if present, otherwise use current
        measure_time_sig = measure.get("time_signature")
        if measure_time_sig is not None:
            # Update current time signature for subsequent measures
            if isinstance(measure_time_sig, str):
                parts = measure_time_sig.split('/')
                if len(parts) == 2:
                    current_time_signature = {"numerator": int(parts[0]), "denominator": int(parts[1])}
            elif isinstance(measure_time_sig, dict):
                current_time_signature = measure_time_sig
        
        result = validate_measure(measure, current_time_signature)
        results.append(result)
        if not result["both_valid"]:
            all_valid = False
    
    # Calculate statistics
    valid_count = sum(1 for r in results if r["both_valid"])
    invalid_count = len(results) - valid_count
    
    return {
        "status": "success",
        "time_signature": f"{time_signature['numerator']}/{time_signature['denominator']}",
        "total_measures": len(measures),
        "valid_measures": valid_count,
        "invalid_measures": invalid_count,
        "all_valid": all_valid,
        "measure_results": results,
        "summary": {
            "right_hand_valid_count": sum(1 for r in results if r["right_hand_valid"]),
            "left_hand_valid_count": sum(1 for r in results if r["left_hand_valid"]),
            "average_right_hand_error": sum(r["right_hand_error"] for r in results) / len(results) if results else 0,
            "average_left_hand_error": sum(r["left_hand_error"] for r in results) / len(results) if results else 0
        }
    }

