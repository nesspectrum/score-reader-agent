# Golden Data Generator - Human-in-the-Loop Evaluation Tool

## Overview

The Golden Data Generator is an interactive web-based tool that integrates the React music player with the evaluation system to create ground truth (golden) test data for evaluating extraction accuracy.

## Features

- 🎵 **Play Extracted Music**: Listen to extracted JSON to verify accuracy
- ✏️ **Edit JSON**: Correct extraction errors directly in the UI
- 💾 **Save Golden Data**: Save corrected data as ground truth
- 📊 **Compare Results**: Compare extracted vs golden data automatically
- 🔄 **Test Case Management**: Organize test cases with metadata
- 📈 **Evaluation Integration**: Use golden data for automated evaluation

## Quick Start

### 1. Install Dependencies

```bash
pip install fastapi uvicorn
```

### 2. Start the Server

```bash
python generate_golden_data.py
```

The server will start on `http://127.0.0.1:8000` and open in your browser automatically.

### 3. Generate Golden Data

1. **Load Extraction**: Enter path to extracted JSON (e.g., `library/xxx.json`)
2. **Set Test ID**: Enter a test case ID (e.g., `test_001`)
3. **Play Music**: Click Play to listen to the extraction
4. **Edit if Needed**: Click "Edit JSON" to make corrections
5. **Save Golden**: Click "Save as Golden" to save corrected data

## Usage

### Basic Workflow

```bash
# 1. Extract music from sheet
python main.py "sheet.pdf" --user-id evaluator

# 2. Generate golden data
python generate_golden_data.py --extraction library/xxx.json --test-id test_001

# 3. Web interface opens - play, edit, save
```

### Command Line Options

```bash
python generate_golden_data.py [OPTIONS]

Options:
  --port PORT          Port to run server on (default: 8000)
  --host HOST          Host to bind to (default: 127.0.0.1)
  --no-browser         Don't open browser automatically
  --extraction PATH    Path to extracted JSON to load initially
  --test-id ID         Test case ID (e.g., test_001)
```

### API Endpoints

The server provides REST API endpoints:

- `POST /api/load-extraction` - Load extracted JSON
- `POST /api/save-golden` - Save golden data
- `GET /api/test-cases` - List all test cases
- `GET /api/test-case/{test_id}` - Get test case with data
- `GET /api/golden-data/{test_id}` - Get golden data
- `GET /api/compare/{test_id}` - Compare extracted vs golden

## Directory Structure

```
golden_data/
├── test_cases.json          # Test case registry
├── test_001/
│   ├── extracted.json       # Original extraction
│   ├── golden.json          # Corrected golden data
│   └── metadata.json        # Test case metadata
├── test_002/
│   └── ...
└── ...
```

## Integration with Evaluation System

### Using Golden Data for Evaluation

```python
from tools.evaluation_system import EvaluationSystem
from tools.golden_data_manager import GoldenDataManager

# Initialize
evaluator = EvaluationSystem()
golden_manager = GoldenDataManager()

# Evaluate against golden data
result = evaluator.evaluate_with_golden_data(
    test_id="test_001",
    extracted_data=extracted_data,
    user_id="evaluator"
)

# Get comparison metrics
comparison = result["comparison"]
print(f"Accuracy: {comparison['accuracy_score'] * 100}%")
```

### Using in Test Scripts

```python
# In test_extraction_performance.py
from tools.golden_data_manager import GoldenDataManager

golden_manager = GoldenDataManager()
golden_data = golden_manager.get_golden_data("test_001")

if golden_data:
    metrics = calculate_accuracy_metrics(extracted, golden_data)
    print_performance_report(metrics)
```

## Web Interface Features

### Test Case Management
- Load existing test cases
- Create new test cases
- View test case status (has golden data or not)

### Music Player
- Play extracted JSON
- Adjust tempo (25% - 200%)
- Select play mode (both/right/left hands)
- Debug log for playback details

### JSON Editor
- View JSON in formatted text
- Edit JSON directly
- Validate JSON syntax
- Compare original vs edited

### Comparison View
- Shows extracted vs golden comparison
- Highlights differences
- Calculates accuracy metrics

## Best Practices

1. **Test Case Naming**: Use descriptive IDs like `test_001_bach_prelude`
2. **Documentation**: Add notes when saving golden data
3. **Validation**: Use measure validator before saving
4. **Version Control**: Keep golden data in version control
5. **Regular Updates**: Update golden data as extraction improves

## Example Workflow

1. **Extract Music Sheet**:
   ```bash
   python main.py "resources/Bach_Prelude.pdf" --user-id evaluator
   ```

2. **Generate Golden Data**:
   ```bash
   python generate_golden_data.py \
       --extraction library/xxx.json \
       --test-id test_bach_prelude_001
   ```

3. **In Web Interface**:
   - Play the extraction
   - Listen and verify accuracy
   - Edit JSON if corrections needed
   - Save as golden data

4. **Use for Evaluation**:
   ```python
   result = evaluator.evaluate_with_golden_data(
       test_id="test_bach_prelude_001",
       extracted_data=new_extraction
   )
   ```

## Troubleshooting

### Server Won't Start
- Check if port 8000 is available
- Install dependencies: `pip install fastapi uvicorn`

### JSON Won't Load
- Check file path is correct
- Verify JSON syntax is valid
- Check file permissions

### Playback Issues
- Check browser audio permissions
- Verify JSON has valid music data
- Check debug log for errors

## Next Steps

- Add batch processing for multiple test cases
- Integrate with CI/CD for automated testing
- Add export functionality for test datasets
- Create evaluation reports and dashboards

