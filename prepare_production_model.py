"""
Production Model Preparation
Trains and saves a production-ready model
"""

import pickle
import json
from pathlib import Path
from datetime import datetime
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.model_selection import train_test_split

print("="*80)
print("  PREPARING PRODUCTION MODEL")
print("="*80 + "\n")

# Load data
print("📊 Loading training data...")
df = pd.read_csv('data/train.csv')
print(f"   Loaded {len(df):,} samples")

# Prepare features
feature_cols = ['temperature', 'vibration', 'pressure', 'rpm', 'current']
X = df[feature_cols].values
y = df['failure'].values

# Split for validation
X_train, X_val, y_train, y_val = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print(f"\n🎯 Training samples: {len(X_train):,}")
print(f"🎯 Validation samples: {len(X_val):,}")

# Train model
print("\n🤖 Training Random Forest model...")
model = RandomForestClassifier(
    n_estimators=200,
    max_depth=15,
    min_samples_split=5,
    min_samples_leaf=2,
    random_state=42,
    n_jobs=-1
)

model.fit(X_train, y_train)
print("   ✅ Training complete!")

# Evaluate
print("\n📊 Evaluating model...")
y_pred = model.predict(X_val)

accuracy = accuracy_score(y_val, y_pred)
precision = precision_score(y_val, y_pred, zero_division=0)
recall = recall_score(y_val, y_pred, zero_division=0)
f1 = f1_score(y_val, y_pred, zero_division=0)

print(f"\n   Accuracy:  {accuracy:.4f}")
print(f"   Precision: {precision:.4f}")
print(f"   Recall:    {recall:.4f}")
print(f"   F1 Score:  {f1:.4f}")

# Save model
print("\n💾 Saving production model...")
Path("models").mkdir(exist_ok=True)

model_path = Path("models/production_model.pkl")
with open(model_path, 'wb') as f:
    pickle.dump(model, f)

print(f"   ✅ Model saved: {model_path}")

# Save metadata
metadata = {
    "model_type": "RandomForestClassifier",
    "n_estimators": 200,
    "max_depth": 15,
    "accuracy": accuracy,
    "precision": precision,
    "recall": recall,
    "f1_score": f1,
    "training_samples": len(X_train),
    "validation_samples": len(X_val),
    "features": feature_cols,
    "created_at": datetime.now().isoformat(),
    "version": "2.0.0"
}

metadata_path = Path("models/production_metadata.json")
with open(metadata_path, 'w') as f:
    json.dump(metadata, f, indent=2)

print(f"   ✅ Metadata saved: {metadata_path}")

print("\n" + "="*80)
print("  ✅ PRODUCTION MODEL READY!")
print("="*80)
print(f"\nModel Performance:")
print(f"  • Accuracy: {accuracy:.2%}")
print(f"  • Precision: {precision:.2%}")
print(f"  • Recall: {recall:.2%}")
print(f"  • F1 Score: {f1:.2%}")
print(f"\nModel Location: {model_path}")
print(f"Metadata: {metadata_path}")
print("\nNext step: python production_api.py")
print("="*80 + "\n")
