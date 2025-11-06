"""
XGBoost Model for Predictive Maintenance
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional
import xgboost as xgb
from .base_model import BaseModel
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class XGBoostModel(BaseModel):
    """XGBoost classifier for equipment failure prediction."""
    
    def __init__(self, config: Dict):
        """
        Initialize XGBoost model.
        
        Args:
            config: Configuration dictionary
        """
        super().__init__("XGBoost", config)
        self.model_config = config.get('models', {}).get('xgboost', {})
    
    def build_model(self):
        """Build XGBoost model."""
        self.model = xgb.XGBClassifier(
            n_estimators=self.model_config.get('n_estimators', 100),
            max_depth=self.model_config.get('max_depth', 6),
            learning_rate=self.model_config.get('learning_rate', 0.1),
            subsample=self.model_config.get('subsample', 0.8),
            colsample_bytree=self.model_config.get('colsample_bytree', 0.8),
            random_state=self.model_config.get('random_state', 42),
            use_label_encoder=False,
            eval_metric='logloss'
        )
        logger.info("XGBoost model built")
    
    def train(self, X_train: pd.DataFrame, y_train: pd.Series,
              X_val: Optional[pd.DataFrame] = None,
              y_val: Optional[pd.Series] = None) -> Dict:
        """
        Train the XGBoost model.
        
        Args:
            X_train: Training features
            y_train: Training labels
            X_val: Validation features
            y_val: Validation labels
            
        Returns:
            Training metrics dictionary
        """
        if self.model is None:
            self.build_model()
        
        logger.info(f"Training {self.model_name} on {len(X_train)} samples...")
        
        # Store feature names
        self.feature_names = X_train.columns.tolist()
        
        # Prepare evaluation set
        eval_set = [(X_train, y_train)]
        if X_val is not None and y_val is not None:
            eval_set.append((X_val, y_val))
        
        # Train model
        self.model.fit(
            X_train, y_train,
            eval_set=eval_set,
            verbose=False
        )
        self.is_trained = True
        
        # Evaluate on training data
        train_metrics = self.evaluate(X_train, y_train)
        train_metrics = {f'train_{k}': v for k, v in train_metrics.items()}
        
        # Evaluate on validation data if provided
        if X_val is not None and y_val is not None:
            val_metrics = self.evaluate(X_val, y_val)
            val_metrics = {f'val_{k}': v for k, v in val_metrics.items()}
            train_metrics.update(val_metrics)
        
        logger.info(f"{self.model_name} training completed")
        return train_metrics
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Make binary predictions.
        
        Args:
            X: Features for prediction
            
        Returns:
            Binary predictions
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
        
        return self.model.predict(X)
    
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """
        Predict failure probabilities.
        
        Args:
            X: Features for prediction
            
        Returns:
            Probability predictions
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
        
        return self.model.predict_proba(X)
