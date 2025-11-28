"""
MusicXML Parser - Converts MusicXML files to the JSON format expected by ExtractionAgent
"""

import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional
import re


# Duration mapping from MusicXML divisions to note names
DURATION_MAP = {
    1: "whole",
    2: "half",
    4: "quarter",
    8: "eighth",
    16: "sixteenth",
    32: "thirty-second",
    64: "sixty-fourth"
}

# Reverse mapping for common durations
DURATION_TO_DIVISIONS = {
    "whole": 1,
    "half": 2,
    "quarter": 4,
    "eighth": 8,
    "sixteenth": 16,
    "thirty-second": 32,
    "sixty-fourth": 64
}


def _get_note_type_from_duration(duration: int, divisions: int) -> str:
    """
    Convert duration in divisions to note type name.
    
    Args:
        duration: Duration in divisions
        divisions: Divisions per quarter note
        
    Returns:
        Note type name (e.g., "quarter", "eighth")
    """
    # Normalize to quarter note = 1
    normalized = duration / divisions
    
    # Find closest match
    closest_type = "quarter"
    min_diff = abs(normalized - 1.0)
    
    for note_type, divs in DURATION_TO_DIVISIONS.items():
        diff = abs(normalized - (4.0 / divs))
        if diff < min_diff:
            min_diff = diff
            closest_type = note_type
    
    return closest_type


def _pitch_to_note_name(step: str, alter: Optional[int], octave: int) -> str:
    """
    Convert MusicXML pitch to note name (e.g., "C4", "F#5").
    
    Args:
        step: Note step (C, D, E, F, G, A, B)
        alter: Alteration (-1 for flat, 0 for natural, 1 for sharp)
        octave: Octave number
        
    Returns:
        Note name string
    """
    note = step
    
    if alter is not None:
        if alter == -1:
            note += "b"  # flat
        elif alter == 1:
            note += "#"  # sharp
        # alter == 0 means natural, no symbol needed
    
    return f"{note}{octave}"


def _parse_key_signature(key_elem: ET.Element) -> str:
    """
    Parse key signature from MusicXML.
    
    Args:
        key_elem: XML element containing key signature
        
    Returns:
        Key signature string (e.g., "C Major", "G Major")
    """
    fifths_elem = key_elem.find(".//fifths")
    mode_elem = key_elem.find(".//mode")
    
    if fifths_elem is None:
        return "C Major"
    
    fifths = int(fifths_elem.text) if fifths_elem.text else 0
    mode = mode_elem.text if mode_elem is not None and mode_elem.text else "major"
    
    # Map fifths to key
    major_keys = {
        0: "C", 1: "G", 2: "D", 3: "A", 4: "E", 5: "B", 6: "F#",
        -1: "F", -2: "Bb", -3: "Eb", -4: "Ab", -5: "Db", -6: "Gb"
    }
    
    minor_keys = {
        0: "A", 1: "E", 2: "B", 3: "F#", 4: "C#", 5: "G#", 6: "D#",
        -1: "D", -2: "G", -3: "C", -4: "F", -5: "Bb", -6: "Eb"
    }
    
    key_map = minor_keys if mode.lower() == "minor" else major_keys
    key_name = key_map.get(fifths, "C")
    
    return f"{key_name} {mode.capitalize()}"


def _parse_tempo(measure: ET.Element) -> Optional[str]:
    """
    Parse tempo from a measure.
    
    Args:
        measure: XML measure element
        
    Returns:
        Tempo string or None
    """
    # Look for sound elements with tempo
    sound_elem = measure.find(".//sound")
    if sound_elem is not None:
        tempo = sound_elem.get("tempo")
        if tempo:
            return tempo
    
    # Look for direction with metronome
    direction = measure.find(".//direction")
    if direction is not None:
        metronome = direction.find(".//metronome")
        if metronome is not None:
            beat_unit = metronome.find("beat-unit")
            per_minute = metronome.find("per-minute")
            if per_minute is not None:
                return per_minute.text
    
    return None


