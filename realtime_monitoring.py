"""
Real-time Evidently AI Monitoring Dashboard
Monitors production API and generates live monitoring reports
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime
import time
import json
from pathlib import Path
from collections import deque

from evidently_monitoring import EvidentlyMonitor

class RealTimeMonitor:
    """Real-time monitoring with Evidently AI"""
    
    def __init__(self, api_url="http://localhost:8001", 
                 reference_data_path="data/train.csv",
                 batch_size=100):
        """
        Initialize real-time monitor
        
        Args:
            api_url: Production API URL
            reference_data_path: Reference data for drift detection
            batch_size: Number of predictions before generating report
        """
        self.api_url = api_url
        self.batch_size = batch_size
        
        # Initialize Evidently monitor
        self.evidently = EvidentlyMonitor(
            reference_data_path=reference_data_path,
            output_dir="reports/evidently/realtime"
        )
        
        # Storage for predictions
        self.prediction_buffer = deque(maxlen=batch_size * 2)
        self.metrics_history = []
        
        print("✅ Real-time monitor initialized")
    
    def check_api_health(self):
        """Check if API is available"""
        try:
            response = requests.get(f"{self.api_url}/health", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def generate_test_data(self, n_samples=10):
        """Generate test sensor data"""
        data = []
        for _ in range(n_samples):
            # Random normal or failure condition
            if np.random.random() < 0.3:  # 30% failure
                temp = np.random.uniform(85, 110)
                vib = np.random.uniform(1.5, 3.0)
            else:  # 70% normal
                temp = np.random.uniform(65, 80)
                vib = np.random.uniform(0.2, 0.8)
            
            sample = {
                "temperature": float(temp),
                "vibration": float(vib),
                "pressure": float(np.random.uniform(85, 100)),
                "rpm": float(np.random.uniform(1400, 1600)),
                "current": float(np.random.uniform(7, 16))
            }
            data.append(sample)
        
        return data
    
    def send_prediction_request(self, sensor_data):
        """Send prediction request to API"""
        try:
            response = requests.post(
                f"{self.api_url}/predict",
                json=sensor_data,
                timeout=5
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return None
        except Exception as e:
            print(f"❌ Error: {e}")
            return None
    
    def collect_predictions(self, n_predictions=100):
        """Collect predictions from API"""
        print(f"\n📊 Collecting {n_predictions} predictions...")
        
        predictions_data = []
        
        for i in range(n_predictions):
            # Generate test data
            test_samples = self.generate_test_data(n_samples=1)
            sensor_data = test_samples[0]
            
            # Get prediction
            result = self.send_prediction_request(sensor_data)
            
            if result:
                # Store prediction with features
                pred_record = {
                    **sensor_data,
                    'prediction': 1 if result['prediction'] == 'failure' else 0,
                    'confidence': result['confidence'],
                    'timestamp': datetime.now().isoformat()
                }
                predictions_data.append(pred_record)
                
                # Progress
                if (i + 1) % 20 == 0:
                    print(f"   Progress: {i + 1}/{n_predictions}")
            
            # Small delay
            time.sleep(0.1)
        
        print(f"   ✅ Collected {len(predictions_data)} predictions")
        return pd.DataFrame(predictions_data)
    
    def run_monitoring_cycle(self):
        """Run one monitoring cycle"""
        print("\n" + "="*100)
        print("  🔄 RUNNING MONITORING CYCLE")
        print("="*100)
        
        # Check API health
        if not self.check_api_health():
            print("❌ API is not available!")
            return False
        
        print("✅ API is healthy")
        
        # Collect predictions
        current_data = self.collect_predictions(n_predictions=self.batch_size)
        
        # Generate Evidently reports
        print("\n📊 Generating Evidently AI reports...")
        
        # Data drift report
        self.evidently.generate_data_drift_report(current_data, save_html=True)
        
        # Data quality report
        self.evidently.generate_data_quality_report(current_data, save_html=True)
        
        # Prediction analysis
        predictions = current_data['prediction'].values
        features = current_data[['temperature', 'vibration', 'pressure', 'rpm', 'current']]
        
        # Create probability matrix (approximate from confidence)
        probabilities = np.zeros((len(predictions), 2))
        for i, (pred, conf) in enumerate(zip(predictions, current_data['confidence'])):
            if pred == 1:
                probabilities[i] = [1 - conf, conf]
            else:
                probabilities[i] = [conf, 1 - conf]
        
        analysis = self.evidently.analyze_predictions(features, predictions, probabilities)
        
        # Store metrics
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'total_predictions': len(predictions),
            'failure_rate': float(np.mean(predictions)),
            'avg_confidence': float(np.mean(current_data['confidence'])),
            'high_risk_count': len(analysis['high_risk_samples'])
        }
        self.metrics_history.append(metrics)
        
        print("\n✅ Monitoring cycle complete!")
        return True
    
    def run_continuous_monitoring(self, n_cycles=3, interval_seconds=60):
        """
        Run continuous monitoring
        
        Args:
            n_cycles: Number of monitoring cycles
            interval_seconds: Seconds between cycles
        """
        print("\n" + "="*100)
        print("  🚀 STARTING CONTINUOUS EVIDENTLY AI MONITORING")
        print("="*100)
        print(f"\n  Configuration:")
        print(f"     API URL: {self.api_url}")
        print(f"     Batch Size: {self.batch_size}")
        print(f"     Cycles: {n_cycles}")
        print(f"     Interval: {interval_seconds}s")
        
        for cycle in range(n_cycles):
            print(f"\n{'='*100}")
            print(f"  📍 CYCLE {cycle + 1}/{n_cycles}")
            print(f"{'='*100}")
            
            if not self.run_monitoring_cycle():
                print("⚠️  Monitoring cycle failed, waiting...")
            
            if cycle < n_cycles - 1:
                print(f"\n⏳ Waiting {interval_seconds}s before next cycle...")
                time.sleep(interval_seconds)
        
        # Save metrics history
        self.save_metrics_summary()
        
        print("\n" + "="*100)
        print("  ✅ CONTINUOUS MONITORING COMPLETE")
        print("="*100)
    
    def save_metrics_summary(self):
        """Save metrics summary"""
        summary_path = Path("reports/evidently/realtime/metrics_summary.json")
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(summary_path, 'w') as f:
            json.dump(self.metrics_history, f, indent=2)
        
        print(f"\n📊 Metrics summary saved: {summary_path}")
        
        # Print summary statistics
        if self.metrics_history:
            print("\n📈 Overall Statistics:")
            failure_rates = [m['failure_rate'] for m in self.metrics_history]
            confidences = [m['avg_confidence'] for m in self.metrics_history]
            
            print(f"   Avg Failure Rate: {np.mean(failure_rates)*100:.1f}%")
            print(f"   Avg Confidence: {np.mean(confidences)*100:.1f}%")
            print(f"   Total Predictions: {sum(m['total_predictions'] for m in self.metrics_history)}")

def main():
    """Main function"""
    print("\n" + "="*100)
    print("  🎯 EVIDENTLY AI REAL-TIME MONITORING")
    print("="*100)
    
    # Check API availability
    api_url = "http://localhost:8001"
    
    print(f"\n🔍 Checking API at {api_url}...")
    try:
        response = requests.get(f"{api_url}/health", timeout=2)
        if response.status_code == 200:
            print("   ✅ API is running")
        else:
            print("   ❌ API returned error")
            return
    except:
        print("   ❌ API is not available")
        print("\n   Please start the production API:")
        print("   python production_api.py")
        return
    
    # Create monitor
    monitor = RealTimeMonitor(
        api_url=api_url,
        reference_data_path="data/train.csv",
        batch_size=100
    )
    
    # Run monitoring
    monitor.run_continuous_monitoring(
        n_cycles=3,
        interval_seconds=30
    )
    
    print("\n" + "="*100)
    print("  🎉 MONITORING SESSION COMPLETE")
    print("="*100)
    print("\n  📊 Reports Generated:")
    print("     - Data Drift Reports (HTML)")
    print("     - Data Quality Reports (HTML)")
    print("     - Metrics Summary (JSON)")
    print("\n  📁 Location: reports/evidently/realtime/")
    print("\n  💡 Open HTML reports in browser for interactive analysis!")

if __name__ == "__main__":
    main()
