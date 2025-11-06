"""
Real-World Production Testing
Simulates real sensor data and tests the production API
"""

import requests
import time
import random
import pandas as pd
from datetime import datetime
from pathlib import Path

# Configuration
API_BASE_URL = "http://localhost:8001"  # Production API base URL
API_URL = API_BASE_URL  # Alias for compatibility

def print_header(text):
    print("\n" + "="*80)
    print(f"  {text}")
    print("="*80 + "\n")

def check_api_health():
    """Check if API is healthy"""
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API Status: {data['status'].upper()}")
            print(f"   Model Loaded: {data['model_loaded']}")
            print(f"   Uptime: {data['uptime_seconds']:.1f}s")
            print(f"   Predictions Made: {data['total_predictions']}")
            return True
        else:
            print(f"❌ API Health Check Failed: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to API: {e}")
        print(f"\n💡 Make sure to start the API server:")
        print(f"   python production_api.py")
        return False

def test_normal_operation():
    """Test with normal operating conditions"""
    print_header("TEST 1: NORMAL OPERATION")
    
    normal_data = {
        "temperature": 72.0,
        "vibration": 0.35,
        "pressure": 95.0,
        "rpm": 1450.0,
        "current": 8.5
    }
    
    print("📊 Sensor Data (Normal Conditions):")
    for key, value in normal_data.items():
        print(f"   {key}: {value}")
    
    try:
        start = time.time()
        response = requests.post(f"{API_URL}/predict", json=normal_data, timeout=5)
        elapsed = (time.time() - start) * 1000
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ Prediction: {result['prediction']}")
            print(f"   Confidence: {result['probability']:.2%}")
            print(f"   Response Time: {elapsed:.2f}ms")
            return result['prediction'] == 'NORMAL'
        else:
            print(f"❌ Prediction Failed: HTTP {response.status_code}")
            print(f"   {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_failure_condition():
    """Test with failure conditions"""
    print_header("TEST 2: FAILURE CONDITION (High Temperature + Vibration)")
    
    failure_data = {
        "temperature": 105.0,  # High temperature
        "vibration": 2.5,      # High vibration
        "pressure": 88.0,      # Low pressure
        "rpm": 1550.0,
        "current": 15.0        # High current
    }
    
    print("📊 Sensor Data (Failure Conditions):")
    for key, value in failure_data.items():
        print(f"   {key}: {value}")
    
    try:
        start = time.time()
        response = requests.post(f"{API_URL}/predict", json=failure_data, timeout=5)
        elapsed = (time.time() - start) * 1000
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ Prediction: {result['prediction']}")
            print(f"   Confidence: {result['probability']:.2%}")
            print(f"   Response Time: {elapsed:.2f}ms")
            return result['prediction'] == 'FAILURE'
        else:
            print(f"❌ Prediction Failed: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_batch_predictions():
    """Test batch predictions"""
    print_header("TEST 3: BATCH PREDICTIONS (Real Test Data)")
    
    # Load test data
    if not Path("data/test.csv").exists():
        print("⚠️  Test data not found, skipping batch test")
        return None
    
    df = pd.read_csv("data/test.csv")
    
    # Take 10 random samples
    samples = df.sample(10)
    
    batch_data = []
    for _, row in samples.iterrows():
        batch_data.append({
            "temperature": float(row['temperature']),
            "vibration": float(row['vibration']),
            "pressure": float(row['pressure']),
            "rpm": float(row['rpm']),
            "current": float(row['current'])
        })
    
    print(f"📊 Testing {len(batch_data)} samples from test dataset...")
    
    try:
        start = time.time()
        response = requests.post(f"{API_URL}/predict/batch", json=batch_data, timeout=10)
        elapsed = (time.time() - start) * 1000
        
        if response.status_code == 200:
            result = response.json()
            predictions = result['predictions']
            
            # Compare with actual
            actual = samples['failure'].values
            correct = sum(1 for i, pred in enumerate(predictions) 
                         if (pred == 'FAILURE' and actual[i] == 1) or 
                            (pred == 'NORMAL' and actual[i] == 0))
            
            accuracy = correct / len(predictions) * 100
            
            print(f"\n✅ Batch Prediction Complete!")
            print(f"   Samples: {len(predictions)}")
            print(f"   Correct: {correct}/{len(predictions)}")
            print(f"   Accuracy: {accuracy:.1f}%")
            print(f"   Total Time: {elapsed:.2f}ms")
            print(f"   Avg Time/Sample: {elapsed/len(predictions):.2f}ms")
            
            # Show sample results
            print(f"\n   Sample Results:")
            for i in range(min(5, len(predictions))):
                actual_label = "FAILURE" if actual[i] == 1 else "NORMAL"
                match = "✅" if predictions[i] == actual_label else "❌"
                print(f"   {match} Predicted: {predictions[i]:8s} | Actual: {actual_label:8s} | Conf: {result['probabilities'][i]:.2%}")
            
            return accuracy >= 80
        else:
            print(f"❌ Batch Prediction Failed: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_continuous_monitoring():
    """Simulate continuous real-time monitoring"""
    print_header("TEST 4: CONTINUOUS MONITORING (10 Samples)")
    
    print("🔄 Simulating real-time sensor stream...\n")
    
    results = []
    
    for i in range(10):
        # Generate realistic sensor data with some variation
        if random.random() < 0.3:  # 30% chance of anomaly
            # Anomalous conditions
            data = {
                "temperature": random.uniform(85, 110),
                "vibration": random.uniform(1.5, 3.0),
                "pressure": random.uniform(70, 90),
                "rpm": random.uniform(1400, 1600),
                "current": random.uniform(10, 20)
            }
        else:
            # Normal conditions
            data = {
                "temperature": random.uniform(65, 80),
                "vibration": random.uniform(0.2, 0.6),
                "pressure": random.uniform(90, 100),
                "rpm": random.uniform(1400, 1500),
                "current": random.uniform(7, 10)
            }
        
        try:
            response = requests.post(f"{API_URL}/predict", json=data, timeout=5)
            
            if response.status_code == 200:
                result = response.json()
                timestamp = datetime.now().strftime("%H:%M:%S")
                
                # Color code the output
                if result['prediction'] == 'FAILURE':
                    status = "🔴 ALERT"
                else:
                    status = "🟢 OK   "
                
                print(f"{timestamp} | {status} | Temp: {data['temperature']:5.1f}°C | "
                      f"Vib: {data['vibration']:.2f} | Conf: {result['probability']:.1%}")
                
                results.append(result)
            
            time.sleep(0.5)  # 2 samples per second
            
        except Exception as e:
            print(f"❌ Error at sample {i+1}: {e}")
    
    print(f"\n✅ Monitoring Complete: {len(results)} samples processed")
    
    failures = sum(1 for r in results if r['prediction'] == 'FAILURE')
    print(f"   Failures Detected: {failures}/{len(results)}")
    
    return len(results) == 10

def run_production_tests():
    """Run all production tests"""
    print("="*80)
    print("  PRODUCTION API - REAL-WORLD TESTING")
    print("="*80)
    print(f"\nTimestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"API URL: {API_URL}\n")
    
    # Check API health first
    if not check_api_health():
        return
    
    # Run tests
    tests_passed = 0
    tests_total = 0
    
    # Test 1: Normal operation
    tests_total += 1
    if test_normal_operation():
        tests_passed += 1
    
    # Test 2: Failure detection
    tests_total += 1
    if test_failure_condition():
        tests_passed += 1
    
    # Test 3: Batch predictions
    tests_total += 1
    result = test_batch_predictions()
    if result is not None and result:
        tests_passed += 1
    elif result is None:
        tests_total -= 1  # Don't count if skipped
    
    # Test 4: Continuous monitoring
    tests_total += 1
    if test_continuous_monitoring():
        tests_passed += 1
    
    # Summary
    print_header("TEST SUMMARY")
    
    pass_rate = (tests_passed / tests_total * 100) if tests_total > 0 else 0
    
    print(f"Total Tests: {tests_total}")
    print(f"✅ Passed:   {tests_passed}")
    print(f"❌ Failed:   {tests_total - tests_passed}")
    print(f"Pass Rate:   {pass_rate:.1f}%")
    
    if pass_rate >= 75:
        print(f"\n🎉 PRODUCTION API IS OPERATIONAL!")
    else:
        print(f"\n⚠️  Some tests failed - check API configuration")
    
    print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    run_production_tests()
