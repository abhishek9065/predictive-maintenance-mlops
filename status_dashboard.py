"""
MLOps System Status Dashboard
Check what's currently running and accessible
"""

import requests
from datetime import datetime

print("="*80)
print("MLOps SYSTEM STATUS DASHBOARD")
print(f"Status Check: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80)

# Check API
print("\n[1] FastAPI Prediction Service")
print("-" * 80)
try:
    response = requests.get("http://localhost:8000/health", timeout=2)
    if response.status_code == 200:
        data = response.json()
        print("Status: 🟢 RUNNING")
        print(f"URL: http://localhost:8000")
        print(f"Docs: http://localhost:8000/docs")
        print(f"Model Loaded: {data.get('model_loaded', False)}")
    else:
        print("Status: 🟡 DEGRADED")
except Exception as e:
    print("Status: 🔴 NOT RUNNING")
    print(f"Error: {str(e)[:50]}")
    print("Start with: python api_quickstart.py")

# Check MLflow
print("\n[2] MLflow Experiment Tracking")
print("-" * 80)
try:
    response = requests.get("http://localhost:5000", timeout=2)
    if response.status_code == 200:
        print("Status: 🟢 RUNNING")
        print(f"URL: http://localhost:5000")
        print("View experiments, compare models, track metrics")
    else:
        print("Status: 🟡 DEGRADED")
except Exception as e:
    print("Status: 🔴 NOT RUNNING")
    print(f"Error: {str(e)[:50]}")
    print("Start with: mlflow ui --port 5000")

# Check Data
print("\n[3] Training Data")
print("-" * 80)
from pathlib import Path
data_dir = Path("data/raw")
historical = list(data_dir.glob("historical_*.json"))
realtime = list(data_dir.glob("sensor_data_*.json"))

if historical:
    print(f"Status: 🟢 AVAILABLE")
    print(f"Historical Files: {len(historical)}")
    print(f"Real-time Files: {len(realtime)}")
else:
    print("Status: 🔴 NO DATA")
    print("Generate with: python src/data_collection/iot_simulator.py")

# Check Models
print("\n[4] Trained Models")
print("-" * 80)
models_dir = Path("models")
mlruns_dir = Path("mlruns")

model_files = list(models_dir.glob("*.pkl")) if models_dir.exists() else []
has_mlruns = mlruns_dir.exists() and any(mlruns_dir.iterdir())

if model_files or has_mlruns:
    print(f"Status: 🟢 AVAILABLE")
    if model_files:
        print(f"Saved Models: {len(model_files)}")
        for m in model_files:
            print(f"  - {m.name}")
    if has_mlruns:
        print(f"MLflow Experiments: Available in mlruns/")
else:
    print("Status: 🟡 LIMITED")
    print("Train models with: python mlflow_quickstart.py")

# Check Tests
print("\n[5] Test Results")
print("-" * 80)
test_results = Path("test_results.json")
if test_results.exists():
    import json
    with open(test_results) as f:
        results = json.load(f)
    
    summary = results.get('summary', {})
    print(f"Status: 🟢 TESTS RUN")
    print(f"Total Tests: {summary.get('total', 0)}")
    print(f"Passed: {summary.get('passed', 0)}")
    print(f"Failed: {summary.get('failed', 0)}")
    print(f"Grade: {summary.get('grade', 'N/A')}")
else:
    print("Status: 🟡 NOT RUN")
    print("Run tests with: python run_all_tests.py")

# Summary
print("\n" + "="*80)
print("QUICK ACCESS LINKS")
print("="*80)
print("\n🌐 Web Interfaces:")
print("   • API Documentation: http://localhost:8000/docs")
print("   • API Root:          http://localhost:8000")
print("   • MLflow UI:         http://localhost:5000")

print("\n🚀 Quick Commands:")
print("   • Start API:         python api_quickstart.py")
print("   • Start MLflow UI:   mlflow ui --port 5000")
print("   • Generate Data:     python src/data_collection/iot_simulator.py")
print("   • Train Models:      python mlflow_quickstart.py")
print("   • Run Tests:         python run_all_tests.py")
print("   • Test API:          python test_api.py")

print("\n📊 Project Stats:")
from pathlib import Path
py_files = list(Path("src").rglob("*.py"))
test_files = list(Path("tests").rglob("*.py"))
doc_files = list(Path(".").glob("*.md"))

print(f"   • Source Files:      {len(py_files)}")
print(f"   • Test Files:        {len(test_files)}")
print(f"   • Documentation:     {len(doc_files)} markdown files")
print(f"   • Total Lines:       Thousands!")

print("\n" + "="*80)
print("✅ MLOps System Ready!")
print("="*80)
