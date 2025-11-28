# Golden Data Generator Integration

## Summary

Successfully integrated the React music player (`json-music-player_v35.tsx`) with the evaluation system to create a human-in-the-loop tool for generating golden test data.

## Components Created

### 1. `tools/golden_data_manager.py`
- Manages golden test datasets
- Creates and organizes test cases
- Compares extracted vs golden data
- Stores metadata and corrections

### 2. `tools/golden_data_server.py`
- FastAPI web server
- Serves React music player
- REST API for golden data management
- Endpoints for loading, saving, and comparing data

### 3. `web/golden_data_player.jsx`
- Enhanced React component based on `json-music-player_v35.tsx`
- Features:
  - Play extracted JSON music
  - Edit JSON directly in UI
  - Save as golden data
  - Compare extracted vs golden
  - Test case management
  - Visual comparison metrics

### 4. `web/index.html`
- HTML wrapper for React app
- Loads React, Babel, Tailwind CSS

### 5. `generate_golden_data.py`
- CLI tool to start the server
- Command-line options for configuration
- Auto-opens browser

### 6. Enhanced `tools/evaluation_system.py`
- Added `evaluate_with_golden_data()` method
- Automatic comparison with golden data
- Accuracy metrics calculation

## Usage

### Start the Server

```bash
python generate_golden_data.py
```

### Generate Golden Data

1. Extract music sheet:
   ```bash
   python main.py "sheet.pdf" --user-id evaluator
   ```

2. Start golden data generator:
   ```bash
   python generate_golden_data.py --extraction library/xxx.json --test-id test_001
   ```

3. In web interface:
   - Play the extraction
   - Listen and verify
   - Edit JSON if needed
   - Save as golden data

### Use Golden Data for Evaluation

```python
from tools.evaluation_system import EvaluationSystem

evaluator = EvaluationSystem()
result = evaluator.evaluate_with_golden_data(
    test_id="test_001",
    extracted_data=extracted_data
)
```

## File Structure

```
sheet-reader-agent/
├── tools/
│   ├── golden_data_manager.py      # Golden data management
│   ├── golden_data_server.py       # FastAPI server
│   └── evaluation_system.py        # Enhanced evaluation
├── web/
│   ├── golden_data_player.jsx      # Enhanced React component
│   └── index.html                   # HTML wrapper
├── golden_data/                     # Golden test data storage
│   ├── test_cases.json             # Test case registry
│   └── test_001/
│       ├── extracted.json          # Original extraction
│       ├── golden.json             # Corrected golden data
│       └── metadata.json           # Test case metadata
└── generate_golden_data.py         # CLI tool
```

## API Endpoints

- `POST /api/load-extraction` - Load extracted JSON
- `POST /api/save-golden` - Save golden data
- `GET /api/test-cases` - List test cases
- `GET /api/test-case/{test_id}` - Get test case
- `GET /api/golden-data/{test_id}` - Get golden data
- `GET /api/compare/{test_id}` - Compare extracted vs golden

## Next Steps

1. Install dependencies: `pip install fastapi uvicorn`
2. Test the server: `python generate_golden_data.py`
3. Create test cases using the web interface
4. Use golden data for automated evaluation

