"""
Test the API with REAL test data from CSV
"""

import pandas as pd
import requests
import json

def test_api_with_real_data():
    """Test API using actual test data from CSV"""
    print("="*80)
    print("  TESTING API WITH REAL TEST DATA")
    print("="*80 + "\n")
    
    # Load test data
    print("1. Loading test data from CSV...")
    df = pd.read_csv('data/test.csv')
    print(f"   ✅ Loaded {len(df)} samples")
    
    # Get some normal samples
    print(f"\n2. Testing with KNOWN NORMAL samples...")
    normal_samples = df[df['failure'] == 0].head(5)
    
    print(f"\n   Actual normal samples from CSV:")
    for idx, row in normal_samples.iterrows():
        print(f"      Temp: {row['temperature']:.1f}°C, Vib: {row['vibration']:.3f}, "
              f"Press: {row['pressure']:.1f} PSI, RPM: {row['rpm']:.0f}, Current: {row['current']:.1f}A")
    
    # Prepare API request
    sensor_data = []
    for _, row in normal_samples.iterrows():
        sensor_data.append({
            "temperature": float(row['temperature']),
            "vibration": float(row['vibration']),
            "pressure": float(row['pressure']),
            "rpm": float(row['rpm']),
            "current": float(row['current'])
        })
    
    request_data = {
        "data": sensor_data,
        "return_probability": True
    }
    
    # Make API request
    print(f"\n3. Sending to API...")
    response = requests.post(
        "http://localhost:8000/predict",
        json=request_data
    )
    
    if response.status_code == 200:
        result = response.json()
        predictions = result['predictions']
        probabilities = result.get('probabilities', [[]] * len(predictions))
        
        print(f"\n   API Predictions:")
        for i, (pred, prob) in enumerate(zip(predictions, probabilities)):
            status = "FAILURE" if pred == 1 else "NORMAL"
            prob_val = prob[1] if len(prob) > 1 else 0
            actual_status = "NORMAL"
            match = "✓" if pred == 0 else "✗"
            
            print(f"      Sample {i+1}: Predicted={status:7s} (Prob: {prob_val:.2%}) | "
                  f"Actual={actual_status:7s} | {match}")
        
        correct = sum(1 for p in predictions if p == 0)
        accuracy = correct / len(predictions) * 100
        print(f"\n   Accuracy on normal samples: {accuracy:.1f}%")
    else:
        print(f"   ❌ API Error: {response.status_code}")
        print(f"   {response.text}")
    
    # Test failure samples
    print(f"\n4. Testing with KNOWN FAILURE samples...")
    failure_samples = df[df['failure'] == 1].head(5)
    
    print(f"\n   Actual failure samples from CSV:")
    for idx, row in failure_samples.iterrows():
        print(f"      Temp: {row['temperature']:.1f}°C, Vib: {row['vibration']:.3f}, "
              f"Press: {row['pressure']:.1f} PSI, RPM: {row['rpm']:.0f}, Current: {row['current']:.1f}A")
    
    sensor_data_failure = []
    for _, row in failure_samples.iterrows():
        sensor_data_failure.append({
            "temperature": float(row['temperature']),
            "vibration": float(row['vibration']),
            "pressure": float(row['pressure']),
            "rpm": float(row['rpm']),
            "current": float(row['current'])
        })
    
    request_data_failure = {
        "data": sensor_data_failure,
        "return_probability": True
    }
    
    response = requests.post(
        "http://localhost:8000/predict",
        json=request_data_failure
    )
    
    if response.status_code == 200:
        result = response.json()
        predictions = result['predictions']
        probabilities = result.get('probabilities', [[]] * len(predictions))
        
        print(f"\n   API Predictions:")
        for i, (pred, prob) in enumerate(zip(predictions, probabilities)):
            status = "FAILURE" if pred == 1 else "NORMAL"
            prob_val = prob[1] if len(prob) > 1 else 0
            actual_status = "FAILURE"
            match = "✓" if pred == 1 else "✗"
            
            print(f"      Sample {i+1}: Predicted={status:7s} (Prob: {prob_val:.2%}) | "
                  f"Actual={actual_status:7s} | {match}")
        
        correct = sum(1 for p in predictions if p == 1)
        accuracy = correct / len(predictions) * 100
        print(f"\n   Accuracy on failure samples: {accuracy:.1f}%")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    test_api_with_real_data()
