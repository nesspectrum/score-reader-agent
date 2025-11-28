# Extraction Performance Testing Script

## Overview

`test_extraction_performance.py` is a standalone script to test and improve `ExtractionAgent` performance using few-shot learning examples.

## Features

- ✅ **Few-Shot Learning**: Includes 5 pre-built examples of different music patterns
- ✅ **Performance Metrics**: Calculates accuracy scores comparing extracted vs expected data
- ✅ **Comparison Testing**: Compare extraction with vs without few-shot examples
- ✅ **Custom Examples**: Add your own examples to improve accuracy
- ✅ **Example Management**: Save/load examples to/from JSON files

## Usage

### Basic Test

```bash
# Test extraction with few-shot examples (default)
python3 test_extraction_performance.py "resources/Bach_Prelude in C major, BWV 846.pdf"

# Test without few-shot examples
python3 test_extraction_performance.py "resources/Bach_Prelude in C major, BWV 846.pdf" --no-few-shot
```

### Test with Expected Data (Accuracy Comparison)

```bash
# Compare extracted data with expected JSON
python3 test_extraction_performance.py \
    "resources/Bach_Prelude in C major, BWV 846.pdf" \
    --expected test_expected_bach_prelude.json
```

### Compare Few-Shot vs No Few-Shot

```bash
# Run comparison test
python3 test_extraction_performance.py --compare
```

### Manage Examples

```bash
# Save examples to file
python3 test_extraction_performance.py --save-examples few_shot_examples.json

# Load examples from file
python3 test_extraction_performance.py --load-examples few_shot_examples.json

# Add custom example
python3 test_extraction_performance.py --add-example my_example.json
```

## Few-Shot Examples Included

1. **Simple C Major chord progression** - Basic chord patterns
2. **Bach-style arpeggio pattern** - Arpeggiated patterns
3. **Rest and single note pattern** - Rests and single notes
4. **Chromatic scale pattern** - Fast note sequences
5. **Polyphonic texture** - Multiple voices/chords

## Example JSON Format

To add your own example, create a JSON file:

```json
{
  "description": "My custom example description",
  "example": {
    "key": "C Major",
    "tempo": "120",
    "measures": [
      {
        "id": 1,
        "right_hand": [
          {"notes": ["C4", "E4"], "duration": "quarter"},
          {"notes": ["G4"], "duration": "quarter"}
        ],
        "left_hand": [
          {"notes": ["C3"], "duration": "half"}
        ]
      }
    ]
  }
}
```

## Performance Metrics

The script calculates:

- **Key Match**: Extracted key matches expected
- **Tempo Match**: Extracted tempo matches expected
- **Piece Name Match**: Extracted piece name matches expected
- **Composer Match**: Extracted composer matches expected
- **Measure Count Match**: Number of measures matches
- **Measure-by-Measure Accuracy**: Right/left hand event counts per measure

## Output Example

```
================================================================================
TESTING EXTRACTION: resources/Bach_Prelude in C major, BWV 846.pdf
================================================================================
Extracting notes from resources/Bach_Prelude in C major, BWV 846.pdf...
✓ Extraction validated successfully

✅ Extraction completed in 5.23 seconds

📋 Extracted Data:
   Piece Name: Prelude in C Major
   Composer: Bach
   Key: C Major
   Tempo: 112
   Measures: 35

================================================================================
PERFORMANCE REPORT
================================================================================

⏱️  Extraction Time: 5.23 seconds

📊 Accuracy Metrics:
   Key Match:        ✅
   Tempo Match:      ✅
   Piece Name Match: ✅
   Composer Match:   ✅
   Measure Count:    ✅

📈 Overall Score: 5/5

🎵 Measure-by-Measure Accuracy:
   Measure 1: RH ✅ | LH ✅
   Measure 2: RH ✅ | LH ✅
   ...
```

## Improving Performance

1. **Add More Examples**: Include examples similar to your music sheets
2. **Refine Existing Examples**: Update examples to match common patterns
3. **Test Different Patterns**: Test with various music styles
4. **Compare Results**: Use `--compare` to see improvement

## Tips

- Start with the included examples
- Add examples that match your specific use case
- Test with `--compare` to measure improvement
- Save your examples for reuse: `--save-examples`
- Use `--expected` to compare against ground truth data

