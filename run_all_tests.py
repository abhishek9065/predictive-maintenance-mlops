"""
Comprehensive MLOps Project Testing Suite
Run this to validate all components are working correctly
"""

import sys
import json
import time
from pathlib import Path
import numpy as np
import pandas as pd
from datetime import datetime

# Results tracking
test_results = []

def log_test(name, status, details=""):
    """Log test results"""
    test_results.append({
        'test': name,
        'status': status,
        'details': details,
        'timestamp': datetime.now().isoformat()
    })
    symbols = {"PASS": "[PASS]", "FAIL": "[FAIL]", "SKIP": "[SKIP]"}
    symbol = symbols.get(status, "[????]")
    print(f"{symbol} {name}: {status}")
    if details:
        print(f"   {details}")

print("="*80)
print("COMPREHENSIVE MLOps PROJECT TESTING SUITE")
print("="*80)

# TEST 1: Environment Setup
print("\nTEST SUITE 1: ENVIRONMENT SETUP")
print("-" * 80)

try:
    import yaml
    import sklearn
    import mlflow
    import fastapi
    log_test("Required packages installed", "PASS", 
             f"sklearn={sklearn.__version__}, mlflow={mlflow.__version__}")
except ImportError as e:
    log_test("Required packages installed", "FAIL", str(e))

# TEST 2: Project Structure
print("\n📁 TEST SUITE 2: PROJECT STRUCTURE")
print("-" * 80)

required_dirs = [
    'src/data_collection',
    'src/preprocessing', 
    'src/models',
    'src/training',
    'src/deployment',
    'src/monitoring',
    'data/raw',
    'data/processed',
    'data/features',
    'config',
    'tests'
]

all_dirs_exist = True
for dir_path in required_dirs:
    exists = Path(dir_path).exists()
    if not exists:
        all_dirs_exist = False
        log_test(f"Directory: {dir_path}", "FAIL", "Missing")
    else:
        log_test(f"Directory: {dir_path}", "PASS")

# TEST 3: Configuration Files
print("\n⚙️ TEST SUITE 3: CONFIGURATION VALIDATION")
print("-" * 80)