def _parse_clef(clef_elem: ET.Element) -> str:
    """
    Determine if clef is treble (upper) or bass (lower).
    
    Args:
        clef_elem: XML clef element
        
    Returns:
        "upper" for treble, "lower" for bass
    """
    sign_elem = clef_elem.find("sign")
    if sign_elem is not None:
        sign = sign_elem.text
        if sign and sign.upper() == "G":
            return "upper"
        elif sign and sign.upper() == "F":
            return "lower"
    
    # Default based on line
    line_elem = clef_elem.find("line")
    if line_elem is not None:
        line = int(line_elem.text) if line_elem.text else 2
        if line <= 2:
            return "upper"
    
    return "lower"


def parse_musicxml_to_json(xml_path: str) -> Dict[str, Any]:
    """
    Parse a MusicXML file and convert it to the JSON format expected by ExtractionAgent.
    
    Args:
        xml_path: Path to the MusicXML file
        
    Returns:
        Dictionary with music data in the expected format
    """
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        # Handle MusicXML namespace
        ns = {'mx': 'http://www.musicxml.org/ns/partwise/2009-08-01'}
        
        # Try without namespace first
        score_partwise = root.find("score-partwise")
        if score_partwise is None:
            score_partwise = root.find(".//{http://www.musicxml.org/ns/partwise/2009-08-01}score-partwise")
            if score_partwise is None:
                score_partwise = root
        
        # Extract piece name
        work_title = score_partwise.find(".//work/work-title")
        piece_name = work_title.text if work_title is not None else ""
        
        # Extract composer
        creator = score_partwise.find(".//identification/creator")
        composer = creator.text if creator is not None and creator.get("type") == "composer" else ""
        
        # Get parts
        parts = score_partwise.findall(".//part")
        if not parts:
            parts = score_partwise.findall(".//{http://www.musicxml.org/ns/partwise/2009-08-01}part")
        
        if not parts:
            return {
                "status": "error",
                "error_message": "No parts found in MusicXML"
            }
        
        # Parse first part (typically piano part)
        part = parts[0]
        measures = part.findall("measure")
        if not measures:
            measures = part.findall("{http://www.musicxml.org/ns/partwise/2009-08-01}measure")
        
        if not measures:
            return {
                "status": "error",
                "error_message": "No measures found in MusicXML"
            }
        
        # Get divisions (divisions per quarter note)
        first_measure = measures[0]
        attributes = first_measure.find("attributes")
        if attributes is None:
            attributes = first_measure.find("{http://www.musicxml.org/ns/partwise/2009-08-01}attributes")
        
        divisions = 1
        if attributes is not None:
            divs_elem = attributes.find("divisions")
            if divs_elem is None:
                divs_elem = attributes.find("{http://www.musicxml.org/ns/partwise/2009-08-01}divisions")
            if divs_elem is not None and divs_elem.text:
                divisions = int(divs_elem.text)
        
        # Parse key signature
        key = "C Major"
        if attributes is not None:
            key_elem = attributes.find("key")
            if key_elem is None:
                key_elem = attributes.find("{http://www.musicxml.org/ns/partwise/2009-08-01}key")
            if key_elem is not None:
                key = _parse_key_signature(key_elem)
        
        # Parse tempo
        tempo = None
        for measure in measures[:3]:  # Check first few measures
            tempo = _parse_tempo(measure)
            if tempo:
                break
        
        # Parse measures
        parsed_measures = []
        right_hand_events = []
        left_hand_events = []
        
        for measure_idx, measure in enumerate(measures):
            measure_number = measure.get("number", str(measure_idx + 1))
            
            # Get notes in this measure
            notes = measure.findall(".//note")
            if not notes:
                notes = measure.findall(".//{http://www.musicxml.org/ns/partwise/2009-08-01}note")
            
            # Separate by staff (voice)
            for note in notes:
                # Check if rest
                rest_elem = note.find("rest")
                if rest_elem is None:
                    rest_elem = note.find("{http://www.musicxml.org/ns/partwise/2009-08-01}rest")
                
                # Get staff number (1 = upper/right, 2 = lower/left)
                staff_elem = note.find("staff")
                if staff_elem is None:
                    staff_elem = note.find("{http://www.musicxml.org/ns/partwise/2009-08-01}staff")
                
                staff_num = 1
                if staff_elem is not None and staff_elem.text:
                    staff_num = int(staff_elem.text)
                
                # Get duration
                duration_elem = note.find("duration")
                if duration_elem is None:
                    duration_elem = note.find("{http://www.musicxml.org/ns/partwise/2009-08-01}duration")
                
                if duration_elem is None or not duration_elem.text:
                    continue
                
                duration_divs = int(duration_elem.text)
                duration_type = _get_note_type_from_duration(duration_divs, divisions)
                
                # Check if chord (multiple notes played together)
                chord_elem = note.find("chord")
                if chord_elem is None:
                    chord_elem = note.find("{http://www.musicxml.org/ns/partwise/2009-08-01}chord")
                
                is_chord = chord_elem is not None
                
                if rest_elem is not None:
                    # Rest
                    note_name = "Rest"
                else:
                    # Get pitch
                    pitch_elem = note.find("pitch")
                    if pitch_elem is None:
                        pitch_elem = note.find("{http://www.musicxml.org/ns/partwise/2009-08-01}pitch")
                    
                    if pitch_elem is None:
                        continue
                    
                    step_elem = pitch_elem.find("step")
                    if step_elem is None:
                        step_elem = pitch_elem.find("{http://www.musicxml.org/ns/partwise/2009-08-01}step")
                    
                    octave_elem = pitch_elem.find("octave")
                    if octave_elem is None:
                        octave_elem = pitch_elem.find("{http://www.musicxml.org/ns/partwise/2009-08-01}octave")
                    
                    alter_elem = pitch_elem.find("alter")
                    if alter_elem is None:
                        alter_elem = pitch_elem.find("{http://www.musicxml.org/ns/partwise/2009-08-01}alter")
                    
                    if step_elem is None or octave_elem is None:
                        continue
                    
                    step = step_elem.text
                    octave = int(octave_elem.text) if octave_elem.text else 4
                    alter = int(alter_elem.text) if alter_elem is not None and alter_elem.text else 0
                    
                    note_name = _pitch_to_note_name(step, alter, octave)
                
                # Add to appropriate hand
                event = {
                    "notes": [note_name],
                    "duration": duration_type
                }
                
                if staff_num == 1:
                    if not is_chord and right_hand_events:
                        # Add previous event if not a chord continuation
                        pass
                    right_hand_events.append(event)
                else:
                    if not is_chord and left_hand_events:
                        # Add previous event if not a chord continuation
                        pass
                    left_hand_events.append(event)
                
                # Handle chords - add to previous event's notes
                if is_chord:
                    if staff_num == 1 and right_hand_events:
                        right_hand_events[-1]["notes"].append(note_name)
                    elif staff_num == 2 and left_hand_events:
                        left_hand_events[-1]["notes"].append(note_name)
            
            # Create measure
            parsed_measure = {
                "id": int(measure_number) if measure_number.isdigit() else measure_idx + 1,
                "right_hand": right_hand_events.copy(),
                "left_hand": left_hand_events.copy()
            }
            
            parsed_measures.append(parsed_measure)
            
            # Clear events for next measure
            right_hand_events = []
            left_hand_events = []
        
        result = {
            "status": "success",
            "piece_name": piece_name,
            "composer": composer,
            "key": key,
            "tempo": tempo,
            "measures": parsed_measures
        }
        
        return result
        
    except ET.ParseError as e:
        return {
            "status": "error",
            "error_message": f"XML parsing error: {str(e)}"
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Error parsing MusicXML: {str(e)}"
        }

