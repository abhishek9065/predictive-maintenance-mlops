"""
Training Script
Main script for model training with MLflow tracking.
"""

import yaml
import pandas as pd
import mlflow
import argparse
from pathlib import Path
import sys

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.models import RandomForestModel, XGBoostModel, LSTMModel
from src.preprocessing import DataCleaner, FeatureEngineer, DataSplitter
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def load_config(config_path: str = 'config/config.yaml'):
    """Load configuration from YAML file."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def prepare_data(config: dict):
    """Prepare data for training."""
    logger.info("Starting data preparation...")
    
    # Load raw data
    data_path = Path(config['data']['raw_data_path'])
    data_files = sorted(data_path.glob('historical_data_*.json'))
    
    if not data_files:
        raise FileNotFoundError("No training data found. Run data collection first.")
    
    latest_file = data_files[-1]
    logger.info(f"Using data file: {latest_file}")
    
    # Clean data
    cleaner = DataCleaner(config)
    df = cleaner.load_data(str(latest_file))
    df_clean = cleaner.clean_pipeline(df, remove_outliers=True)
    
    # Engineer features
    engineer = FeatureEngineer(config)
    df_features = engineer.engineer_features_pipeline(df_clean)
    
    # Save features
    features_path = Path(config['data']['features_path']) / 'features.csv'
    features_path.parent.mkdir(parents=True, exist_ok=True)
    df_features.to_csv(features_path, index=False)
    
    logger.info(f"Data preparation completed. Features saved to {features_path}")
    return df_features


def train_model(config: dict, model_type: str, X_train, X_val, X_test, y_train, y_val, y_test):
    """Train a specific model type."""
    logger.info(f"\n{'='*60}")
    logger.info(f"Training {model_type.upper()} model")
    logger.info(f"{'='*60}")
    
    # Select model class
    model_classes = {
        'random_forest': RandomForestModel,
        'xgboost': XGBoostModel,
        'lstm': LSTMModel
    }
    
    if model_type not in model_classes:
        raise ValueError(f"Unknown model type: {model_type}")
    
    # Create model
    model = model_classes[model_type](config)
    
    # Start MLflow run
    with mlflow.start_run(run_name=f"{model_type}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}"):
        # Log parameters
        mlflow.log_params(config['models'].get(model_type, {}))
        mlflow.log_param('model_type', model_type)
        mlflow.log_param('train_samples', len(X_train))
        mlflow.log_param('val_samples', len(X_val))
        mlflow.log_param('test_samples', len(X_test))
        
        # Train model
        train_metrics = model.train(X_train, y_train, X_val, y_val)
        
        # Log training metrics
        mlflow.log_metrics(train_metrics)
        
        # Evaluate on test set
        test_metrics = model.evaluate(X_test, y_test)
        test_metrics_log = {f'test_{k}': v for k, v in test_metrics.items() 
                           if k != 'confusion_matrix'}
        mlflow.log_metrics(test_metrics_log)
        
        # Log confusion matrix
        if 'confusion_matrix' in test_metrics:
            mlflow.log_text(str(test_metrics['confusion_matrix']), 'confusion_matrix.txt')
        
        # Save model
        model_path = Path('models') / f'{model_type}_model.pkl'
        model_path.parent.mkdir(parents=True, exist_ok=True)
        model.save_model(str(model_path))
        
        # Log model artifact
        mlflow.log_artifact(str(model_path))
        
        # Log feature importance if available
        feature_importance = model.get_feature_importance()
        if feature_importance is not None:
            importance_path = Path('models') / f'{model_type}_feature_importance.csv'
            feature_importance.to_csv(importance_path, index=False)
            mlflow.log_artifact(str(importance_path))
        
        logger.info(f"\nTest Metrics for {model_type}:")
        for metric, value in test_metrics_log.items():
            logger.info(f"  {metric}: {value:.4f}")
    
    return model, test_metrics


def main():
    """Main training function."""
    parser = argparse.ArgumentParser(description='Train predictive maintenance models')
    parser.add_argument('--config', type=str, default='config/config.yaml',
                       help='Path to configuration file')
    parser.add_argument('--models', nargs='+', 
                       default=['random_forest', 'xgboost'],
                       help='Models to train')
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Set up MLflow
    mlflow.set_tracking_uri(config['mlflow']['tracking_uri'])
    mlflow.set_experiment(config['mlflow']['experiment_name'])
    
    logger.info("Starting training pipeline...")
    logger.info(f"Models to train: {args.models}")
    
    # Prepare data
    df_features = prepare_data(config)
    
    # Split data
    logger.info("\nSplitting data...")
    splitter = DataSplitter(config)
    X_train, X_val, X_test, y_train, y_val, y_test = splitter.time_series_split(df_features)
    
    # Save splits
    splitter.save_splits(
        (X_train, X_val, X_test, y_train, y_val, y_test),
        'data/processed'
    )
    
    # Train models
    best_model = None
    best_score = 0
    best_model_name = None
    
    for model_type in args.models:
        try:
            model, metrics = train_model(
                config, model_type,
                X_train, X_val, X_test,
                y_train, y_val, y_test
            )
            
            # Track best model
            f1_score = metrics.get('f1_score', 0)
            if f1_score > best_score:
                best_score = f1_score
                best_model = model
                best_model_name = model_type
        
        except Exception as e:
            logger.error(f"Failed to train {model_type}: {e}")
            continue
    
    # Summary
    logger.info(f"\n{'='*60}")
    logger.info("TRAINING SUMMARY")
    logger.info(f"{'='*60}")
    logger.info(f"Best Model: {best_model_name}")
    logger.info(f"Best F1 Score: {best_score:.4f}")
    logger.info(f"Models saved to: models/")
    logger.info(f"MLflow tracking URI: {config['mlflow']['tracking_uri']}")
    logger.info(f"{'='*60}\n")


if __name__ == "__main__":
    main()
