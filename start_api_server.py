"""
Start FastAPI Server Script
Run this to start the API server in the background
"""

import subprocess
import time
import requests

def start_server():
    """Start the FastAPI server"""
    print("="*80)
    print("  STARTING FASTAPI SERVER")
    print("="*80 + "\n")
    
    print("🚀 Starting server on http://localhost:8000...")
    print("   Press Ctrl+C to stop the server\n")
    
    # Start the server
    subprocess.run(["uvicorn", "src.deployment.api_fastapi:app", "--host", "0.0.0.0", "--port", "8000"])

if __name__ == "__main__":
    start_server()
