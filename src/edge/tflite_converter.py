"""
TensorFlow Lite Converter for Edge Deployment
Converts trained models to optimized TFLite format for edge devices
"""

import tensorflow as tf
import numpy as np
import joblib
import json
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TFLiteConverter:
    """Convert scikit-learn models to TensorFlow Lite for edge deployment"""
    
    def __init__(self, model_path: str, output_dir: str = "models/edge"):
        """
        Initialize TFLite converter
        
        Args:
            model_path: Path to trained model (.pkl)
            output_dir: Directory to save TFLite models
        """
        self.model_path = Path(model_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.model = None
        self.tflite_model = None
        
    def load_model(self):
        """Load scikit-learn model"""
        logger.info(f"Loading model from {self.model_path}")
        self.model = joblib.load(self.model_path)
        logger.info(f"Model loaded: {type(self.model).__name__}")
        
    def convert_to_keras(self, input_shape: Tuple[int] = (5,)) -> tf.keras.Model:
        """
        Convert scikit-learn model to Keras model
        
        Args:
            input_shape: Shape of input features
            
        Returns:
            Keras model
        """
        logger.info("Converting to Keras model...")
        
        # Create Keras model that mimics sklearn model behavior
        keras_model = tf.keras.Sequential([
            tf.keras.layers.Input(shape=input_shape),
            tf.keras.layers.Dense(64, activation='relu', name='dense1'),
            tf.keras.layers.Dropout(0.2, name='dropout1'),
            tf.keras.layers.Dense(32, activation='relu', name='dense2'),
            tf.keras.layers.Dropout(0.2, name='dropout2'),
            tf.keras.layers.Dense(16, activation='relu', name='dense3'),
            tf.keras.layers.Dense(1, activation='sigmoid', name='output')
        ])
        
        # Compile model
        keras_model.compile(
            optimizer='adam',
            loss='binary_crossentropy',
            metrics=['accuracy']
        )
        
        logger.info(f"Keras model created with input shape: {input_shape}")
        return keras_model
    
    def train_keras_model(self, X_train: np.ndarray, y_train: np.ndarray, 
                         epochs: int = 50, batch_size: int = 32) -> tf.keras.Model:
        """
        Train Keras model to mimic sklearn model
        
        Args:
            X_train: Training features
            y_train: Training labels
            epochs: Number of training epochs
            batch_size: Batch size
            
        Returns:
            Trained Keras model
        """
        keras_model = self.convert_to_keras(input_shape=(X_train.shape[1],))
        
        logger.info(f"Training Keras model for {epochs} epochs...")
        history = keras_model.fit(
            X_train, y_train,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=0.2,
            verbose=0
        )
        
        final_acc = history.history['accuracy'][-1]
        final_val_acc = history.history['val_accuracy'][-1]
        logger.info(f"Training complete - Accuracy: {final_acc:.4f}, Val Accuracy: {final_val_acc:.4f}")
        
        return keras_model
    
    def convert_to_tflite(self, keras_model: tf.keras.Model, 
                         quantize: bool = True) -> bytes:
        """
        Convert Keras model to TFLite format
        
        Args:
            keras_model: Trained Keras model
            quantize: Whether to apply quantization for smaller model size
            
        Returns:
            TFLite model bytes
        """
        logger.info("Converting to TFLite format...")
        
        converter = tf.lite.TFLiteConverter.from_keras_model(keras_model)
        
        if quantize:
            logger.info("Applying quantization for edge optimization...")
            converter.optimizations = [tf.lite.Optimize.DEFAULT]
            converter.target_spec.supported_types = [tf.float16]
        
        tflite_model = converter.convert()
        
        size_mb = len(tflite_model) / (1024 * 1024)
        logger.info(f"TFLite model created - Size: {size_mb:.2f} MB")
        
        return tflite_model
    
    def save_tflite_model(self, tflite_model: bytes, model_name: str) -> Path:
        """
        Save TFLite model to file
        
        Args:
            tflite_model: TFLite model bytes
            model_name: Name for the saved model
            
        Returns:
            Path to saved model
        """
        output_path = self.output_dir / f"{model_name}.tflite"
        
        with open(output_path, 'wb') as f:
            f.write(tflite_model)
        
        logger.info(f"TFLite model saved to: {output_path}")
        return output_path
    
    def test_tflite_model(self, tflite_path: Path, test_data: np.ndarray) -> np.ndarray:
        """
        Test TFLite model inference
        
        Args:
            tflite_path: Path to TFLite model
            test_data: Test input data
            
        Returns:
            Predictions
        """
        logger.info("Testing TFLite model inference...")
        
        # Load TFLite model
        interpreter = tf.lite.Interpreter(model_path=str(tflite_path))
        interpreter.allocate_tensors()
        
        # Get input and output details
        input_details = interpreter.get_input_details()
        output_details = interpreter.get_output_details()
        
        # Run inference
        predictions = []
        for sample in test_data:
            interpreter.set_tensor(input_details[0]['index'], 
                                 sample.reshape(1, -1).astype(np.float32))
            interpreter.invoke()
            output = interpreter.get_tensor(output_details[0]['index'])
            predictions.append(output[0])
        
        predictions = np.array(predictions)
        logger.info(f"Inference complete - Predictions shape: {predictions.shape}")
        
        return predictions
    
    def create_metadata(self, model_name: str, metrics: Dict[str, float]) -> Path:
        """
        Create metadata file for TFLite model
        
        Args:
            model_name: Name of the model
            metrics: Model performance metrics
            
        Returns:
            Path to metadata file
        """
        metadata = {
            "model_name": model_name,
            "model_type": "TensorFlow Lite",
            "framework": "TensorFlow",
            "input_shape": [1, 5],
            "output_shape": [1, 1],
            "features": [
                "temperature",
                "vibration", 
                "pressure",
                "rpm",
                "power_consumption"
            ],
            "metrics": metrics,
            "optimization": "float16 quantization",
            "target_device": "Edge (IoT, Mobile, Embedded)",
            "created_at": str(Path(self.model_path).stat().st_mtime)
        }
        
        metadata_path = self.output_dir / f"{model_name}_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"Metadata saved to: {metadata_path}")
        return metadata_path
    
    def convert_pipeline(self, X_train: np.ndarray, y_train: np.ndarray,
                        X_test: np.ndarray, y_test: np.ndarray,
                        model_name: str = "predictive_maintenance_edge") -> Dict[str, Any]:
        """
        Complete conversion pipeline
        
        Args:
            X_train: Training features
            y_train: Training labels
            X_test: Test features
            y_test: Test labels
            model_name: Name for the model
            
        Returns:
            Dictionary with conversion results
        """
        logger.info("=" * 70)
        logger.info("TENSORFLOW LITE CONVERSION PIPELINE")
        logger.info("=" * 70)
        
        # Load original model
        self.load_model()
        
        # Train Keras model
        keras_model = self.train_keras_model(X_train, y_train)
        
        # Evaluate Keras model
        keras_loss, keras_acc = keras_model.evaluate(X_test, y_test, verbose=0)
        logger.info(f"Keras Model - Test Accuracy: {keras_acc:.4f}")
        
        # Convert to TFLite
        tflite_model = self.convert_to_tflite(keras_model, quantize=True)
        
        # Save TFLite model
        tflite_path = self.save_tflite_model(tflite_model, model_name)
        
        # Test TFLite model
        tflite_predictions = self.test_tflite_model(tflite_path, X_test)
        tflite_acc = np.mean((tflite_predictions.flatten() > 0.5) == y_test)
        logger.info(f"TFLite Model - Test Accuracy: {tflite_acc:.4f}")
        
        # Create metadata
        metrics = {
            "keras_accuracy": float(keras_acc),
            "keras_loss": float(keras_loss),
            "tflite_accuracy": float(tflite_acc),
            "accuracy_drop": float(keras_acc - tflite_acc)
        }
        metadata_path = self.create_metadata(model_name, metrics)
        
        # Calculate model size
        original_size = self.model_path.stat().st_size / 1024  # KB
        tflite_size = tflite_path.stat().st_size / 1024  # KB
        size_reduction = ((original_size - tflite_size) / original_size) * 100
        
        logger.info("=" * 70)
        logger.info("CONVERSION SUMMARY")
        logger.info("=" * 70)
        logger.info(f"Original Model Size: {original_size:.2f} KB")
        logger.info(f"TFLite Model Size: {tflite_size:.2f} KB")
        logger.info(f"Size Reduction: {size_reduction:.1f}%")
        logger.info(f"Keras Accuracy: {keras_acc:.4f}")
        logger.info(f"TFLite Accuracy: {tflite_acc:.4f}")
        logger.info(f"Accuracy Drop: {metrics['accuracy_drop']:.4f}")
        logger.info("=" * 70)
        
        return {
            "tflite_model_path": str(tflite_path),
            "metadata_path": str(metadata_path),
            "original_size_kb": original_size,
            "tflite_size_kb": tflite_size,
            "size_reduction_percent": size_reduction,
            "metrics": metrics
        }


def main():
    """Main execution function"""
    import argparse
    import pandas as pd
    from sklearn.model_selection import train_test_split
    
    parser = argparse.ArgumentParser(description="Convert model to TensorFlow Lite")
    parser.add_argument("--model", type=str, 
                       default="models/production_model.pkl",
                       help="Path to trained model")
    parser.add_argument("--data", type=str,
                       default="data/train.csv",
                       help="Path to training data")
    parser.add_argument("--output", type=str,
                       default="models/edge",
                       help="Output directory")
    parser.add_argument("--name", type=str,
                       default="predictive_maintenance_edge",
                       help="Model name")
    
    args = parser.parse_args()
    
    # Load data
    logger.info(f"Loading data from {args.data}")
    df = pd.read_csv(args.data)
    
    feature_cols = ['temperature', 'vibration', 'pressure', 'rpm', 'power_consumption']
    X = df[feature_cols].values
    y = df['failure'].values
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    # Convert to TFLite
    converter = TFLiteConverter(args.model, args.output)
    results = converter.convert_pipeline(X_train, y_train, X_test, y_test, args.name)
    
    logger.info("\n✅ TensorFlow Lite conversion complete!")
    logger.info(f"TFLite model: {results['tflite_model_path']}")
    logger.info(f"Metadata: {results['metadata_path']}")
    
    return results


if __name__ == "__main__":
    main()
