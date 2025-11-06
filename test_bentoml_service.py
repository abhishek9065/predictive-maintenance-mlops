"""
Test BentoML Service
Tests the predictive maintenance service
"""

import requests
import time
import json

# Configuration
BASE_URL = "http://localhost:3000"

def wait_for_service(max_attempts=30):
    """Wait for BentoML service to be ready"""
    print("⏳ Waiting for BentoML service to start...")
    
    for i in range(max_attempts):
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=2)
            if response.status_code == 200:
                print(f"✅ Service is ready!")
                return True
        except:
            pass
        
        print(f"   Attempt {i+1}/{max_attempts}...")
        time.sleep(2)
    
    print("❌ Service failed to start")
    return False

def test_health():
    """Test health endpoint"""
    print("\n" + "="*80)
    print("  🏥 TESTING HEALTH ENDPOINT")
    print("="*80)
    
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Health Check Passed")
            print(f"   Status: {data.get('status')}")
            print(f"   Service: {data.get('service')}")
            print(f"   Model Version: {data.get('model_version')}")
            print(f"   Framework: {data.get('framework')}")
            print(f"   Model Tag: {data.get('model_tag')}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_model_info():
    """Test model info endpoint"""
    print("\n" + "="*80)
    print("  ℹ️  TESTING MODEL INFO ENDPOINT")
    print("="*80)
    
    try:
        response = requests.get(f"{BASE_URL}/model_info")
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Model Info Retrieved")
            print(f"   Tag: {data.get('tag')}")
            print(f"   Framework: {data.get('framework')}")
            
            metadata = data.get('metadata', {})
            if metadata:
                print(f"\n   📊 Metrics:")
                print(f"      Accuracy: {metadata.get('accuracy', 0)*100:.2f}%")
                print(f"      Precision: {metadata.get('precision', 0)*100:.2f}%")
                print(f"      Recall: {metadata.get('recall', 0)*100:.2f}%")
                print(f"      F1 Score: {metadata.get('f1_score', 0)*100:.2f}%")
            
            return True
        else:
            print(f"❌ Model info failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_predict_normal():
    """Test prediction with normal data"""
    print("\n" + "="*80)
    print("  ✅ TESTING NORMAL OPERATION PREDICTION")
    print("="*80)
    
    sensor_data = {
        "temperature": 72.0,
        "vibration": 0.35,
        "pressure": 95.0,
        "rpm": 1450.0,
        "current": 8.5
    }
    
    print(f"\n📊 Sensor Data:")
    for key, value in sensor_data.items():
        print(f"   {key}: {value}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/predict",
            json=sensor_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Prediction: {data.get('prediction').upper()}")
            print(f"   Confidence: {data.get('confidence')*100:.2f}%")
            print(f"   Probability Normal: {data.get('probability_normal')*100:.2f}%")
            print(f"   Probability Failure: {data.get('probability_failure')*100:.2f}%")
            return True
        else:
            print(f"❌ Prediction failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_predict_failure():
    """Test prediction with failure data"""
    print("\n" + "="*80)
    print("  🔴 TESTING FAILURE DETECTION")
    print("="*80)
    
    sensor_data = {
        "temperature": 105.0,
        "vibration": 2.5,
        "pressure": 88.0,
        "rpm": 1550.0,
        "current": 15.0
    }
    
    print(f"\n📊 Sensor Data (Failure Condition):")
    for key, value in sensor_data.items():
        print(f"   {key}: {value}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/predict",
            json=sensor_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            icon = "🔴" if data.get('prediction') == 'failure' else "🟢"
            print(f"\n{icon} Prediction: {data.get('prediction').upper()}")
            print(f"   Confidence: {data.get('confidence')*100:.2f}%")
            print(f"   Probability Normal: {data.get('probability_normal')*100:.2f}%")
            print(f"   Probability Failure: {data.get('probability_failure')*100:.2f}%")
            return True
        else:
            print(f"❌ Prediction failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_batch_predict():
    """Test batch prediction"""
    print("\n" + "="*80)
    print("  📦 TESTING BATCH PREDICTION")
    print("="*80)
    
    batch_data = {
        "data": [
            {"temperature": 72.0, "vibration": 0.35, "pressure": 95.0, "rpm": 1450.0, "current": 8.5},
            {"temperature": 105.0, "vibration": 2.5, "pressure": 88.0, "rpm": 1550.0, "current": 15.0},
            {"temperature": 70.0, "vibration": 0.30, "pressure": 96.0, "rpm": 1440.0, "current": 8.0},
            {"temperature": 95.0, "vibration": 1.8, "pressure": 90.0, "rpm": 1520.0, "current": 12.5},
        ]
    }
    
    print(f"\n📊 Testing {len(batch_data['data'])} samples...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/predict_batch",
            json=batch_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Batch Prediction Complete!")
            
            summary = data.get('summary', {})
            print(f"\n📈 Summary:")
            print(f"   Total Samples: {summary.get('total_samples')}")
            print(f"   Failures Detected: {summary.get('failures_detected')}")
            print(f"   Normal Operations: {summary.get('normal_operations')}")
            print(f"   Failure Rate: {summary.get('failure_rate')*100:.1f}%")
            
            print(f"\n📋 Predictions:")
            for pred in data.get('predictions', []):
                icon = "🔴" if pred['prediction'] == 'failure' else "🟢"
                print(f"   {icon} Sample {pred['index']}: {pred['prediction'].upper()} (confidence: {pred['confidence']*100:.1f}%)")
            
            return True
        else:
            print(f"❌ Batch prediction failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("  🧪 BENTOML SERVICE TESTING")
    print("="*80)
    print(f"  Service URL: {BASE_URL}")
    print("="*80)
    
    # Wait for service
    if not wait_for_service():
        print("\n❌ Service is not available. Please start BentoML service:")
        print("   bentoml serve service:PredictiveMaintenanceService --port 3000")
        return
    
    # Run tests
    tests = [
        ("Health Check", test_health),
        ("Model Info", test_model_info),
        ("Normal Prediction", test_predict_normal),
        ("Failure Detection", test_predict_failure),
        ("Batch Prediction", test_batch_predict),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"\n❌ Test '{name}' crashed: {e}")
            results.append((name, False))
        
        time.sleep(1)
    
    # Summary
    print("\n" + "="*80)
    print("  📊 TEST SUMMARY")
    print("="*80)
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status} - {name}")
    
    print("\n" + "-"*80)
    print(f"  Total: {passed_count}/{total_count} tests passed ({passed_count/total_count*100:.1f}%)")
    print("="*80)
    
    if passed_count == total_count:
        print("\n🎉 All tests passed! BentoML service is fully operational!")
    else:
        print(f"\n⚠️  {total_count - passed_count} test(s) failed. Please review the errors above.")

if __name__ == "__main__":
    main()
