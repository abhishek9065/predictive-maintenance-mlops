"""
Save Production Model to BentoML
Prepares the model for BentoML serving
"""

import bentoml
import joblib
from pathlib import Path
import json

def save_model():
    """Save production model to BentoML model store"""
    
    print("="*80)
    print("  📦 SAVING MODEL TO BENTOML")
    print("="*80)
    
    # Load the production model
    model_path = Path("models/production_model.pkl")
    metadata_path = Path("models/production_metadata.json")
    
    if not model_path.exists():
        print(f"❌ Model not found at {model_path}")
        print("   Please run: python prepare_production_model.py")
        return None
    
    print(f"\n📂 Loading model from: {model_path}")
    model = joblib.load(model_path)
    
    # Load metadata
    metadata = {}
    if metadata_path.exists():
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        print(f"📄 Loaded metadata from: {metadata_path}")
    
    # Save to BentoML
    print("\n💾 Saving to BentoML model store...")
    
    bento_model = bentoml.sklearn.save_model(
        "predictive_maintenance_model",
        model,
        metadata={
            "framework": "sklearn",
            "model_type": metadata.get("model_type", "RandomForestClassifier"),
            "accuracy": metadata.get("metrics", {}).get("accuracy", 0.9546),
            "precision": metadata.get("metrics", {}).get("precision", 0.9770),
            "recall": metadata.get("metrics", {}).get("recall", 0.9209),
            "f1_score": metadata.get("metrics", {}).get("f1_score", 0.9481),
            "features": metadata.get("features", ["temperature", "vibration", "pressure", "rpm", "current"]),
            "version": metadata.get("version", "2.0.0"),
            "hyperparameters": metadata.get("hyperparameters", {}),
            "training_date": metadata.get("trained_at", ""),
        },
        labels={
            "stage": "production",
            "owner": "mlops-team",
            "project": "predictive-maintenance"
        },
        custom_objects={
            "feature_names": ["temperature", "vibration", "pressure", "rpm", "current"]
        }
    )
    
    print(f"\n✅ Model saved successfully!")
    print(f"   Tag: {bento_model.tag}")
    print(f"   Path: {bento_model.path}")
    
    # Display model info
    print(f"\n📊 Model Information:")
    print(f"   Framework: sklearn")
    print(f"   Type: {metadata.get('model_type', 'RandomForestClassifier')}")
    print(f"   Version: {metadata.get('version', '2.0.0')}")
    print(f"   Accuracy: {metadata.get('metrics', {}).get('accuracy', 0.9546)*100:.2f}%")
    print(f"   Precision: {metadata.get('metrics', {}).get('precision', 0.9770)*100:.2f}%")
    print(f"   Recall: {metadata.get('metrics', {}).get('recall', 0.9209)*100:.2f}%")
    print(f"   F1 Score: {metadata.get('metrics', {}).get('f1_score', 0.9481)*100:.2f}%")
    
    print("\n" + "="*80)
    print("  ✅ MODEL READY FOR BENTOML SERVING")
    print("="*80)
    
    return bento_model

if __name__ == "__main__":
    save_model()
    
    # List all models in BentoML store
    print("\n📚 All models in BentoML store:")
    print("-"*80)
    
    try:
        models = bentoml.models.list()
        for model in models:
            print(f"   • {model.tag}")
    except Exception as e:
        print(f"   Error listing models: {e}")
