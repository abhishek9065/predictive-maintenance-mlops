"""
Model Loader
Loads and manages trained models for deployment.
"""

from typing import Dict, Optional
import joblib
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ModelLoader:
    """Load and manage trained models."""
    
    def __init__(self):
        """Initialize model loader."""
        self.models: Dict = {}
    
    def load_model(self, model_name: str, model_path: str):
        """
        Load a model from disk.
        
        Args:
            model_name: Name to assign to the model
            model_path: Path to the model file
        """
        if not Path(model_path).exists():
            raise FileNotFoundError(f"Model file not found: {model_path}")
        
        try:
            model_data = joblib.load(model_path)
            self.models[model_name] = model_data['model']
            logger.info(f"Model '{model_name}' loaded successfully")
        
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
    
    def get_model(self, model_name: str):
        """
        Get a loaded model.
        
        Args:
            model_name: Name of the model
            
        Returns:
            Model object or None
        """
        return self.models.get(model_name)
    
    def unload_model(self, model_name: str):
        """
        Unload a model from memory.
        
        Args:
            model_name: Name of the model to unload
        """
        if model_name in self.models:
            del self.models[model_name]
            logger.info(f"Model '{model_name}' unloaded")
        else:
            raise KeyError(f"Model '{model_name}' not found")
    
    def list_models(self) -> list:
        """
        List all loaded models.
        
        Returns:
            List of model names
        """
        return list(self.models.keys())
