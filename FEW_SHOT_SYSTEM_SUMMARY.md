# Few-Shot Learning System Summary

## What Changed

The extraction agent now uses **visual few-shot learning** with actual image files paired with their JSON extraction files, instead of just text examples.

## Key Features

### 1. Image + JSON Pairs
- Each example consists of:
  - **Image file**: `.png`, `.jpg`, `.pdf` (the music sheet)
  - **JSON file**: `.json` (the correct extraction)

### 2. Automatic Loading
- Examples are automatically loaded from `few_shot_examples/` directory
- Matching is done by filename (e.g., `example1.png` + `example1.json`)

### 3. Visual Learning
- Example images are included in the prompt to the model
- Model sees both the visual example and its correct JSON output
- Better learning than text-only examples

## File Structure

```
few_shot_examples/
├── example1.png              # Music sheet image
├── example1.json             # Correct extraction
├── bach_prelude.pdf          # Another example
├── bach_prelude.json         # Its extraction
└── README.md                 # Documentation
```

## Quick Start

### 1. Create an Example from Existing Extraction

```bash
# If you've already extracted a sheet:
python3 create_few_shot_example.py \
    "resources/Bach_Prelude in C major, BWV 846.pdf" \
    --from-library
```

### 2. Test with Examples

```bash
# Test extraction using the examples
python3 test_extraction_performance.py \
    "resources/Bach_Prelude in C major, BWV 846.pdf"
```

### 3. Compare Performance

```bash
# Compare with vs without few-shot examples
python3 test_extraction_performance.py --compare
```

## How It Works

1. **Loading Phase**:
   - Script scans `few_shot_examples/` directory
   - Finds all image files (`.png`, `.jpg`, `.pdf`)
   - Matches them with corresponding `.json` files
   - Loads the JSON data

2. **Prompt Construction**:
   - Includes JSON examples in text format
   - Includes example images in the prompt
   - Shows model: "Here are examples of correct extractions"

3. **Extraction Phase**:
   - Model sees example images + their JSON outputs
   - Model applies patterns to target music sheet
   - Better accuracy through visual learning

## Benefits

✅ **Visual Learning**: Model sees actual music sheets, not just text
✅ **Real Examples**: Uses real extraction data, not synthetic
✅ **Easy to Add**: Simple file-based system
✅ **Flexible**: Can add/remove examples easily
✅ **Measurable**: Can compare performance with/without examples

## Example JSON Format

```json
{
  "description": "Bach Prelude in C Major - Arpeggio pattern",
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

## Scripts

1. **`test_extraction_performance.py`**: Test extraction with few-shot examples
2. **`create_few_shot_example.py`**: Create example pairs from existing extractions

## Next Steps

1. Add more examples to `few_shot_examples/`
2. Test with different music sheets
3. Compare performance improvements
4. Refine examples based on results

