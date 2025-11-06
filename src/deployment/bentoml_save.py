"""
BentoML Model Saver
Save trained models to BentoML model store
"""

import json
import logging
from datetime import datetime
from pathlib import Path

import bentoml
import joblib
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def save_model_to_bentoml(
    model_path: str,
    model_name: str = "predictive_maintenance_model",
    labels: dict = None
):
    """
    Save a scikit-learn model to BentoML model store
    
    Args:
        model_path: Path to the saved model (.pkl file)
        model_name: Name for the BentoML model
        labels: Additional labels/metadata
    """
    try:
        # Load the model
        model = joblib.load(model_path)
        logger.info(f"Loaded model from {model_path}")
        
        # Load metadata if exists
        metadata_path = Path(model_path).parent / "metadata.json"
        metadata = {}
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            logger.info(f"Loaded metadata: {metadata.get('model_type', 'unknown')}")
        
        # Prepare labels
        if labels is None:
            labels = {}
        
        labels.update({
            "model_type": metadata.get("model_type", type(model).__name__),
            "training_date": metadata.get("training_date", datetime.now().isoformat()),
            "framework": "scikit-learn"
        })
        
        # Save to BentoML
        saved_model = bentoml.sklearn.save_model(
            model_name,
            model,
            labels=labels,
            metadata=metadata,
            custom_objects={
                "metadata": metadata
            }
        )
        
        logger.info(f"Model saved to BentoML: {saved_model.tag}")
        print(f"\n✓ Model saved successfully!")
        print(f"  Name: {saved_model.tag.name}")
        print(f"  Version: {saved_model.tag.version}")
        print(f"  Path: {saved_model.path}")
        
        return saved_model
    
    except Exception as e:
        logger.error(f"Error saving model to BentoML: {e}")
        raise

def save_production_model():
    """Save the current production model to BentoML"""
    production_path = "models/production/model.pkl"
    
    if not Path(production_path).exists():
        logger.warning(f"Production model not found at {production_path}")
        logger.info("Trying staging model...")
        production_path = "models/staging/model.pkl"
    
    if Path(production_path).exists():
        return save_model_to_bentoml(
            production_path,
            model_name="predictive_maintenance_model",
            labels={"stage": "production"}
        )
    else:
        raise FileNotFoundError("No model found to save")

def list_bentoml_models():
    """List all models in BentoML store"""
    try:
        models = bentoml.models.list()
        
        print("\nBentoML Model Store:")
        print("-" * 80)
        
        for model in models:
            print(f"\nName: {model.tag.name}")
            print(f"Version: {model.tag.version}")
            print(f"Created: {model.info.creation_time}")
            print(f"Labels: {model.info.labels}")
        
        return models
    
    except Exception as e:
        logger.error(f"Error listing models: {e}")
        return []

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Save models to BentoML")
    parser.add_argument(
        "--model-path",
        type=str,
        help="Path to model file (.pkl)"
    )
    parser.add_argument(
        "--production",
        action="store_true",
        help="Save production model"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all BentoML models"
    )
    
    args = parser.parse_args()
    
    if args.list:
        list_bentoml_models()
    elif args.production:
        save_production_model()
    elif args.model_path:
        save_model_to_bentoml(args.model_path)
    else:
        # Default: save production model
        save_production_model()
