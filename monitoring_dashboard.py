"""
Real-time Monitoring Dashboard
Alternative to Grafana - Simple Python-based monitoring
"""

import requests
import time
import os
from datetime import datetime
from collections import deque
import statistics

# Configuration
API_URL = "http://localhost:8001"
REFRESH_INTERVAL = 5  # seconds
HISTORY_SIZE = 20  # keep last 20 readings

class MonitoringDashboard:
    def __init__(self):
        self.prediction_history = deque(maxlen=HISTORY_SIZE)
        self.response_times = deque(maxlen=HISTORY_SIZE)
        self.failure_count = 0
        self.normal_count = 0
        self.start_time = datetime.now()
        
    def clear_screen(self):
        """Clear console screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def get_api_health(self):
        """Get API health status"""
        try:
            response = requests.get(f"{API_URL}/health", timeout=2)
            if response.status_code == 200:
                return response.json()
            return None
        except:
            return None
    
    def get_model_info(self):
        """Get model information"""
        try:
            response = requests.get(f"{API_URL}/model/info", timeout=2)
            if response.status_code == 200:
                return response.json()
            return None
        except:
            return None
    
    def make_test_prediction(self):
        """Make a test prediction to measure response time"""
        import random
        
        # Generate random sensor data
        temp = random.uniform(65, 110)
        vibration = random.uniform(0.2, 3.0)
        
        data = {
            "temperature": temp,
            "vibration": vibration,
            "pressure": random.uniform(85, 100),
            "rpm": random.uniform(1400, 1600),
            "current": random.uniform(7, 16)
        }
        
        try:
            start = time.time()
            response = requests.post(f"{API_URL}/predict", json=data, timeout=5)
            elapsed = (time.time() - start) * 1000  # Convert to ms
            
            if response.status_code == 200:
                result = response.json()
                self.response_times.append(elapsed)
                
                prediction = result.get("prediction", "unknown")
                self.prediction_history.append({
                    "time": datetime.now(),
                    "prediction": prediction,
                    "confidence": result.get("confidence", 0),
                    "response_time": elapsed
                })
                
                if prediction == "failure":
                    self.failure_count += 1
                else:
                    self.normal_count += 1
                
                return result, elapsed
            return None, None
        except Exception as e:
            return None, None
    
    def print_dashboard(self):
        """Print the monitoring dashboard"""
        self.clear_screen()
        
        # Header
        print("=" * 100)
        print("  🖥️  PREDICTIVE MAINTENANCE - REAL-TIME MONITORING DASHBOARD")
        print("=" * 100)
        print(f"  Monitoring: {API_URL}")
        print(f"  Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  Uptime: {(datetime.now() - self.start_time).total_seconds():.1f}s")
        print("=" * 100)
        print()
        
        # API Health
        health = self.get_api_health()
        if health:
            print("📊 API HEALTH STATUS")
            print("─" * 100)
            status_icon = "🟢" if health.get("status") == "healthy" else "🔴"
            print(f"  {status_icon} Status: {health.get('status', 'unknown').upper()}")
            print(f"  🤖 Model Loaded: {'✅ Yes' if health.get('model_loaded') else '❌ No'}")
            print(f"  ⏱️  API Uptime: {health.get('uptime_seconds', 0):.1f}s")
            print(f"  📈 Total Predictions: {health.get('total_predictions', 0)}")
        else:
            print("📊 API HEALTH STATUS")
            print("─" * 100)
            print("  🔴 Status: OFFLINE or UNREACHABLE")
        print()
        
        # Model Information
        model_info = self.get_model_info()
        if model_info:
            print("🤖 MODEL INFORMATION")
            print("─" * 100)
            print(f"  Type: {model_info.get('model_type', 'N/A')}")
            print(f"  Version: {model_info.get('version', 'N/A')}")
            metrics = model_info.get('metrics', {})
            if metrics:
                print(f"  Accuracy: {metrics.get('accuracy', 0)*100:.2f}%")
                print(f"  Precision: {metrics.get('precision', 0)*100:.2f}%")
                print(f"  Recall: {metrics.get('recall', 0)*100:.2f}%")
        print()
        
        # Performance Metrics
        print("⚡ PERFORMANCE METRICS")
        print("─" * 100)
        if len(self.response_times) > 0:
            avg_response = statistics.mean(self.response_times)
            min_response = min(self.response_times)
            max_response = max(self.response_times)
            
            # Color code based on performance
            if avg_response < 100:
                perf_icon = "🟢"
                perf_status = "EXCELLENT"
            elif avg_response < 500:
                perf_icon = "🟡"
                perf_status = "GOOD"
            else:
                perf_icon = "🔴"
                perf_status = "SLOW"
            
            print(f"  {perf_icon} Performance: {perf_status}")
            print(f"  📊 Avg Response Time: {avg_response:.2f}ms")
            print(f"  ⚡ Min Response Time: {min_response:.2f}ms")
            print(f"  🐌 Max Response Time: {max_response:.2f}ms")
            print(f"  📦 Samples Monitored: {len(self.prediction_history)}")
        else:
            print("  ⏳ Collecting performance data...")
        print()
        
        # Prediction Statistics
        total = self.normal_count + self.failure_count
        if total > 0:
            print("📈 PREDICTION STATISTICS")
            print("─" * 100)
            print(f"  🟢 Normal: {self.normal_count} ({self.normal_count/total*100:.1f}%)")
            print(f"  🔴 Failure: {self.failure_count} ({self.failure_count/total*100:.1f}%)")
            print(f"  📊 Total: {total}")
            print()
        
        # Recent Predictions
        if len(self.prediction_history) > 0:
            print("🔄 RECENT PREDICTIONS (Last 10)")
            print("─" * 100)
            print(f"  {'Time':<12} {'Prediction':<10} {'Confidence':<12} {'Response Time':<15}")
            print("  " + "─" * 96)
            
            for pred in list(self.prediction_history)[-10:]:
                time_str = pred["time"].strftime("%H:%M:%S")
                prediction = pred["prediction"].upper()
                confidence = f"{pred['confidence']*100:.1f}%"
                response = f"{pred['response_time']:.2f}ms"
                
                icon = "🟢" if pred["prediction"] == "normal" else "🔴"
                print(f"  {time_str:<12} {icon} {prediction:<8} {confidence:<12} {response:<15}")
        print()
        
        print("=" * 100)
        print(f"  🔄 Refreshing every {REFRESH_INTERVAL}s... (Press Ctrl+C to stop)")
        print("=" * 100)
    
    def run(self):
        """Run the monitoring dashboard"""
        print("\n🚀 Starting Monitoring Dashboard...\n")
        time.sleep(2)
        
        try:
            while True:
                # Make test prediction
                self.make_test_prediction()
                
                # Display dashboard
                self.print_dashboard()
                
                # Wait before next refresh
                time.sleep(REFRESH_INTERVAL)
                
        except KeyboardInterrupt:
            print("\n\n👋 Monitoring stopped by user")
            print("\n📊 FINAL STATISTICS")
            print("─" * 50)
            print(f"  Total Predictions: {self.normal_count + self.failure_count}")
            print(f"  Normal: {self.normal_count}")
            print(f"  Failures: {self.failure_count}")
            if len(self.response_times) > 0:
                print(f"  Avg Response Time: {statistics.mean(self.response_times):.2f}ms")
            print()

if __name__ == "__main__":
    dashboard = MonitoringDashboard()
    dashboard.run()
