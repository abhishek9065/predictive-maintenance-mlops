"""
Real-Time API Monitoring Dashboard
Alternative to Prometheus/Grafana for native deployment
"""

import requests
import time
from datetime import datetime
import os
import sys

API_URL = "http://localhost:8001"
REFRESH_INTERVAL = 5  # seconds

def clear_screen():
    """Clear console screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

def format_uptime(seconds):
    """Format uptime in human-readable format"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"

def get_api_health():
    """Get API health status"""
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        if response.status_code == 200:
            return response.json(), None
        else:
            return None, f"HTTP {response.status_code}"
    except requests.exceptions.ConnectionError:
        return None, "Connection refused - API not running"
    except requests.exceptions.Timeout:
        return None, "Request timeout"
    except Exception as e:
        return None, str(e)

def get_model_info():
    """Get model information"""
    try:
        response = requests.get(f"{API_URL}/model/info", timeout=5)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def test_prediction():
    """Test prediction endpoint"""
    try:
        test_data = {
            "temperature": 72.0,
            "vibration": 0.35,
            "pressure": 95.0,
            "rpm": 1450.0,
            "current": 8.5
        }
        start_time = time.time()
        response = requests.post(f"{API_URL}/predict", json=test_data, timeout=5)
        response_time = (time.time() - start_time) * 1000  # ms
        
        if response.status_code == 200:
            return response.json(), response_time, None
        else:
            return None, None, f"HTTP {response.status_code}"
    except Exception as e:
        return None, None, str(e)

def display_dashboard(health_data, model_info, prediction_data, response_time, error, history):
    """Display monitoring dashboard"""
    clear_screen()
    
    print("=" * 80)
    print("  🔍 PRODUCTION API MONITORING DASHBOARD")
    print("=" * 80)
    print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  API URL: {API_URL}")
    print(f"  Refresh: Every {REFRESH_INTERVAL}s")
    print("=" * 80)
    
    # API Status
    print("\n📊 API STATUS")
    print("-" * 80)
    if error:
        print(f"  ❌ Status: ERROR - {error}")
        print(f"  💡 Tip: Start the API with: python production_api.py")
    elif health_data:
        status_emoji = "✅" if health_data['status'] == 'healthy' else "❌"
        print(f"  {status_emoji} Status: {health_data['status'].upper()}")
        print(f"  🕐 Uptime: {format_uptime(health_data['uptime_seconds'])}")
        print(f"  📈 Total Predictions: {health_data['total_predictions']}")
        print(f"  🤖 Model Loaded: {'Yes' if health_data['model_loaded'] else 'No'}")
    
    # Model Info
    if model_info:
        print("\n🧠 MODEL INFORMATION")
        print("-" * 80)
        print(f"  Type: {model_info.get('model_type', 'N/A')}")
        print(f"  Version: {model_info.get('version', 'N/A')}")
        
        metrics = model_info.get('metrics', {})
        if metrics:
            print(f"  Accuracy: {metrics.get('accuracy', 0)*100:.2f}%")
            print(f"  Precision: {metrics.get('precision', 0)*100:.2f}%")
            print(f"  Recall: {metrics.get('recall', 0)*100:.2f}%")
            print(f"  F1 Score: {metrics.get('f1_score', 0)*100:.2f}%")
        
        features = model_info.get('features', [])
        if features:
            print(f"  Features: {', '.join(features)}")
    
    # Prediction Test
    print("\n🎯 LATEST PREDICTION TEST")
    print("-" * 80)
    if prediction_data:
        result = prediction_data.get('prediction', 'unknown').upper()
        confidence = prediction_data.get('confidence', 0) * 100
        
        result_emoji = "🟢" if result == "NORMAL" else "🔴"
        print(f"  {result_emoji} Prediction: {result}")
        print(f"  📊 Confidence: {confidence:.2f}%")
        print(f"  ⚡ Response Time: {response_time:.2f}ms")
        
        # Response time indicator
        if response_time < 100:
            perf = "🚀 Excellent"
        elif response_time < 500:
            perf = "✅ Good"
        elif response_time < 1000:
            perf = "⚠️  Acceptable"
        else:
            perf = "❌ Slow"
        print(f"  Performance: {perf}")
    
    # Prediction History
    if history:
        print("\n📈 PREDICTION HISTORY (Last 10)")
        print("-" * 80)
        for i, record in enumerate(reversed(history[-10:]), 1):
            timestamp = record['timestamp']
            result = record['result']
            conf = record['confidence']
            rt = record['response_time']
            
            emoji = "🟢" if result == "NORMAL" else "🔴"
            print(f"  {i:2d}. {timestamp} | {emoji} {result:7s} | {conf:5.1f}% | {rt:6.1f}ms")
    
    # System Health
    print("\n💊 SYSTEM HEALTH")
    print("-" * 80)
    if health_data and prediction_data:
        checks = []
        checks.append(("API Responsive", True))
        checks.append(("Model Loaded", health_data.get('model_loaded', False)))
        checks.append(("Predictions Working", True))
        checks.append(("Response Time < 1s", response_time < 1000))
        
        passed = sum(1 for _, status in checks if status)
        total = len(checks)
        
        for check, status in checks:
            icon = "✅" if status else "❌"
            print(f"  {icon} {check}")
        
        print(f"\n  Health Score: {passed}/{total} ({passed/total*100:.0f}%)")
    
    # Footer
    print("\n" + "=" * 80)
    print("  Press Ctrl+C to stop monitoring")
    print("=" * 80)

def main():
    """Main monitoring loop"""
    print("Starting API monitoring...")
    print(f"Connecting to: {API_URL}")
    print("Press Ctrl+C to stop\n")
    time.sleep(2)
    
    prediction_history = []
    
    try:
        while True:
            # Get API health
            health_data, health_error = get_api_health()
            
            # Get model info (only once or periodically)
            model_info = get_model_info()
            
            # Test prediction
            prediction_data = None
            response_time = None
            if health_data and health_data.get('model_loaded'):
                prediction_data, response_time, pred_error = test_prediction()
                
                # Add to history
                if prediction_data:
                    prediction_history.append({
                        'timestamp': datetime.now().strftime('%H:%M:%S'),
                        'result': prediction_data.get('prediction', 'unknown').upper(),
                        'confidence': prediction_data.get('confidence', 0) * 100,
                        'response_time': response_time
                    })
            
            # Display dashboard
            display_dashboard(
                health_data, 
                model_info, 
                prediction_data, 
                response_time, 
                health_error,
                prediction_history
            )
            
            # Wait before next refresh
            time.sleep(REFRESH_INTERVAL)
            
    except KeyboardInterrupt:
        print("\n\n✅ Monitoring stopped by user")
        print(f"Total predictions monitored: {len(prediction_history)}")
        if prediction_history:
            avg_response = sum(r['response_time'] for r in prediction_history) / len(prediction_history)
            print(f"Average response time: {avg_response:.2f}ms")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
