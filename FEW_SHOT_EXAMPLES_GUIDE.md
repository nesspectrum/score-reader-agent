# Few-Shot Examples Guide

## Overview

The extraction agent now uses **visual few-shot learning** with image files paired with their corresponding JSON extraction files. This provides better learning than text-only examples.

## Directory Structure

```
few_shot_examples/
├── example1.png          # Music sheet image
├── example1.json         # Corresponding extraction
├── bach_prelude.pdf      # Another example
├── bach_prelude.json     # Its extraction
└── README.md
```

## Creating Examples

### Method 1: From Library Entry (Easiest)

If you've already extracted a music sheet and it's in the library:

```bash
python3 create_few_shot_example.py \
    "resources/Bach_Prelude in C major, BWV 846.pdf" \
    --from-library
```

This will:
1. Calculate the hash of the PDF
2. Find the matching JSON in `library/`
3. Create the example pair in `few_shot_examples/`

### Method 2: From Image + JSON Files

If you have an image and its JSON extraction:

```bash
python3 create_few_shot_example.py \
    "path/to/sheet.png" \
    "path/to/extraction.json" \
    --description "My example description"
```

### Method 3: Using Test Script

```bash
python3 test_extraction_performance.py \
    --add-example "sheet.png" "extraction.json"
```

## JSON File Format

Each JSON file should contain:

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

## Using Examples

### Test with Examples

```bash
# Use default directory (few_shot_examples/)
python3 test_extraction_performance.py "sheet.pdf"

# Use custom directory
python3 test_extraction_performance.py "sheet.pdf" --few-shot-dir "my_examples"
```

### Compare Performance

```bash
# Compare with vs without few-shot examples
python3 test_extraction_performance.py --compare
```

## How It Works

1. **Loading**: Examples are loaded from the directory on agent initialization
2. **Inclusion**: Example images are included in the prompt to the model
3. **Learning**: The model sees both the example images and their correct JSON outputs
4. **Application**: The model applies the pattern to the target music sheet

## Best Practices

### Example Selection

Choose examples that:
- ✅ Match your use case (similar music styles)
- ✅ Cover different patterns (chords, arpeggios, scales)
- ✅ Include common edge cases (rests, polyphony)
- ✅ Are high quality (clear, readable)

### Example Quantity

- **Start**: 3-5 examples
- **Optimal**: 5-10 examples
- **Maximum**: 10-15 examples (more may hit token limits)

### Example Diversity

Include examples with:
- Different keys (C Major, G Major, A Minor, etc.)
- Different tempos (slow, moderate, fast)
- Different patterns (simple chords, complex polyphony)
- Different composers/styles

## Creating Example from Existing Extraction

If you've already extracted a sheet and want to use it as an example:

```bash
# Step 1: Extract the sheet (if not already done)
python3 main.py "sheet.pdf" --user-id "test"

# Step 2: Create few-shot example from library
python3 create_few_shot_example.py "sheet.pdf" --from-library

# Step 3: Verify the example was created
ls few_shot_examples/
```

## Example Workflow

1. **Extract a good example**:
   ```bash
   python3 main.py "good_example.pdf" --user-id "test"
   ```

2. **Review and correct** if needed (interactive mode)

3. **Create few-shot example**:
   ```bash
   python3 create_few_shot_example.py "good_example.pdf" --from-library
   ```

4. **Test with examples**:
   ```bash
   python3 test_extraction_performance.py "new_sheet.pdf"
   ```

5. **Compare performance**:
   ```bash
   python3 test_extraction_performance.py --compare
   ```

## Tips

- ✅ Use examples similar to your target music sheets
- ✅ Include examples that cover common mistakes
- ✅ Update examples as you find better patterns
- ✅ Test regularly to measure improvement
- ✅ Keep examples organized and documented

## Troubleshooting

### "No examples found"
- Check that `few_shot_examples/` directory exists
- Ensure image and JSON files have matching names
- Verify JSON files are valid

### "Token limit exceeded"
- Reduce number of examples (limit to 3-5)
- Use smaller images
- Simplify example JSONs

### "Examples not improving accuracy"
- Review example quality
- Ensure examples match your use case
- Try different example combinations