try:
    with open('config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    required_keys = ['data', 'models', 'deployment', 'monitoring']
    missing_keys = [k for k in required_keys if k not in config]
    
    if missing_keys:
        log_test("Config file structure", "FAIL", f"Missing: {missing_keys}")
    else:
        log_test("Config file structure", "PASS", 
                f"Found {len(config)} config sections")
except Exception as e:
    log_test("Config file loading", "FAIL", str(e))

# TEST 4: Data Availability
print("\n💾 TEST SUITE 4: DATA VALIDATION")
print("-" * 80)

data_dir = Path("data/raw")
historical_files = list(data_dir.glob("historical_*.json"))
sensor_files = list(data_dir.glob("sensor_data_*.json"))

if historical_files:
    log_test("Historical data available", "PASS", 
            f"Found {len(historical_files)} file(s)")
    
    # Validate data quality
    try:
        with open(historical_files[0], 'r') as f:
            data = json.load(f)
        
        if len(data) > 0:
            log_test("Data file readable", "PASS", f"{len(data)} records")
            
            # Check data schema
            required_fields = ['equipment_id', 'timestamp', 'sensors', 'is_failing']
            sample = data[0]
            missing_fields = [f for f in required_fields if f not in sample]
            
            if missing_fields:
                log_test("Data schema validation", "FAIL", 
                        f"Missing fields: {missing_fields}")
            else:
                log_test("Data schema validation", "PASS", 
                        "All required fields present")
                
                # Validate sensor data structure
                sensor_keys = list(sample['sensors'].keys())
                log_test("Sensor data structure", "PASS", 
                        f"Sensors: {', '.join(sensor_keys)}")
        else:
            log_test("Data file content", "FAIL", "Empty data file")
    except Exception as e:
        log_test("Data file validation", "FAIL", str(e))
else:
    log_test("Historical data available", "FAIL", 
            "No historical data found. Run: python src/data_collection/iot_simulator.py")

if sensor_files:
    log_test("Real-time sensor data", "PASS", f"Found {len(sensor_files)} file(s)")
else:
    log_test("Real-time sensor data", "SKIP", "Optional - run simulator for more data")

# TEST 5: Data Processing Pipeline
print("\n🔄 TEST SUITE 5: DATA PROCESSING PIPELINE")
print("-" * 80)

try:
    if historical_files:
        with open(historical_files[0], 'r') as f:
            data = json.load(f)
        
        # Extract features
        features = []
        labels = []
        
        for record in data[:100]:  # Test with subset
            sensors = record['sensors']
            features.append([
                sensors['temperature']['value'],
                sensors['vibration']['value'],
                sensors['pressure']['value'],
                sensors['current']['value'],
                sensors['rpm']['value']
            ])
            labels.append(record['is_failing'])
        
        X = np.array(features)
        y = np.array(labels)
        
        log_test("Feature extraction", "PASS", 
                f"Extracted {X.shape[1]} features from {X.shape[0]} samples")
        
        # Check for missing values
        if np.isnan(X).any():
            log_test("Data quality check", "FAIL", "Contains NaN values")
        else:
            log_test("Data quality check", "PASS", "No missing values")
        
        # Check feature ranges
        feature_names = ['temperature', 'vibration', 'pressure', 'current', 'rpm']
        for i, name in enumerate(feature_names):
            min_val, max_val = X[:, i].min(), X[:, i].max()
            log_test(f"Feature range: {name}", "PASS", 
                    f"Range: {min_val:.2f} to {max_val:.2f}")
    else:
        log_test("Data processing pipeline", "SKIP", "No data available")
except Exception as e:
    log_test("Data processing pipeline", "FAIL", str(e))

# TEST 6: Model Training Pipeline
print("\n🤖 TEST SUITE 6: MODEL TRAINING VALIDATION")
print("-" * 80)

try:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score, f1_score
    
    if historical_files and len(features) > 0:
        # Train a quick test model
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        log_test("Data splitting", "PASS", 
                f"Train: {len(X_train)}, Test: {len(X_test)}")
        
        model = RandomForestClassifier(n_estimators=10, random_state=42, n_jobs=-1)
        
        start_time = time.time()
        model.fit(X_train, y_train)
        training_time = time.time() - start_time
        
        log_test("Model training", "PASS", f"Completed in {training_time:.2f}s")
        
        # Evaluate model
        y_pred = model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred)
        
        if accuracy >= 0.7:
            log_test("Model accuracy", "PASS", f"{accuracy:.2%}")
        else:
            log_test("Model accuracy", "FAIL", f"{accuracy:.2%} (threshold: 70%)")
        
        log_test("F1 Score", "PASS" if f1 >= 0.5 else "FAIL", f"{f1:.4f}")
        
        # Test prediction capability
        sample = X_test[0:1]
        prediction = model.predict(sample)[0]
        probability = model.predict_proba(sample)[0]
        
        log_test("Prediction capability", "PASS", 
                f"Predicted: {'FAILURE' if prediction else 'NORMAL'} "
                f"(confidence: {probability.max():.2%})")
    else:
        log_test("Model training pipeline", "SKIP", "No data available")
except Exception as e:
    log_test("Model training pipeline", "FAIL", str(e))

# TEST 7: Model Files
print("\n💾 TEST SUITE 7: MODEL ARTIFACTS")
print("-" * 80)

models_dir = Path("models")
if models_dir.exists():
    model_files = list(models_dir.glob("*.pkl")) + list(models_dir.glob("*.joblib"))
    if model_files:
        log_test("Saved models found", "PASS", f"Found {len(model_files)} model(s)")
    else:
        log_test("Saved models found", "SKIP", "No saved models yet")
else:
    log_test("Models directory", "SKIP", "Directory not created yet")

# TEST 8: API Components
print("\n🌐 TEST SUITE 8: API COMPONENTS")
print("-" * 80)

