"""
Data Splitter Module
Handles train/validation/test data splitting with proper time-series considerations.
"""

import pandas as pd
import numpy as np
from typing import Tuple, Optional
from sklearn.model_selection import train_test_split
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataSplitter:
    """Split data into train, validation, and test sets."""
    
    def __init__(self, config: dict):
        """
        Initialize data splitter with configuration.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        training_config = config.get('training', {})
        self.test_size = training_config.get('test_size', 0.2)
        self.validation_size = training_config.get('validation_size', 0.1)
        self.random_state = training_config.get('random_state', 42)
    
    def time_series_split(self, df: pd.DataFrame, 
                         target_column: str = 'is_failing') -> Tuple:
        """
        Split data chronologically for time series.
        
        Args:
            df: Input DataFrame
            target_column: Name of target column
            
        Returns:
            Tuple of (X_train, X_val, X_test, y_train, y_val, y_test)
        """
        logger.info("Performing time-series split...")
        
        # Ensure data is sorted by timestamp
        if 'timestamp' in df.columns:
            df = df.sort_values('timestamp').reset_index(drop=True)
        
        # Calculate split indices
        n = len(df)
        test_idx = int(n * (1 - self.test_size))
        val_idx = int(test_idx * (1 - self.validation_size))
        
        # Split chronologically
        train_df = df.iloc[:val_idx]
        val_df = df.iloc[val_idx:test_idx]
        test_df = df.iloc[test_idx:]
        
        # Separate features and target
        feature_columns = [col for col in df.columns if col not in 
                          [target_column, 'timestamp', 'equipment_id', 'status']]
        
        X_train = train_df[feature_columns]
        X_val = val_df[feature_columns]
        X_test = test_df[feature_columns]
        
        y_train = train_df[target_column] if target_column in df.columns else None
        y_val = val_df[target_column] if target_column in df.columns else None
        y_test = test_df[target_column] if target_column in df.columns else None
        
        logger.info(f"Train set: {len(X_train)} samples")
        logger.info(f"Validation set: {len(X_val)} samples")
        logger.info(f"Test set: {len(X_test)} samples")
        
        return X_train, X_val, X_test, y_train, y_val, y_test
    
    def random_split(self, df: pd.DataFrame, 
                    target_column: str = 'is_failing',
                    stratify: bool = True) -> Tuple:
        """
        Random split with optional stratification.
        
        Args:
            df: Input DataFrame
            target_column: Name of target column
            stratify: Whether to stratify based on target
            
        Returns:
            Tuple of (X_train, X_val, X_test, y_train, y_val, y_test)
        """
        logger.info("Performing random split...")
        
        # Separate features and target
        feature_columns = [col for col in df.columns if col not in 
                          [target_column, 'timestamp', 'equipment_id', 'status']]
        
        X = df[feature_columns]
        y = df[target_column] if target_column in df.columns else None
        
        # First split: train+val vs test
        stratify_param = y if stratify and y is not None else None
        
        X_temp, X_test, y_temp, y_test = train_test_split(
            X, y,
            test_size=self.test_size,
            random_state=self.random_state,
            stratify=stratify_param
        )
        
        # Second split: train vs val
        val_size_adjusted = self.validation_size / (1 - self.test_size)
        stratify_param = y_temp if stratify and y_temp is not None else None
        
        X_train, X_val, y_train, y_val = train_test_split(
            X_temp, y_temp,
            test_size=val_size_adjusted,
            random_state=self.random_state,
            stratify=stratify_param
        )
        
        logger.info(f"Train set: {len(X_train)} samples")
        logger.info(f"Validation set: {len(X_val)} samples")
        logger.info(f"Test set: {len(X_test)} samples")
        
        return X_train, X_val, X_test, y_train, y_val, y_test
    
    def save_splits(self, splits: Tuple, output_dir: str):
        """
        Save train/val/test splits to files.
        
        Args:
            splits: Tuple of (X_train, X_val, X_test, y_train, y_val, y_test)
            output_dir: Output directory path
        """
        from pathlib import Path
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        X_train, X_val, X_test, y_train, y_val, y_test = splits
        
        # Save features
        X_train.to_csv(output_path / 'X_train.csv', index=False)
        X_val.to_csv(output_path / 'X_val.csv', index=False)
        X_test.to_csv(output_path / 'X_test.csv', index=False)
        
        # Save targets
        if y_train is not None:
            pd.DataFrame({'target': y_train}).to_csv(output_path / 'y_train.csv', index=False)
            pd.DataFrame({'target': y_val}).to_csv(output_path / 'y_val.csv', index=False)
            pd.DataFrame({'target': y_test}).to_csv(output_path / 'y_test.csv', index=False)
        
        logger.info(f"Splits saved to {output_dir}")


def main():
    """Main function for testing data splitter."""
    config = {
        'training': {
            'test_size': 0.2,
            'validation_size': 0.1,
            'random_state': 42
        }
    }
    
    splitter = DataSplitter(config)
    logger.info("Data splitter module ready")


if __name__ == "__main__":
    main()
