"""
LSTM Model for Predictive Maintenance
Time-series deep learning model for failure prediction.
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from .base_model import BaseModel
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LSTMModel(BaseModel):
    """LSTM neural network for equipment failure prediction."""
    
    def __init__(self, config: Dict):
        """
        Initialize LSTM model.
        
        Args:
            config: Configuration dictionary
        """
        super().__init__("LSTM", config)
        self.model_config = config.get('models', {}).get('lstm', {})
        self.sequence_length = self.model_config.get('sequence_length', 60)
        self.scaler = None
    
    def prepare_sequences(self, X: pd.DataFrame, y: Optional[pd.Series] = None
                         ) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """
        Prepare sequential data for LSTM.
        
        Args:
            X: Features
            y: Labels (optional)
            
        Returns:
            Tuple of (X_sequences, y_sequences)
        """
        from sklearn.preprocessing import StandardScaler
        
        # Scale features if not already scaled
        if self.scaler is None:
            self.scaler = StandardScaler()
            X_scaled = self.scaler.fit_transform(X)
        else:
            X_scaled = self.scaler.transform(X)
        
        # Create sequences
        X_sequences = []
        y_sequences = []
        
        for i in range(len(X_scaled) - self.sequence_length):
            X_sequences.append(X_scaled[i:i + self.sequence_length])
            if y is not None:
                y_sequences.append(y.iloc[i + self.sequence_length])
        
        X_sequences = np.array(X_sequences)
        y_sequences = np.array(y_sequences) if y is not None else None
        
        logger.info(f"Created {len(X_sequences)} sequences of length {self.sequence_length}")
        return X_sequences, y_sequences
    
    def build_model(self, input_shape: Tuple):
        """
        Build LSTM model architecture.
        
        Args:
            input_shape: Shape of input (sequence_length, n_features)
        """
        units = self.model_config.get('units', [64, 32])
        dropout = self.model_config.get('dropout', 0.2)
        learning_rate = self.model_config.get('learning_rate', 0.001)
        
        model = keras.Sequential()
        
        # First LSTM layer
        model.add(layers.LSTM(
            units[0],
            return_sequences=len(units) > 1,
            input_shape=input_shape
        ))
        model.add(layers.Dropout(dropout))
        
        # Additional LSTM layers
        for i, unit in enumerate(units[1:], 1):
            model.add(layers.LSTM(
                unit,
                return_sequences=i < len(units) - 1
            ))
            model.add(layers.Dropout(dropout))
        
        # Output layer
        model.add(layers.Dense(1, activation='sigmoid'))
        
        # Compile model
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=learning_rate),
            loss='binary_crossentropy',
            metrics=['accuracy', 'precision', 'recall']
        )
        
        self.model = model
        logger.info("LSTM model architecture built")
        logger.info(f"Model summary:\n{model.summary()}")
    
    def train(self, X_train: pd.DataFrame, y_train: pd.Series,
              X_val: Optional[pd.DataFrame] = None,
              y_val: Optional[pd.Series] = None) -> Dict:
        """
        Train the LSTM model.
        
        Args:
            X_train: Training features
            y_train: Training labels
            X_val: Validation features
            y_val: Validation labels
            
        Returns:
            Training metrics dictionary
        """
        logger.info(f"Training {self.model_name} on {len(X_train)} samples...")
        
        # Store feature names
        self.feature_names = X_train.columns.tolist()
        
        # Prepare sequences
        X_train_seq, y_train_seq = self.prepare_sequences(X_train, y_train)
        
        validation_data = None
        if X_val is not None and y_val is not None:
            X_val_seq, y_val_seq = self.prepare_sequences(X_val, y_val)
            validation_data = (X_val_seq, y_val_seq)
        
        # Build model if not already built
        if self.model is None:
            input_shape = (X_train_seq.shape[1], X_train_seq.shape[2])
            self.build_model(input_shape)
        
        # Train model
        batch_size = self.model_config.get('batch_size', 32)
        epochs = self.model_config.get('epochs', 50)
        
        history = self.model.fit(
            X_train_seq, y_train_seq,
            validation_data=validation_data,
            batch_size=batch_size,
            epochs=epochs,
            verbose=1,
            callbacks=[
                keras.callbacks.EarlyStopping(
                    monitor='val_loss' if validation_data else 'loss',
                    patience=10,
                    restore_best_weights=True
                )
            ]
        )
        
        self.is_trained = True
        
        # Extract metrics
        metrics = {
            'train_loss': float(history.history['loss'][-1]),
            'train_accuracy': float(history.history['accuracy'][-1])
        }
        
        if validation_data:
            metrics.update({
                'val_loss': float(history.history['val_loss'][-1]),
                'val_accuracy': float(history.history['val_accuracy'][-1])
            })
        
        logger.info(f"{self.model_name} training completed")
        return metrics
    
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
        
        X_seq, _ = self.prepare_sequences(X)
        predictions = self.model.predict(X_seq, verbose=0)
        return (predictions > 0.5).astype(int).flatten()
    
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
        
        X_seq, _ = self.prepare_sequences(X)
        predictions = self.model.predict(X_seq, verbose=0)
        
        # Return probabilities for both classes
        proba = np.column_stack([1 - predictions, predictions])
        return proba
