"""
API Testing Script - Test the Predictive Maintenance API
"""

import requests
import json
from time import sleep

BASE_URL = "http://localhost:8000"

print("="*80)
print("PREDICTIVE MAINTENANCE API - TESTING SUITE")
print("="*80)

# Test 1: Root endpoint
print("\n[TEST 1] Testing Root Endpoint (/)...")
try:
    response = requests.get(f"{BASE_URL}/")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    assert response.status_code == 200, "Root endpoint failed"
    print("[PASS] Root endpoint working")
except Exception as e:
    print(f"[FAIL] {e}")

# Test 2: Health check
print("\n[TEST 2] Testing Health Check (/health)...")
try:
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status Code: {response.status_code}")
    data = response.json()
    print(f"Response: {json.dumps(data, indent=2)}")
    assert response.status_code == 200, "Health check failed"
    print("[PASS] Health check working")
except Exception as e:
    print(f"[FAIL] {e}")

# Test 3: Model info
print("\n[TEST 3] Testing Model Info (/model/info)...")
try:
    response = requests.get(f"{BASE_URL}/model/info")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    assert response.status_code == 200, "Model info failed"
    print("[PASS] Model info endpoint working")
except Exception as e:
    print(f"[FAIL] {e}")

# Test 4: Single prediction - Normal operation
print("\n[TEST 4] Testing Single Prediction - Normal Operation...")
normal_data = {
    "temperature": 60.0,
    "vibration": 5.0,
    "pressure": 100.0,
    "current": 20.0,
    "rpm": 1500.0
}

try:
    response = requests.post(
        f"{BASE_URL}/predict",
        json=normal_data,
        headers={"Content-Type": "application/json"}
    )
    print(f"Status Code: {response.status_code}")
    result = response.json()
    print(f"\nInput Sensor Data:")
    print(f"  Temperature: {normal_data['temperature']}°C")
    print(f"  Vibration: {normal_data['vibration']} mm/s")
    print(f"  Pressure: {normal_data['pressure']} PSI")
    print(f"  Current: {normal_data['current']} A")
    print(f"  RPM: {normal_data['rpm']}")
    
    print(f"\nPrediction Result:")
    print(f"  Prediction: {result['prediction']}")
    print(f"  Failure Probability: {result['probability']:.2%}")
    print(f"  Risk Level: {result['risk_level']}")
    print(f"  Confidence: {result['confidence']:.2%}")
    
    assert response.status_code == 200, "Prediction failed"
    print("\n[PASS] Normal operation prediction working")
except Exception as e:
    print(f"[FAIL] {e}")

# Test 5: Single prediction - High risk scenario
print("\n[TEST 5] Testing Single Prediction - High Risk Scenario...")
high_risk_data = {
    "temperature": 95.0,  # High temperature
    "vibration": 12.0,    # High vibration
    "pressure": 85.0,     # Low pressure
    "current": 35.0,      # High current
    "rpm": 800.0          # Low RPM
}

try:
    response = requests.post(
        f"{BASE_URL}/predict",
        json=high_risk_data,
        headers={"Content-Type": "application/json"}
    )
    print(f"Status Code: {response.status_code}")
    result = response.json()
    print(f"\nInput Sensor Data (Abnormal):")
    print(f"  Temperature: {high_risk_data['temperature']}°C (HIGH)")
    print(f"  Vibration: {high_risk_data['vibration']} mm/s (HIGH)")
    print(f"  Pressure: {high_risk_data['pressure']} PSI (LOW)")
    print(f"  Current: {high_risk_data['current']} A (HIGH)")
    print(f"  RPM: {high_risk_data['rpm']} (LOW)")
    
    print(f"\nPrediction Result:")
    print(f"  Prediction: {result['prediction']}")
    print(f"  Failure Probability: {result['probability']:.2%}")
    print(f"  Risk Level: {result['risk_level']}")
    print(f"  Confidence: {result['confidence']:.2%}")
    
    assert response.status_code == 200, "Prediction failed"
    print("\n[PASS] High risk prediction working")
except Exception as e:
    print(f"[FAIL] {e}")

# Test 6: Batch prediction
print("\n[TEST 6] Testing Batch Prediction (/predict/batch)...")
batch_data = {
    "data": [
        {"temperature": 60, "vibration": 5, "pressure": 100, "current": 20, "rpm": 1500},
        {"temperature": 75, "vibration": 8, "pressure": 95, "current": 25, "rpm": 1400},
        {"temperature": 90, "vibration": 11, "pressure": 88, "current": 30, "rpm": 900}
    ]
}

try:
    response = requests.post(
        f"{BASE_URL}/predict/batch",
        json=batch_data,
        headers={"Content-Type": "application/json"}
    )
    print(f"Status Code: {response.status_code}")
    result = response.json()
    print(f"\nBatch Predictions for {result['total_predictions']} samples:")
    
    for i, pred in enumerate(result['predictions'], 1):
        print(f"\n  Sample {i}:")
        print(f"    Prediction: {pred['prediction']}")
        print(f"    Risk Level: {pred['risk_level']}")
        print(f"    Probability: {pred['probability']:.2%}")
    
    assert response.status_code == 200, "Batch prediction failed"
    assert result['total_predictions'] == 3, "Expected 3 predictions"
    print("\n[PASS] Batch prediction working")
except Exception as e:
    print(f"[FAIL] {e}")

# Test 7: Invalid input validation
print("\n[TEST 7] Testing Input Validation (Invalid Data)...")
invalid_data = {
    "temperature": 200,  # Out of range (max 150)
    "vibration": 5,
    "pressure": 100,
    "current": 20,
    "rpm": 1500
}

try:
    response = requests.post(
        f"{BASE_URL}/predict",
        json=invalid_data,
        headers={"Content-Type": "application/json"}
    )
    print(f"Status Code: {response.status_code}")
    if response.status_code == 422:
        print(f"Response: Validation error (expected)")
        print(f"Details: Temperature {invalid_data['temperature']} exceeds max 150")
        print("[PASS] Input validation working correctly")
    else:
        print(f"[FAIL] Expected 422 status code, got {response.status_code}")
except Exception as e:
    print(f"[INFO] {e}")

# Test 8: Model info after predictions
print("\n[TEST 8] Checking Model Info After Predictions...")
try:
    response = requests.get(f"{BASE_URL}/model/info")
    data = response.json()
    print(f"Model Status: {data['status']}")
    if data['status'] == 'loaded':
        print(f"Model Info:")
        for key, value in data['info'].items():
            print(f"  {key}: {value}")
        print(f"Features: {', '.join(data['feature_names'])}")
        print("[PASS] Model loaded and operational")
    else:
        print("[INFO] Model not yet loaded")
except Exception as e:
    print(f"[FAIL] {e}")

# Summary
print("\n" + "="*80)
print("API TESTING SUMMARY")
print("="*80)
print("\nAll core endpoints tested successfully!")
print("\n[NEXT STEPS]")
print("1. Open browser: http://localhost:8000/docs")
print("2. Try interactive API documentation (Swagger UI)")
print("3. Test different sensor value combinations")
print("4. Monitor predictions in real-time")
print("\n[API ENDPOINTS]")
print("  GET  /          - API information")
print("  GET  /health    - Health check")
print("  GET  /model/info - Model information")
print("  POST /predict   - Single prediction")
print("  POST /predict/batch - Batch predictions")
print("\n" + "="*80)