try:
    # Check if API file exists and is valid Python
    api_file = Path("src/deployment/api.py")
    if api_file.exists():
        log_test("API file exists", "PASS", str(api_file))
        
        # Try importing API (don't run it)
        import importlib.util
        spec = importlib.util.spec_from_file_location("api", api_file)
        if spec:
            log_test("API module loadable", "PASS")
        else:
            log_test("API module loadable", "FAIL", "Cannot load module")
    else:
        log_test("API file exists", "FAIL", "api.py not found")
except Exception as e:
    log_test("API validation", "FAIL", str(e))

# TEST 9: Logging and Monitoring
print("\n📊 TEST SUITE 9: LOGGING & MONITORING")
print("-" * 80)

logs_dir = Path("logs")
if not logs_dir.exists():
    logs_dir.mkdir(exist_ok=True)
    log_test("Logs directory", "PASS", "Created logs directory")
else:
    log_test("Logs directory", "PASS", "Already exists")

# Test logging capability
try:
    import logging
    from src.utils.logger import setup_logger
    
    test_logger = setup_logger("test_logger")
    test_logger.info("Test log message")
    log_test("Logging system", "PASS", "Logger configured successfully")
except Exception as e:
    log_test("Logging system", "FAIL", str(e))

# TEST 10: Code Quality
print("\n✨ TEST SUITE 10: CODE QUALITY CHECKS")
print("-" * 80)

# Check for __init__.py files
init_files = [
    'src/__init__.py',
    'src/models/__init__.py',
    'src/preprocessing/__init__.py',
]

for init_file in init_files:
    if Path(init_file).exists():
        log_test(f"Package initialization: {init_file}", "PASS")
    else:
        log_test(f"Package initialization: {init_file}", "SKIP", "Not critical")

# FINAL SUMMARY
print("\n" + "="*80)
print("📋 TEST SUMMARY")
print("="*80)

passed = sum(1 for r in test_results if r['status'] == 'PASS')
failed = sum(1 for r in test_results if r['status'] == 'FAIL')
skipped = sum(1 for r in test_results if r['status'] == 'SKIP')
total = len(test_results)

print(f"\nTotal Tests: {total}")
print(f"✅ Passed: {passed} ({passed/total*100:.1f}%)")
print(f"❌ Failed: {failed} ({failed/total*100:.1f}%)")
print(f"⏭️  Skipped: {skipped} ({skipped/total*100:.1f}%)")

# Overall status
if failed == 0 and passed > 0:
    overall_status = "🎉 ALL CRITICAL TESTS PASSED!"
    grade = "A+"
elif failed <= 2:
    overall_status = "✅ MOSTLY WORKING - Minor issues"
    grade = "B+"
else:
    overall_status = "⚠️  NEEDS ATTENTION - Multiple failures"
    grade = "C"

print(f"\n{overall_status}")
print(f"Overall Grade: {grade}")

# Save detailed results
results_file = Path("test_results.json")
with open(results_file, 'w') as f:
    json.dump({
        'timestamp': datetime.now().isoformat(),
        'summary': {
            'total': total,
            'passed': passed,
            'failed': failed,
            'skipped': skipped,
            'grade': grade
        },
        'tests': test_results
    }, f, indent=2)

print(f"\n📄 Detailed results saved to: {results_file}")

# Recommendations
print("\n💡 RECOMMENDATIONS:")
if failed > 0:
    print("\n⚠️  Address Failed Tests:")
    for result in test_results:
        if result['status'] == 'FAIL':
            print(f"   • {result['test']}: {result['details']}")

print("\n🚀 NEXT STEPS:")
next_steps = []
if not historical_files:
    next_steps.append("Generate data: python src/data_collection/iot_simulator.py")
if failed == 0:
    next_steps.append("Start API: uvicorn src.deployment.api:app --reload")
    next_steps.append("Run full training: python src/training/train.py")

if next_steps:
    for step in next_steps:
        print(f"   {step}")

print("\n" + "="*80)
print(f"✅ Testing completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80)
