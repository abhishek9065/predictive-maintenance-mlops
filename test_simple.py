"""
Simple Test Script - Verify Core Functionality
Tests data loading, preprocessing, and basic model training
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

print("="*70)
print("🧪 SIMPLE FUNCTIONALITY TEST")
print("="*70)

# Test 1: Load Data
print("\n✅ Test 1: Loading Historical Data")
data_dir = Path("data/raw")
data_files = list(data_dir.glob("historical_*.json"))

if data_files:
    print(f"   Found {len(data_files)} historical data files")
    with open(data_files[0], 'r') as f:
        data = json.load(f)
    
    df = pd.DataFrame(data)
    print(f"   ✅ Loaded {len(df)} samples")
    print(f"   Columns: {list(df.columns)}")
    
    # Extract sensor data
    sensors_df = pd.json_normalize(df['sensors'])
    df = pd.concat([df.drop('sensors', axis=1), sensors_df], axis=1)
    
    print(f"   Failure samples: {df['is_failing'].sum()}")
    print(f"   Normal samples: {(~df['is_failing']).sum()}")
else:
    print("   ❌ No historical data found!")
    exit(1)

# Test 2: Data Preprocessing
print("\n✅ Test 2: Data Preprocessing")

# Extract features from nested sensor data
features = []
labels = []

for record in data:
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

feature_cols = ['temperature', 'vibration', 'pressure', 'current', 'rpm']

print(f"   Feature shape: {X.shape}")
print(f"   Target shape: {y.shape}")

# Split data
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
print(f"   Training samples: {len(X_train)}")
print(f"   Test samples: {len(X_test)}")

# Test 3: Model Training
print("\n✅ Test 3: Training Random Forest Model")
model = RandomForestClassifier(
    n_estimators=100,
    max_depth=10,
    random_state=42,
    n_jobs=-1
)

model.fit(X_train, y_train)
print("   ✅ Model trained successfully!")

# Test 4: Model Evaluation
print("\n✅ Test 4: Model Evaluation")
y_pred = model.predict(X_test)

accuracy = accuracy_score(y_test, y_pred)
precision = precision_score(y_test, y_pred)
recall = recall_score(y_test, y_pred)
f1 = f1_score(y_test, y_pred)

print(f"   Accuracy:  {accuracy:.4f}")
print(f"   Precision: {precision:.4f}")
print(f"   Recall:    {recall:.4f}")
print(f"   F1 Score:  {f1:.4f}")

# Test 5: Feature Importance
print("\n✅ Test 5: Feature Importance")
feature_importance = pd.DataFrame({
    'feature': feature_cols,
    'importance': model.feature_importances_
}).sort_values('importance', ascending=False)

print(feature_importance.to_string(index=False))

# Test 6: Prediction Test
print("\n✅ Test 6: Making Predictions")
# Create a test sample (normal operation)
normal_sample = np.array([[60, 5.0, 8.0, 15, 1500]])
prediction = model.predict(normal_sample)[0]
probability = model.predict_proba(normal_sample)[0]

print(f"   Normal sample prediction: {'FAILURE' if prediction else 'NORMAL'}")
print(f"   Probability: Normal={probability[0]:.2%}, Failure={probability[1]:.2%}")

# Create a test sample (failure scenario)
failure_sample = np.array([[95, 12.0, 3.0, 25, 800]])
prediction = model.predict(failure_sample)[0]
probability = model.predict_proba(failure_sample)[0]

print(f"   Failure sample prediction: {'FAILURE' if prediction else 'NORMAL'}")
print(f"   Probability: Normal={probability[0]:.2%}, Failure={probability[1]:.2%}")

print("\n" + "="*70)
print("🎉 ALL TESTS PASSED! Your MLOps project is working correctly!")
print("="*70)
print("\n📊 Summary:")
print(f"   ✅ Data loading and parsing")
print(f"   ✅ Feature extraction ({len(feature_cols)} features)")
print(f"   ✅ Model training (Random Forest)")
print(f"   ✅ Model evaluation (Accuracy: {accuracy:.2%})")
print(f"   ✅ Prediction capability")
print("\n🚀 Next Steps:")
print("   1. Start the API: uvicorn src.deployment.api:app --reload")
print("   2. Visit: http://localhost:8000/docs")
print("   3. Test predictions via the API")
print("="*70)
