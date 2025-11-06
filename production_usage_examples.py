"""
Real-World Production Usage Examples
Demonstrates how to use the Predictive Maintenance API in production
"""

import requests
import json
import pandas as pd
import numpy as np
from datetime import datetime
import time

class PredictiveMaintenanceClient:
    """Client for interacting with the Predictive Maintenance API"""
    
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def check_health(self):
        """Check if API is healthy"""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print("✅ API is healthy")
                print(f"   Status: {data.get('status')}")
                print(f"   Model Loaded: {data.get('model_loaded')}")
                return True
            else:
                print(f"⚠️ API returned status {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Cannot connect to API: {str(e)}")
            return False
    
    def get_model_info(self):
        """Get information about the loaded model"""
        try:
            response = self.session.get(f"{self.base_url}/model/info", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print("📊 Model Information:")
                info = data.get('info', {})
                print(f"   Model Type: {info.get('model_type', 'Unknown')}")
                print(f"   Training Samples: {info.get('training_samples', 'Unknown')}")
                print(f"   Features: {', '.join(data.get('feature_names', []))}")
                return data
            else:
                print(f"⚠️ Could not get model info")
                return None
        except Exception as e:
            print(f"❌ Error getting model info: {str(e)}")
            return None
    
    def predict_batch(self, sensor_data_list):
        """
        Make predictions for multiple sensor readings
        
        Args:
            sensor_data_list: List of dicts with sensor readings
        
        Returns:
            List of predictions
        """
        try:
            # Prepare request
            request_data = {
                "data": sensor_data_list,
                "return_probability": True
            }
            
            # Make request
            response = self.session.post(
                f"{self.base_url}/predict",
                json=request_data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                return result
            else:
                print(f"❌ Prediction failed: HTTP {response.status_code}")
                print(f"   Response: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Prediction error: {str(e)}")
            return None
    
    def predict_single_simple(self, temperature, vibration, pressure, rpm, current):
        """
        Make a single prediction (simplified interface)
        
        Args:
            temperature: Temperature in Celsius
            vibration: Vibration level
            pressure: Pressure in PSI
            rpm: Rotations per minute
            current: Current in Amperes
        
        Returns:
            Prediction result
        """
        sensor_data = {
            "temperature": temperature,
            "vibration": vibration,
            "pressure": pressure,
            "rpm": rpm,
            "current": current
        }
        
        result = self.predict_batch([sensor_data])
        
        if result:
            prediction = result['predictions'][0]
            prob = result['probabilities'][0] if result.get('probabilities') else [0, 0]
            
            return {
                'prediction': 'FAILURE' if prediction == 1 else 'NORMAL',
                'failure_probability': prob[1] if len(prob) > 1 else 0,
                'normal_probability': prob[0] if len(prob) > 0 else 1,
                'sensor_data': sensor_data
            }
        
        return None


def example_1_simple_prediction():
    """Example 1: Make a simple prediction"""
    print("="*80)
    print("  EXAMPLE 1: Simple Prediction")
    print("="*80 + "\n")
    
    client = PredictiveMaintenanceClient()
    
    # Check health first
    if not client.check_health():
        print("\\n❌ API not available. Make sure the server is running.")
        return
    
    print("\\n📊 Making prediction for normal equipment...")
    
    # Normal operating conditions
    result = client.predict_single_simple(
        temperature=70.0,
        vibration=0.3,
        pressure=95.0,
        rpm=1450.0,
        current=8.5
    )
    
    if result:
        print(f"\\n✅ Prediction: {result['prediction']}")
        print(f"   Failure Probability: {result['failure_probability']:.2%}")
        print(f"   Normal Probability: {result['normal_probability']:.2%}")
    
    print("\\n📊 Making prediction for faulty equipment...")
    
    # Fault conditions (high temp, high vibration)
    result = client.predict_single_simple(
        temperature=105.0,  # High temperature
        vibration=2.5,      # High vibration
        pressure=85.0,       # Low pressure
        rpm=1450.0,
        current=12.0
    )
    
    if result:
        print(f"\\n✅ Prediction: {result['prediction']}")
        print(f"   Failure Probability: {result['failure_probability']:.2%}")
        print(f"   Normal Probability: {result['normal_probability']:.2%}")


def example_2_batch_prediction():
    """Example 2: Batch prediction from sensor data"""
    print("\\n" + "="*80)
    print("  EXAMPLE 2: Batch Prediction")
    print("="*80 + "\n")
    
    client = PredictiveMaintenanceClient()
    
    # Simulate multiple sensor readings
    sensor_readings = [
        {"temperature": 70, "vibration": 0.3, "pressure": 95, "rpm": 1450, "current": 8.5},
        {"temperature": 75, "vibration": 0.5, "pressure": 93, "rpm": 1445, "current": 9.0},
        {"temperature": 95, "vibration": 1.8, "pressure": 88, "rpm": 1460, "current": 11.0},
        {"temperature": 110, "vibration": 2.5, "pressure": 80, "rpm": 1470, "current": 13.0},
    ]
    
    print(f"📊 Processing {len(sensor_readings)} sensor readings...")
    
    result = client.predict_batch(sensor_readings)
    
    if result:
        predictions = result['predictions']
        probabilities = result.get('probabilities', [[]] * len(predictions))
        
        print(f"\\n✅ Processed {len(predictions)} predictions:\\n")
        
        for i, (pred, prob) in enumerate(zip(predictions, probabilities)):
            status = "FAILURE" if pred == 1 else "NORMAL"
            prob_val = prob[1] if len(prob) > 1 else 0
            
            print(f"   Reading #{i+1}:")
            print(f"      Temp: {sensor_readings[i]['temperature']}°C, "
                  f"Vib: {sensor_readings[i]['vibration']}, "
                  f"Pressure: {sensor_readings[i]['pressure']} PSI")
            print(f"      → Prediction: {status} (Failure prob: {prob_val:.2%})")


def example_3_realtime_monitoring():
    """Example 3: Real-time monitoring simulation"""
    print("\\n" + "="*80)
    print("  EXAMPLE 3: Real-Time Monitoring Simulation")
    print("="*80 + "\n")
    
    client = PredictiveMaintenanceClient()
    
    print("🔍 Simulating real-time sensor monitoring...")
    print("   (Monitoring 5 readings, 2-second intervals)\\n")
    
    # Simulate gradual degradation
    base_temp = 70
    base_vib = 0.3
    
    for i in range(5):
        # Gradually increase temperature and vibration
        temp = base_temp + (i * 8)
        vib = base_vib + (i * 0.5)
        
        result = client.predict_single_simple(
            temperature=temp,
            vibration=vib,
            pressure=95.0,
            rpm=1450.0,
            current=8.5 + i
        )
        
        if result:
            timestamp = datetime.now().strftime('%H:%M:%S')
            status = result['prediction']
            prob = result['failure_probability']
            
            symbol = "🔴" if status == "FAILURE" else "🟢"
            print(f"{symbol} [{timestamp}] Temp: {temp}°C, Vib: {vib:.1f} → "
                  f"{status} (Risk: {prob:.1%})")
        
        if i < 4:
            time.sleep(2)
    
    print("\\n✅ Monitoring complete")


def example_4_csv_file_processing():
    """Example 4: Process data from CSV file"""
    print("\\n" + "="*80)
    print("  EXAMPLE 4: Process CSV File")
    print("="*80 + "\n")
    
    client = PredictiveMaintenanceClient()
    
    # Check if test data exists
    csv_file = "data/test.csv"
    
    try:
        df = pd.read_csv(csv_file)
        print(f"📄 Loaded {len(df)} records from {csv_file}")
        
        # Take first 10 samples
        sample_df = df.head(10)
        
        # Prepare sensor data
        sensor_data_list = []
        for _, row in sample_df.iterrows():
            sensor_data_list.append({
                "temperature": float(row['temperature']),
                "vibration": float(row['vibration']),
                "pressure": float(row['pressure']),
                "rpm": float(row['rpm']),
                "current": float(row['current'])
            })
        
        # Make predictions
        print(f"\\n🔮 Making predictions for {len(sensor_data_list)} samples...\\n")
        
        result = client.predict_batch(sensor_data_list)
        
        if result:
            predictions = result['predictions']
            actual = sample_df['failure'].values
            
            # Calculate accuracy
            correct = sum(p == a for p, a in zip(predictions, actual))
            accuracy = correct / len(predictions) * 100
            
            print(f"✅ Results:")
            print(f"   Total Predictions: {len(predictions)}")
            print(f"   Correct: {correct}")
            print(f"   Accuracy: {accuracy:.1f}%")
            print(f"   Failures Detected: {sum(predictions)}")
            
            # Show first 5
            print(f"\\n   Sample Results:")
            for i in range(min(5, len(predictions))):
                pred = "FAILURE" if predictions[i] == 1 else "NORMAL"
                act = "FAILURE" if actual[i] == 1 else "NORMAL"
                match = "✓" if predictions[i] == actual[i] else "✗"
                print(f"      {i+1}. Predicted: {pred:7s} | Actual: {act:7s} | {match}")
        
    except FileNotFoundError:
        print(f"⚠️ CSV file not found: {csv_file}")
        print("   Using sample data instead...")


def example_5_production_metrics():
    """Example 5: Monitor production metrics"""
    print("\\n" + "="*80)
    print("  EXAMPLE 5: Production Metrics")
    print("="*80 + "\n")
    
    client = PredictiveMaintenanceClient()
    
    print("📊 Model Information:")
    client.get_model_info()
    
    print("\\n🔍 API Health:")
    client.check_health()
    
    # Make a few predictions to generate metrics
    print("\\n📈 Generating usage metrics...")
    for i in range(3):
        client.predict_single_simple(70 + i*10, 0.3 + i*0.2, 95, 1450, 8.5)
    
    print("\\n✅ Metrics generated!")
    print("   View at: http://localhost:8000/metrics")


def main():
    """Run all examples"""
    print("\\n" + "="*80)
    print("  PREDICTIVE MAINTENANCE API - REAL-WORLD USAGE EXAMPLES")
    print("="*80)
    print("\\nThese examples demonstrate how to use the API in production scenarios.\\n")
    
    try:
        example_1_simple_prediction()
        example_2_batch_prediction()
        example_3_realtime_monitoring()
        example_4_csv_file_processing()
        example_5_production_metrics()
        
        print("\\n" + "="*80)
        print("  ✅ ALL EXAMPLES COMPLETED SUCCESSFULLY!")
        print("="*80)
        print("\\n📖 For more information:")
        print("   - API Documentation: http://localhost:8000/docs")
        print("   - Deployment Guide: PRODUCTION_DEPLOYMENT.md")
        print("   - Project Status: PROJECT_STATUS_REPORT.md")
        print("\\n" + "="*80 + "\\n")
        
    except KeyboardInterrupt:
        print("\\n\\nExamples interrupted by user.")
    except Exception as e:
        print(f"\\n❌ Error: {str(e)}")


if __name__ == "__main__":
    main()
