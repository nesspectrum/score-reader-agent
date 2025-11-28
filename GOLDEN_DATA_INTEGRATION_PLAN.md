# Golden Data Generator Integration Plan

## Overview
Integrate the React music player (`json-music-player_v35.tsx`) with the evaluation system to create a human-in-the-loop tool for generating golden test data.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  FastAPI Web Server (golden_data_server.py)            │
│  - Serves React music player                            │
│  - API endpoints for golden data management             │
│  - Integrates with EvaluationSystem                     │
└─────────────────────────────────────────────────────────┘
                        ↕
┌─────────────────────────────────────────────────────────┐
│  React Music Player (Enhanced)                          │
│  - Play extracted JSON                                  │
│  - Edit/correct JSON in UI                             │
│  - Save as golden data                                  │
│  - Compare extracted vs golden                          │
└─────────────────────────────────────────────────────────┘
                        ↕
┌─────────────────────────────────────────────────────────┐
│  Golden Data Storage                                    │
│  - golden_data/ directory                               │
│  - Test case files                                      │
│  - Linked to evaluations                                │
└─────────────────────────────────────────────────────────┘
```

## Components to Create

### 1. FastAPI Server (`tools/golden_data_server.py`)
- Serve static React app
- API endpoints:
  - `POST /api/load-extraction` - Load extracted JSON
  - `POST /api/save-golden` - Save corrected JSON as golden data
  - `GET /api/golden-data/{test_id}` - Get golden data
  - `GET /api/test-cases` - List all test cases
  - `POST /api/create-test-case` - Create new test case

### 2. Enhanced React Component (`web/golden_data_player.tsx`)
- Based on `json-music-player_v35.tsx`
- Add JSON editor
- Add comparison view (extracted vs golden)
- Add save/load golden data buttons
- Add validation feedback

### 3. Golden Data Manager (`tools/golden_data_manager.py`)
- Manages golden test datasets
- Links to evaluation system
- Validates golden data format
- Creates test case structure

### 4. Integration Script (`generate_golden_data.py`)
- CLI tool to start server
- Load extraction results
- Launch web interface

## File Structure

```
sheet-reader-agent/
├── tools/
│   ├── golden_data_server.py      # FastAPI server
│   ├── golden_data_manager.py     # Golden data management
│   └── evaluation_system.py        # Enhanced with golden data support
├── web/
│   ├── golden_data_player.tsx      # Enhanced React component
│   ├── index.html                  # HTML wrapper
│   └── package.json                # React dependencies
├── golden_data/                    # Golden test data storage
│   ├── test_cases.json            # Test case registry
│   ├── test_001/
│   │   ├── extracted.json        # Original extraction
│   │   ├── golden.json            # Corrected golden data
│   │   └── metadata.json          # Test case metadata
│   └── ...
└── generate_golden_data.py        # CLI tool
```

## Workflow

1. **Extract Music Sheet**
   ```bash
   python main.py sheet.pdf --user-id evaluator
   ```

2. **Generate Golden Data**
   ```bash
   python generate_golden_data.py --extraction library/xxx.json
   ```

3. **Web Interface Opens**
   - Play extracted JSON
   - Listen and verify
   - Edit JSON if needed
   - Save as golden data

4. **Use for Evaluation**
   - Compare future extractions against golden data
   - Calculate accuracy metrics
   - Track improvements

## API Endpoints

### POST /api/load-extraction
```json
{
  "file_path": "library/xxx.json",
  "test_id": "test_001"
}
```

### POST /api/save-golden
```json
{
  "test_id": "test_001",
  "golden_data": {...},
  "metadata": {
    "source_file": "sheet.pdf",
    "corrections": ["key", "tempo"],
    "notes": "User corrections..."
  }
}
```

### GET /api/test-cases
Returns list of all test cases with metadata

### GET /api/golden-data/{test_id}
Returns golden data for a test case

## Integration Points

1. **EvaluationSystem** - Add method to load golden data
2. **test_extraction_performance.py** - Use golden data as expected data
3. **main.py** - Add flag to generate golden data after extraction

