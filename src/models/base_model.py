"""
Base Model Abstract Class
Defines the interface for all predictive maintenance models.
"""

from abc import ABC, abstractmethod
import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple, Optional
import joblib
import json
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BaseModel(ABC):
    """Abstract base class for all predictive maintenance models."""
    
    def __init__(self, model_name: str, config: Dict):
        """
        Initialize base model.
        
        Args:
            model_name: Name of the model
            config: Model configuration dictionary
        """
        self.model_name = model_name
        self.config = config
        self.model = None
        self.is_trained = False
        self.feature_names = None
        self.metrics = {}
    
    @abstractmethod
    def build_model(self):
        """Build the model architecture/structure."""
        pass
    
    @abstractmethod
    def train(self, X_train: pd.DataFrame, y_train: pd.Series,
              X_val: Optional[pd.DataFrame] = None,
              y_val: Optional[pd.Series] = None) -> Dict:
        """
        Train the model.
        
        Args:
            X_train: Training features
            y_train: Training labels
            X_val: Validation features
            y_val: Validation labels
            
        Returns:
            Dictionary with training metrics
        """
        pass
    
    @abstractmethod
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Make predictions.
        
        Args:
            X: Features for prediction
            
        Returns:
            Predictions array
        """
        pass
    
    @abstractmethod
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """
        Predict probabilities.
        
        Args:
            X: Features for prediction
            
        Returns:
            Probability array
        """
        pass
    
    def evaluate(self, X: pd.DataFrame, y: pd.Series) -> Dict:
        """
        Evaluate model performance.
        
        Args:
            X: Features
            y: True labels
            
        Returns:
            Dictionary with evaluation metrics
        """
        from sklearn.metrics import (
            accuracy_score, precision_score, recall_score,
            f1_score, roc_auc_score, confusion_matrix
        )
        
        y_pred = self.predict(X)
        y_pred_proba = self.predict_proba(X)[:, 1]
        
        metrics = {
            'accuracy': accuracy_score(y, y_pred),
            'precision': precision_score(y, y_pred, average='binary'),
            'recall': recall_score(y, y_pred, average='binary'),
            'f1_score': f1_score(y, y_pred, average='binary'),
            'roc_auc': roc_auc_score(y, y_pred_proba),
            'confusion_matrix': confusion_matrix(y, y_pred).tolist()
        }
        
        self.metrics = metrics
        logger.info(f"{self.model_name} Evaluation Metrics:")
        for metric, value in metrics.items():
            if metric != 'confusion_matrix':
                logger.info(f"  {metric}: {value:.4f}")
        
        return metrics
    
    def save_model(self, file_path: str):
        """
        Save model to disk.
        
        Args:
            file_path: Path to save the model
        """
        if not self.is_trained:
            logger.warning("Model is not trained. Saving untrained model.")
        
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        
        model_data = {
            'model': self.model,
            'model_name': self.model_name,
            'config': self.config,
            'feature_names': self.feature_names,
            'metrics': self.metrics,
            'is_trained': self.is_trained
        }
        
        joblib.dump(model_data, file_path)
        logger.info(f"Model saved to {file_path}")
    
    def load_model(self, file_path: str):
        """
        Load model from disk.
        
        Args:
            file_path: Path to load the model from
        """
        model_data = joblib.load(file_path)
        
        self.model = model_data['model']
        self.model_name = model_data.get('model_name', self.model_name)
        self.config = model_data.get('config', self.config)
        self.feature_names = model_data.get('feature_names')
        self.metrics = model_data.get('metrics', {})
        self.is_trained = model_data.get('is_trained', True)
        
        logger.info(f"Model loaded from {file_path}")
    
    def get_feature_importance(self) -> Optional[pd.DataFrame]:
        """
        Get feature importance scores.
        
        Returns:
            DataFrame with feature importance (if available)
        """
        if not hasattr(self.model, 'feature_importances_'):
            logger.warning(f"{self.model_name} does not support feature importance")
            return None
        
        importance_df = pd.DataFrame({
            'feature': self.feature_names,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        return importance_df
    
    def save_metrics(self, file_path: str):
        """
        Save metrics to JSON file.
        
        Args:
            file_path: Path to save metrics
        """
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w') as f:
            json.dump(self.metrics, f, indent=2)
        
        logger.info(f"Metrics saved to {file_path}")
    
    def __repr__(self) -> str:
        """String representation of the model."""
        return (f"{self.__class__.__name__}(model_name='{self.model_name}', "
                f"is_trained={self.is_trained})")
