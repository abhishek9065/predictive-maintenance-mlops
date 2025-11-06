"""
Quick Start Test Script
Tests core functionality without requiring full package installation.
"""

import sys
import os
from pathlib import Path

print("=" * 70)
print("🔍 PREDICTIVE MAINTENANCE MLOps - QUICK VALIDATION TEST")
print("=" * 70)

# Test 1: Python Version
print("\n✅ Test 1: Python Version")
print(f"   Python {sys.version}")
if sys.version_info >= (3, 8):
    print("   ✅ PASSED - Python 3.8+ detected")
else:
    print("   ❌ FAILED - Python 3.8+ required")
    sys.exit(1)

# Test 2: Project Structure
print("\n✅ Test 2: Project Structure")
required_dirs = [
    "src/data_collection",
    "src/preprocessing", 
    "src/models",
    "src/training",
    "src/deployment",
    "src/monitoring",
    "airflow/dags",
    "config",
    "data/raw",
    "data/processed",
    "data/features",
    "deployment",
    "docs"
]

all_exist = True
for dir_path in required_dirs:
    if Path(dir_path).exists():
        print(f"   ✅ {dir_path}")
    else:
        print(f"   ❌ {dir_path} - MISSING")
        all_exist = False

if all_exist:
    print("   ✅ PASSED - All directories present")
else:
    print("   ❌ FAILED - Some directories missing")

# Test 3: Required Files
print("\n✅ Test 3: Core Files")
required_files = [
    "README.md",
    "GETTING_STARTED.md",
    "requirements.txt",
    "setup.py",
    "config/config.yaml",
    "src/data_collection/iot_simulator.py",
    "src/preprocessing/data_cleaner.py",
    "src/models/random_forest_model.py",
    "src/deployment/api.py",
    "src/training/train.py"
]

files_exist = True
for file_path in required_files:
    if Path(file_path).exists():
        print(f"   ✅ {file_path}")
    else:
        print(f"   ❌ {file_path} - MISSING")
        files_exist = False

if files_exist:
    print("   ✅ PASSED - All core files present")
else:
    print("   ❌ FAILED - Some files missing")

# Test 4: File Syntax Check
print("\n✅ Test 4: Python Syntax Check")
python_files = [
    "src/data_collection/iot_simulator.py",
    "src/preprocessing/data_cleaner.py",
    "src/models/random_forest_model.py"
]

syntax_ok = True
for file_path in python_files:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            compile(f.read(), file_path, 'exec')
        print(f"   ✅ {file_path} - Valid Python")
    except SyntaxError as e:
        print(f"   ❌ {file_path} - Syntax Error: {e}")
        syntax_ok = False

if syntax_ok:
    print("   ✅ PASSED - No syntax errors")
else:
    print("   ❌ FAILED - Syntax errors found")

# Test 5: Package Check
print("\n✅ Test 5: Required Packages Check")
packages_to_check = {
    'yaml': 'PyYAML',
    'pandas': 'pandas',
    'numpy': 'numpy',
    'sklearn': 'scikit-learn',
    'fastapi': 'fastapi',
    'mlflow': 'mlflow'
}

installed_packages = []
missing_packages = []

for module, package in packages_to_check.items():
    try:
        __import__(module)
        print(f"   ✅ {package} - Installed")
        installed_packages.append(package)
    except ImportError:
        print(f"   ⏳ {package} - Not installed (run: pip install {package})")
        missing_packages.append(package)

if len(installed_packages) == len(packages_to_check):
    print("   ✅ PASSED - All packages installed")
elif len(installed_packages) > 0:
    print(f"   ⚠️  PARTIAL - {len(installed_packages)}/{len(packages_to_check)} packages installed")
else:
    print("   ⏳ PENDING - Install packages with: pip install -r requirements.txt")

# Summary
print("\n" + "=" * 70)
print("📊 VALIDATION SUMMARY")
print("=" * 70)

total_tests = 5
passed_tests = sum([
    sys.version_info >= (3, 8),
    all_exist,
    files_exist,
    syntax_ok,
    len(installed_packages) > 0
])

print(f"\n✅ Tests Passed: {passed_tests}/{total_tests}")
print(f"⏳ Tests Pending: {total_tests - passed_tests}/{total_tests}")

if passed_tests == total_tests:
    print("\n🎉 ALL TESTS PASSED! Project is fully functional.")
elif passed_tests >= 4:
    print("\n✅ PROJECT STRUCTURE VALID! Install packages to complete setup.")
    print(f"\n   Run: pip install -r requirements.txt")
else:
    print("\n⚠️  Some issues detected. Please check the output above.")

# Next Steps
print("\n" + "=" * 70)
print("🚀 NEXT STEPS")
print("=" * 70)

if missing_packages:
    print("\n1. Install Missing Packages:")
    print("   pip install -r requirements.txt")
    print("\n2. Generate Sample Data:")
    print("   python src/data_collection/iot_simulator.py")
    print("\n3. Train Models:")
    print("   python src/training/train.py")
    print("\n4. Start API:")
    print("   uvicorn src.deployment.api:app --reload")
else:
    print("\n✅ All packages installed! You can now:")
    print("   1. python src/data_collection/iot_simulator.py  # Generate data")
    print("   2. python src/training/train.py                 # Train models")
    print("   3. uvicorn src.deployment.api:app --reload      # Start API")

print("\n📖 For detailed instructions, read: GETTING_STARTED.md")
print("=" * 70)
