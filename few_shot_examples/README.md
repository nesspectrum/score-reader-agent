# Few-Shot Examples Directory

This directory contains example music sheet images paired with their corresponding JSON extraction files.

## Directory Structure

```
few_shot_examples/
├── example1.png
├── example1.json
├── example2.jpg
├── example2.json
├── bach_prelude.pdf
├── bach_prelude.json
└── README.md
```

## File Naming Convention

- Image files: `example_name.png` (or `.jpg`, `.jpeg`, `.pdf`)
- JSON files: `example_name.json` (must match image name)

## JSON File Format

Each JSON file should contain the extracted music data:

```json
{
  "description": "Brief description of the example",
  "piece_name": "Prelude in C Major",
  "composer": "Bach",
  "key": "C Major",
  "tempo": "112",
  "measures": [
    {
      "id": 1,
      "right_hand": [
        {"notes": ["C5"], "duration": "eighth"},
        {"notes": ["E5"], "duration": "eighth"}
      ],
      "left_hand": [
        {"notes": ["C3"], "duration": "quarter"}
      ]
    }
  ]
}
```

## Adding Examples

### Method 1: Using the test script

```bash
python3 test_extraction_performance.py --add-example path/to/image.png path/to/extraction.json
```

### Method 2: Manual

1. Copy your example image to this directory
2. Create a JSON file with the same base name
3. Ensure JSON contains the `description` field

## Best Practices

1. **Diversity**: Include examples of different:
   - Keys (C Major, G Major, A Minor, etc.)
   - Tempos (slow, moderate, fast)
   - Patterns (chords, arpeggios, scales, polyphony)
   - Difficulties (simple, complex)

2. **Quality**: Use clear, readable music sheets
   - High resolution images
   - Clear notation
   - Complete measures

3. **Accuracy**: Ensure JSON extractions are correct
   - Verify note names
   - Check durations
   - Validate structure

4. **Quantity**: Start with 3-5 examples, add more as needed

## Example Use Cases

- **Simple patterns**: Basic chord progressions
- **Complex patterns**: Polyphonic textures, fast passages
- **Specific composers**: Bach, Beethoven, Chopin styles
- **Common errors**: Examples that help avoid common mistakes

