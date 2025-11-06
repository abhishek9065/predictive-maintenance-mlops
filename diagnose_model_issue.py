"""
Diagnose why the model is predicting everything as FAILURE
"""

import pickle
import pandas as pd
import numpy as np
import json

def check_model_file():
    """Check the loaded model"""
    print("="*80)
    print("  DIAGNOSING MODEL ISSUE")
    print("="*80 + "\n")
    
    # Load model
    print("1. Loading model...")
    with open('models/best_model.pkl', 'rb') as f:
        model = pickle.load(f)
    
    print(f"   ✅ Model loaded: {type(model).__name__}")
    print(f"   Features expected: {model.n_features_in_}")
    
    # Check if model has feature names
    if hasattr(model, 'feature_names_in_'):
        print(f"   Feature names: {list(model.feature_names_in_)}")
    
    # Check model parameters
    print(f"\n2. Model Parameters:")
    print(f"   Estimators: {model.n_estimators}")
    print(f"   Max Depth: {model.max_depth}")
    
    # Load test data
    print(f"\n3. Loading test data...")
    df_test = pd.read_csv('data/test.csv')
    print(f"   ✅ Loaded {len(df_test)} test samples")
    print(f"   Class distribution:")
    print(f"      Normal (0): {sum(df_test['failure'] == 0)} ({sum(df_test['failure'] == 0)/len(df_test)*100:.1f}%)")
    print(f"      Failure (1): {sum(df_test['failure'] == 1)} ({sum(df_test['failure'] == 1)/len(df_test)*100:.1f}%)")
    
    # Test with actual normal samples
    print(f"\n4. Testing with KNOWN NORMAL samples...")
    normal_samples = df_test[df_test['failure'] == 0].head(5)
    
    X_normal = normal_samples[['temperature', 'vibration', 'pressure', 'rpm', 'current']]
    y_actual = normal_samples['failure'].values
    
    print(f"\n   Sample data:")
    for idx, row in X_normal.iterrows():
        print(f"      Temp: {row['temperature']:.1f}, Vib: {row['vibration']:.2f}, "
              f"Press: {row['pressure']:.1f}, RPM: {row['rpm']:.0f}, Current: {row['current']:.1f}")
    
    # Make predictions
    predictions = model.predict(X_normal)
    probabilities = model.predict_proba(X_normal)
    
    print(f"\n   Predictions:")
    for i, (pred, prob, actual) in enumerate(zip(predictions, probabilities, y_actual)):
        status = "FAILURE" if pred == 1 else "NORMAL"
        actual_status = "FAILURE" if actual == 1 else "NORMAL"
        match = "✓" if pred == actual else "✗"
        print(f"      Sample {i+1}: Predicted={status:7s} (Prob: {prob[1]:.2%}) | "
              f"Actual={actual_status:7s} | {match}")
    
    # Test with actual failure samples
    print(f"\n5. Testing with KNOWN FAILURE samples...")
    failure_samples = df_test[df_test['failure'] == 1].head(5)
    
    X_failure = failure_samples[['temperature', 'vibration', 'pressure', 'rpm', 'current']]
    y_actual_failure = failure_samples['failure'].values
    
    print(f"\n   Sample data:")
    for idx, row in X_failure.iterrows():
        print(f"      Temp: {row['temperature']:.1f}, Vib: {row['vibration']:.2f}, "
              f"Press: {row['pressure']:.1f}, RPM: {row['rpm']:.0f}, Current: {row['current']:.1f}")
    
    predictions_failure = model.predict(X_failure)
    probabilities_failure = model.predict_proba(X_failure)
    
    print(f"\n   Predictions:")
    for i, (pred, prob, actual) in enumerate(zip(predictions_failure, probabilities_failure, y_actual_failure)):
        status = "FAILURE" if pred == 1 else "NORMAL"
        actual_status = "FAILURE" if actual == 1 else "NORMAL"
        match = "✓" if pred == actual else "✗"
        print(f"      Sample {i+1}: Predicted={status:7s} (Prob: {prob[1]:.2%}) | "
              f"Actual={actual_status:7s} | {match}")
    
    # Test on full test set
    print(f"\n6. Testing on FULL test set ({len(df_test)} samples)...")
    X_test = df_test[['temperature', 'vibration', 'pressure', 'rpm', 'current']]
    y_test = df_test['failure'].values
    
    all_predictions = model.predict(X_test)
    
    from sklearn.metrics import accuracy_score, confusion_matrix, classification_report
    
    accuracy = accuracy_score(y_test, all_predictions)
    cm = confusion_matrix(y_test, all_predictions)
    
    print(f"\n   Overall Accuracy: {accuracy*100:.2f}%")
    print(f"\n   Confusion Matrix:")
    print(f"                  Predicted")
    print(f"                NORMAL  FAILURE")
    print(f"   Actual NORMAL   {cm[0][0]:5d}   {cm[0][1]:5d}")
    print(f"          FAILURE  {cm[1][0]:5d}   {cm[1][1]:5d}")
    
    print(f"\n   Classification Report:")
    print(classification_report(y_test, all_predictions, target_names=['Normal', 'Failure']))
    
    # Check training data
    print(f"\n7. Checking TRAINING data...")
    df_train = pd.read_csv('data/train.csv')
    print(f"   ✅ Loaded {len(df_train)} training samples")
    print(f"   Class distribution:")
    print(f"      Normal (0): {sum(df_train['failure'] == 0)} ({sum(df_train['failure'] == 0)/len(df_train)*100:.1f}%)")
    print(f"      Failure (1): {sum(df_train['failure'] == 1)} ({sum(df_train['failure'] == 1)/len(df_train)*100:.1f}%)")
    
    # Check if we trained on augmented data
    try:
        df_augmented = pd.read_csv('data/augmented_train.csv')
        print(f"\n   ⚠️ Augmented data found: {len(df_augmented)} samples")
        print(f"   Class distribution:")
        print(f"      Normal (0): {sum(df_augmented['failure'] == 0)} ({sum(df_augmented['failure'] == 0)/len(df_augmented)*100:.1f}%)")
        print(f"      Failure (1): {sum(df_augmented['failure'] == 1)} ({sum(df_augmented['failure'] == 1)/len(df_augmented)*100:.1f}%)")
    except FileNotFoundError:
        print(f"\n   No augmented data found")
    
    # Check model metadata
    print(f"\n8. Checking model metadata...")
    try:
        with open('models/best_model_metrics.json', 'r') as f:
            metrics = json.load(f)
        
        print(f"   ✅ Model metrics found:")
        print(f"      Accuracy: {metrics.get('accuracy', 'N/A')}")
        print(f"      Precision: {metrics.get('precision', 'N/A')}")
        print(f"      Recall: {metrics.get('recall', 'N/A')}")
        print(f"      F1 Score: {metrics.get('f1_score', 'N/A')}")
    except FileNotFoundError:
        print(f"   ⚠️ No metrics file found")
    
    print("\n" + "="*80)
    print("  DIAGNOSIS COMPLETE")
    print("="*80 + "\n")

if __name__ == "__main__":
    check_model_file()
