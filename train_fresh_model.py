"""
Train a fresh production-ready model
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import pickle
import json
from datetime import datetime

def train_production_model():
    """Train a new production model"""
    print("="*80)
    print("  TRAINING FRESH PRODUCTION MODEL")
    print("="*80 + "\n")
    
    # Load training data
    print("1. Loading training data...")
    df_train = pd.read_csv('data/train.csv')
    print(f"   ✅ Loaded {len(df_train)} training samples")
    print(f"   Class distribution:")
    print(f"      Normal (0): {sum(df_train['failure'] == 0)} ({sum(df_train['failure'] == 0)/len(df_train)*100:.1f}%)")
    print(f"      Failure (1): {sum(df_train['failure'] == 1)} ({sum(df_train['failure'] == 1)/len(df_train)*100:.1f}%)")
    
    # Load test data
    print(f"\n2. Loading test data...")
    df_test = pd.read_csv('data/test.csv')
    print(f"   ✅ Loaded {len(df_test)} test samples")
    
    # Prepare features
    print(f"\n3. Preparing features...")
    feature_cols = ['temperature', 'vibration', 'pressure', 'rpm', 'current']
    
    X_train = df_train[feature_cols].values
    y_train = df_train['failure'].values
    
    X_test = df_test[feature_cols].values
    y_test = df_test['failure'].values
    
    print(f"   ✅ X_train shape: {X_train.shape}")
    print(f"   ✅ X_test shape: {X_test.shape}")
    
    # Train model
    print(f"\n4. Training Random Forest model...")
    print(f"   Parameters:")
    print(f"      n_estimators: 150")
    print(f"      max_depth: 12")
    print(f"      random_state: 42")
    print(f"      n_jobs: -1")
    
    model = RandomForestClassifier(
        n_estimators=150,
        max_depth=12,
        random_state=42,
        n_jobs=-1,
        class_weight='balanced'  # Handle class imbalance
    )
    
    model.fit(X_train, y_train)
    print(f"   ✅ Model trained successfully")
    
    # Evaluate on training set
    print(f"\n5. Evaluating on TRAINING set...")
    y_train_pred = model.predict(X_train)
    train_accuracy = accuracy_score(y_train, y_train_pred)
    print(f"   Training Accuracy: {train_accuracy*100:.2f}%")
    
    # Evaluate on test set
    print(f"\n6. Evaluating on TEST set...")
    y_pred = model.predict(X_test)
    test_accuracy = accuracy_score(y_test, y_pred)
    
    print(f"   ✅ Test Accuracy: {test_accuracy*100:.2f}%")
    
    # Confusion matrix
    cm = confusion_matrix(y_test, y_pred)
    print(f"\n   Confusion Matrix:")
    print(f"                  Predicted")
    print(f"                NORMAL  FAILURE")
    print(f"   Actual NORMAL   {cm[0][0]:5d}   {cm[0][1]:5d}")
    print(f"          FAILURE  {cm[1][0]:5d}   {cm[1][1]:5d}")
    
    # Classification report
    print(f"\n   Detailed Classification Report:")
    print(classification_report(y_test, y_pred, target_names=['Normal', 'Failure']))
    
    # Feature importance
    print(f"\n7. Feature Importance:")
    feature_importance = sorted(zip(feature_cols, model.feature_importances_), 
                                key=lambda x: x[1], reverse=True)
    for feat, imp in feature_importance:
        print(f"      {feat:15s}: {imp:.4f}")
    
    # Save model
    print(f"\n8. Saving model...")
    
    # Save as best_model.pkl
    with open('models/best_model.pkl', 'wb') as f:
        pickle.dump(model, f)
    print(f"   ✅ Saved to models/best_model.pkl")
    
    # Save metrics
    metrics = {
        'accuracy': float(test_accuracy),
        'train_accuracy': float(train_accuracy),
        'model_type': 'RandomForestClassifier',
        'n_estimators': 150,
        'max_depth': 12,
        'training_samples': len(df_train),
        'test_samples': len(df_test),
        'features': feature_cols,
        'confusion_matrix': cm.tolist(),
        'trained_at': datetime.now().isoformat()
    }
    
    with open('models/best_model_metrics.json', 'w') as f:
        json.dump(metrics, f, indent=2)
    print(f"   ✅ Saved metrics to models/best_model_metrics.json")
    
    # Test the saved model
    print(f"\n9. Verifying saved model...")
    with open('models/best_model.pkl', 'rb') as f:
        loaded_model = pickle.load(f)
    
    test_pred = loaded_model.predict(X_test[:10])
    print(f"   ✅ Model loads correctly")
    print(f"   Sample predictions: {test_pred}")
    
    print("\n" + "="*80)
    print(f"  ✅ MODEL TRAINING COMPLETE - {test_accuracy*100:.2f}% ACCURACY")
    print("="*80 + "\n")
    
    return model, metrics

if __name__ == "__main__":
    train_production_model()
