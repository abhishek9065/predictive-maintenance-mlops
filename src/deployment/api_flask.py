"""
Flask-based ML Model Serving API
Alternative implementation to FastAPI
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path

from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib
import numpy as np
import pandas as pd
from prometheus_client import Counter, Histogram, generate_latest
from werkzeug.exceptions import BadRequest, InternalServerError

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Prometheus metrics
prediction_counter = Counter('predictions_total', 'Total number of predictions made')
prediction_latency = Histogram('prediction_latency_seconds', 'Prediction latency in seconds')
error_counter = Counter('prediction_errors_total', 'Total number of prediction errors')

class ModelStore:
    """Global model storage"""
    def __init__(self):
        self.model = None
        self.scaler = None
        self.metadata = None
        self.model_path = Path(os.getenv("MODEL_PATH", "models/production"))
    
    def load_model(self):
        """Load model from disk"""
        try:
            # Load model
            model_file = self.model_path / "model.pkl"
            if not model_file.exists():
                logger.warning(f"Model not found at {model_file}, trying alternate location")
                model_file = Path("models/staging/model.pkl")
            
            if model_file.exists():
                self.model = joblib.load(model_file)
                logger.info(f"Model loaded from {model_file}")
            else:
                logger.error("No model file found")
                return False
            
            # Load scaler if exists
            scaler_file = self.model_path / "scaler.pkl"
            if scaler_file.exists():
                self.scaler = joblib.load(scaler_file)
                logger.info(f"Scaler loaded from {scaler_file}")
            
            # Load metadata
            metadata_file = self.model_path / "metadata.json"
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    self.metadata = json.load(f)
                logger.info(f"Metadata loaded: {self.metadata.get('model_type', 'Unknown')}")
            
            return True
        
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return False
    
    def predict(self, data: np.ndarray) -> tuple:
        """Make predictions"""
        if self.model is None:
            raise ValueError("Model not loaded")
        
        # Scale data if scaler is available
        if self.scaler is not None:
            data = self.scaler.transform(data)
        
        # Make predictions
        predictions = self.model.predict(data)
        
        # Get probabilities if available
        try:
            probabilities = self.model.predict_proba(data).tolist()
        except AttributeError:
            probabilities = None
        
        return predictions.tolist(), probabilities

# Initialize model store
model_store = ModelStore()

@app.before_first_request
def startup():
    """Load model on startup"""
    logger.info("Starting Flask application...")
    success = model_store.load_model()
    if success:
        logger.info("Model loaded successfully")
    else:
        logger.warning("Failed to load model - predictions will fail")

@app.route('/', methods=['GET'])
def root():
    """Root endpoint"""
    return jsonify({
        "message": "Predictive Maintenance API (Flask)",
        "version": "2.0.0",
        "endpoints": {
            "health": "/health",
            "predict": "/predict",
            "metrics": "/metrics",
            "model_info": "/model/info"
        }
    })

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy" if model_store.model is not None else "degraded",
        "model_loaded": model_store.model is not None,
        "model_version": model_store.metadata.get('version', 'unknown') if model_store.metadata else None,
        "timestamp": datetime.now().isoformat()
    })

@app.route('/predict', methods=['POST'])
def predict():
    """Make predictions on sensor data"""
    try:
        start_time = datetime.now()
        
        # Check if model is loaded
        if model_store.model is None:
            error_counter.inc()
            return jsonify({"error": "Model not loaded"}), 503
        
        # Get request data
        data = request.get_json()
        if not data or 'data' not in data:
            raise BadRequest("Invalid request format. Expected {'data': [...]}")
        
        # Validate request
        sensor_data = data['data']
        if not isinstance(sensor_data, list) or len(sensor_data) == 0:
            raise BadRequest("Data must be a non-empty list")
        
        if len(sensor_data) > 1000:
            raise BadRequest("Maximum batch size is 1000")
        
        # Required fields
        required_fields = ['temperature', 'vibration', 'pressure', 'rpm', 'power_consumption']
        
        # Validate each record
        for i, record in enumerate(sensor_data):
            for field in required_fields:
                if field not in record:
                    raise BadRequest(f"Missing field '{field}' in record {i}")
                
                value = record[field]
                if not isinstance(value, (int, float)):
                    raise BadRequest(f"Invalid type for field '{field}' in record {i}")
                
                if np.isnan(value) or np.isinf(value):
                    raise BadRequest(f"Invalid numeric value for field '{field}' in record {i}")
        
        # Convert to DataFrame
        df = pd.DataFrame(sensor_data)
        
        # Make predictions
        predictions, probabilities = model_store.predict(df.values)
        
        # Update metrics
        prediction_counter.inc(len(predictions))
        prediction_latency.observe((datetime.now() - start_time).total_seconds())
        
        # Prepare response
        response = {
            "predictions": predictions,
            "timestamp": datetime.now().isoformat(),
            "model_version": model_store.metadata.get('version', 'unknown') if model_store.metadata else 'unknown',
            "count": len(predictions)
        }
        
        # Add probabilities if requested
        if data.get('return_probability', True) and probabilities is not None:
            response['probabilities'] = probabilities
        
        logger.info(f"Predictions made: {len(predictions)}")
        return jsonify(response)
    
    except BadRequest as e:
        error_counter.inc()
        logger.warning(f"Bad request: {e}")
        return jsonify({"error": str(e)}), 400
    
    except Exception as e:
        error_counter.inc()
        logger.error(f"Prediction error: {e}")
        return jsonify({"error": f"Prediction failed: {str(e)}"}), 500

@app.route('/metrics', methods=['GET'])
def metrics():
    """Prometheus metrics endpoint"""
    return generate_latest()

@app.route('/model/info', methods=['GET'])
def model_info():
    """Get model information"""
    if model_store.metadata is None:
        return jsonify({"error": "Model metadata not available"}), 404
    
    return jsonify({
        "model_type": model_store.metadata.get('model_type', 'unknown'),
        "version": model_store.metadata.get('version', 'unknown'),
        "training_date": model_store.metadata.get('training_date', 'unknown'),
        "metrics": model_store.metadata.get('metrics', {}),
        "features": model_store.metadata.get('features', [])
    })

@app.route('/model/metrics', methods=['GET'])
def model_metrics():
    """Get model performance metrics"""
    if model_store.metadata is None:
        return jsonify({"error": "Model metadata not available"}), 404
    
    metrics = model_store.metadata.get('metrics', {})
    
    return jsonify({
        "accuracy": metrics.get('accuracy', 0.0),
        "precision": metrics.get('precision', 0.0),
        "recall": metrics.get('recall', 0.0),
        "f1_score": metrics.get('f1_score', 0.0),
        "model_type": model_store.metadata.get('model_type', 'unknown'),
        "training_date": model_store.metadata.get('training_date', 'unknown')
    })

@app.route('/model/reload', methods=['POST'])
def reload_model():
    """Reload model from disk"""
    try:
        success = model_store.load_model()
        if success:
            return jsonify({"status": "success", "message": "Model reloaded successfully"})
        else:
            return jsonify({"error": "Failed to reload model"}), 500
    except Exception as e:
        logger.error(f"Error reloading model: {e}")
        return jsonify({"error": f"Reload failed: {str(e)}"}), 500

@app.errorhandler(Exception)
def handle_error(error):
    """Global error handler"""
    logger.error(f"Unhandled exception: {error}")
    return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=8000,
        debug=False
    )
