"""
FastAPI Server for Golden Data Generator
Serves the React music player and provides API for golden data management
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from tools.golden_data_manager import GoldenDataManager

app = FastAPI(title="Golden Data Generator", version="1.0.0")

# CORS middleware for React app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize golden data manager
golden_manager = GoldenDataManager()


# Pydantic models for API
class LoadExtractionRequest(BaseModel):
    file_path: str
    test_id: Optional[str] = None


class SaveGoldenRequest(BaseModel):
    test_id: str
    golden_data: Dict[str, Any]
    corrections: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None


class CreateTestCaseRequest(BaseModel):
    test_id: str
    source_file: str
    extracted_data: Dict[str, Any]
    description: Optional[str] = None


# API Endpoints
@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the React music player HTML."""
    html_file = Path("web/index.html")
    if html_file.exists():
        return FileResponse(html_file)
    
    # Fallback HTML if file doesn't exist
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Golden Data Generator - ScoreOrchestrator</title>
    <script crossorigin src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
    <script crossorigin src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
    <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
    <script src="https://unpkg.com/lucide-react@latest/dist/umd/lucide-react.js"></script>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { margin: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif; }
    </style>
</head>
<body>
    <div id="root"></div>
    <script type="text/babel" src="/static/golden_data_player.jsx"></script>
</body>
</html>
    """
    return HTMLResponse(content=html_content)


@app.post("/api/load-extraction")
async def load_extraction(request: LoadExtractionRequest):
    """Load extracted JSON data."""
    try:
        if not os.path.exists(request.file_path):
            raise HTTPException(status_code=404, detail=f"File not found: {request.file_path}")
        
        with open(request.file_path, 'r') as f:
            extracted_data = json.load(f)
        
        # Create test case if test_id provided
        if request.test_id:
            metadata = golden_manager.create_test_case(
                test_id=request.test_id,
                source_file=request.file_path,
                extracted_data=extracted_data
            )
            return {
                "status": "success",
                "extracted_data": extracted_data,
                "test_id": request.test_id,
                "metadata": metadata
            }
        
        return {
            "status": "success",
            "extracted_data": extracted_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/save-golden")
async def save_golden(request: SaveGoldenRequest):
    """Save golden (corrected) data."""
    try:
        metadata = golden_manager.save_golden_data(
            test_id=request.test_id,
            golden_data=request.golden_data,
            corrections=request.corrections,
            notes=request.notes
        )
        
        return {
            "status": "success",
            "test_id": request.test_id,
            "metadata": metadata
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/test-cases")
async def list_test_cases():
    """List all test cases."""
    test_cases = golden_manager.list_test_cases()
    return {
        "status": "success",
        "test_cases": test_cases,
        "count": len(test_cases)
    }


@app.get("/api/test-case/{test_id}")
async def get_test_case(test_id: str):
    """Get test case with extracted and golden data."""
    test_case = golden_manager.get_test_case(test_id)
    if not test_case:
        raise HTTPException(status_code=404, detail=f"Test case {test_id} not found")
    
    return {
        "status": "success",
        "test_case": test_case
    }


@app.get("/api/golden-data/{test_id}")
async def get_golden_data(test_id: str):
    """Get golden data for a test case."""
    golden_data = golden_manager.get_golden_data(test_id)
    if not golden_data:
        raise HTTPException(status_code=404, detail=f"Golden data not found for {test_id}")
    
    return {
        "status": "success",
        "golden_data": golden_data
    }


@app.get("/api/extracted-data/{test_id}")
async def get_extracted_data(test_id: str):
    """Get extracted data for a test case."""
    extracted_data = golden_manager.get_extracted_data(test_id)
    if not extracted_data:
        raise HTTPException(status_code=404, detail=f"Extracted data not found for {test_id}")
    
    return {
        "status": "success",
        "extracted_data": extracted_data
    }


@app.post("/api/create-test-case")
async def create_test_case(request: CreateTestCaseRequest):
    """Create a new test case."""
    try:
        metadata = golden_manager.create_test_case(
            test_id=request.test_id,
            source_file=request.source_file,
            extracted_data=request.extracted_data,
            description=request.description
        )
        
        return {
            "status": "success",
            "test_case": metadata
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/compare/{test_id}")
async def compare_data(test_id: str):
    """Compare extracted vs golden data."""
    comparison = golden_manager.compare_extracted_vs_golden(test_id)
    return {
        "status": "success",
        "comparison": comparison
    }


# Serve static files (React component)
static_dir = Path("web")
if static_dir.exists():
    app.mount("/static", StaticFiles(directory="web"), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

