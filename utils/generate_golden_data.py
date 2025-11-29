#!/usr/bin/env python3
"""
Golden Data Generator CLI Tool
Starts the web server for human-in-the-loop golden data generation
"""

import argparse
import os
import sys
import webbrowser
import time
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(
        description="Golden Data Generator - Human-in-the-Loop Evaluation Tool"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to run the server on (default: 8000)"
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind to (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Don't open browser automatically"
    )
    parser.add_argument(
        "--extraction",
        help="Path to extracted JSON file to load initially"
    )
    parser.add_argument(
        "--test-id",
        help="Test case ID (e.g., test_001)"
    )
    
    args = parser.parse_args()
    
    # Check if FastAPI is installed
    try:
        import uvicorn
        from fastapi import FastAPI
    except ImportError:
        print("Error: FastAPI and uvicorn are required.")
        print("Install with: pip install fastapi uvicorn")
        sys.exit(1)
    
    # Import the server
    try:
        from tools.golden_data_server import app
    except ImportError as e:
        print(f"Error importing server: {e}")
        print("Make sure you're running from the project root directory")
        sys.exit(1)
    
    # Build URL
    url = f"http://{args.host}:{args.port}"
    
    # Add query parameters if extraction file provided
    if args.extraction:
        url += f"?extraction={args.extraction}"
        if args.test_id:
            url += f"&test_id={args.test_id}"
    
    print("=" * 80)
    print("Golden Data Generator - ScoreOrchestrator")
    print("=" * 80)
    print(f"\nStarting server on {url}")
    print(f"\nFeatures:")
    print("  - Play extracted music JSON")
    print("  - Edit and correct JSON")
    print("  - Save as golden test data")
    print("  - Compare extracted vs golden")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 80)
    
    # Open browser after a short delay
    if not args.no_browser:
        def open_browser():
            time.sleep(1.5)
            webbrowser.open(url)
        
        import threading
        threading.Thread(target=open_browser, daemon=True).start()
    
    # Run the server
    try:
        uvicorn.run(
            app,
            host=args.host,
            port=args.port,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n\nServer stopped.")
        sys.exit(0)


if __name__ == "__main__":
    main()

