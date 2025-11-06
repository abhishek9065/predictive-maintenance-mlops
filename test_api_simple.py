"""
Simple API Tester - Cross-platform (Windows/Linux/Mac)
Tests the FastAPI server endpoints
"""

import requests
import json

def test_endpoint(name, method, url, data=None):
    """Test an API endpoint"""
    print(f"\nTesting {name}...")
    try:
        if method == "GET":
            response = requests.get(url, timeout=5)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=5)
        
        print(f"✅ Status: {response.status_code}")
        
        if response.headers.get('content-type', '').startswith('application/json'):
            print("Response:")
            print(json.dumps(response.json(), indent=2))
        else:
            print("Response (first 200 chars):")
            print(response.text[:200])
        
        return True
    except requests.exceptions.ConnectionError:
        print("❌ Error: Cannot connect to server")
        print("💡 Start server with: uvicorn src.deployment.api_fastapi:app --reload")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("\n" + "=" * 70)
    print("  🚀 FASTAPI SERVER TESTER")
    print("=" * 70)
    
    base_url = "http://localhost:8000"
    
    # Test 1: Check if server is running
    print("\nChecking if server is running...")
    try:
        response = requests.get(f"{base_url}/health", timeout=2)
        print("✅ Server is running!")
    except:
        print("❌ Server not running")
        print("Start with: uvicorn src.deployment.api_fastapi:app --reload")
        return
    
    # Test endpoints
    tests_passed = 0
    tests_total = 5
    
    # Test 2: Health endpoint
    if test_endpoint("Health Endpoint", "GET", f"{base_url}/health"):
        tests_passed += 1
    
    # Test 3: Root endpoint
    if test_endpoint("Root Endpoint", "GET", f"{base_url}/"):
        tests_passed += 1
    
    # Test 4: Model info
    if test_endpoint("Model Info", "GET", f"{base_url}/model/info"):
        tests_passed += 1
    
    # Test 5: Prediction
    prediction_data = {
        "data": [{
            "temperature": 75.5,
            "vibration": 0.8,
            "pressure": 100.2,
            "current": 12.5,
            "rpm": 1500.0
        }],
        "return_probability": True
    }
    if test_endpoint("Prediction", "POST", f"{base_url}/predict", prediction_data):
        tests_passed += 1
    
    # Test 6: Metrics
    if test_endpoint("Prometheus Metrics", "GET", f"{base_url}/metrics"):
        tests_passed += 1
    
    # Summary
    print("\n" + "=" * 70)
    print("  📊 TEST SUMMARY")
    print("=" * 70)
    print(f"\nTests Passed: {tests_passed}/{tests_total}")
    
    if tests_passed == tests_total:
        print("\n🎉 All tests passed!")
    else:
        print("\n⚠️  Some tests failed")
    
    print("\n💡 View interactive docs:")
    print("   http://localhost:8000/docs (Swagger UI)")
    print("   http://localhost:8000/redoc (ReDoc)")
    print()

if __name__ == "__main__":
    main()
