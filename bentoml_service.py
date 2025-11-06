"""
BentoML Service for Predictive Maintenance
Production-ready ML model serving with BentoML 1.4
"""

import bentoml
import numpy as np
from bentoml.io import JSON
from pydantic import BaseModel
from typing import List
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define input schema
class SensorData(BaseModel):
    temperature: float
    vibration: float
    pressure: float
    rpm: float
    current: float

class BatchSensorData(BaseModel):
    data: List[SensorData]

# Load the model and save to BentoML model store
def save_model_to_bentoml():
    """Save production model to BentoML model store"""
    import joblib
    from pathlib import Path
    
    model_path = Path("models/production_model.pkl")
    
    if not model_path.exists():
        raise FileNotFoundError(f"Model not found at {model_path}")
    
    # Load the model
    model = joblib.load(model_path)
    
    # Save to BentoML
    bento_model = bentoml.sklearn.save_model(
        "predictive_maintenance_model",
        model,
        metadata={
            "framework": "sklearn",
            "model_type": "RandomForestClassifier",
            "accuracy": 0.9546,
            "precision": 0.9770,
            "recall": 0.9209,
            "f1_score": 0.9481,
            "features": ["temperature", "vibration", "pressure", "rpm", "current"],
            "version": "2.0.0"
        },
        labels={
            "stage": "production",
            "owner": "mlops-team"
        }
    )
    
    logger.info(f"✅ Model saved to BentoML: {bento_model.tag}")
    return bento_model

# Create BentoML service
try:
    # Try to get existing model
    model_ref = bentoml.sklearn.get("predictive_maintenance_model:latest")
    logger.info(f"✅ Loaded existing model: {model_ref.tag}")
except bentoml.exceptions.NotFound:
    # Save model if not found
    logger.info("📦 Model not found in BentoML store, saving...")
    model_ref = save_model_to_bentoml()

# Create the runner
predictive_maintenance_runner = bentoml.sklearn.get("predictive_maintenance_model:latest").to_runner()

# Create the service (BentoML 1.4 API)
svc = bentoml.Service("predictive_maintenance")
svc.add_runner(predictive_maintenance_runner)

@svc.api(input=JSON(pydantic_model=SensorData), output=JSON())
async def predict(sensor_data: SensorData) -> dict:
    """
    Single prediction endpoint
    
    Args:
        sensor_data: Sensor readings (temperature, vibration, pressure, rpm, current)
    
    Returns:
        dict: Prediction result with confidence
    """
    try:
        # Prepare features
        features = np.array([[
            sensor_data.temperature,
            sensor_data.vibration,
            sensor_data.pressure,
            sensor_data.rpm,
            sensor_data.current
        ]])
        
        # Make prediction
        prediction = await predictive_maintenance_runner.predict.async_run(features)
        proba = await predictive_maintenance_runner.predict_proba.async_run(features)
        
        # Get confidence (probability of predicted class)
        confidence = float(np.max(proba[0]))
        predicted_class = "failure" if prediction[0] == 1 else "normal"
        
        logger.info(f"Prediction: {predicted_class} (confidence: {confidence:.2%})")
        
        return {
            "prediction": predicted_class,
            "confidence": confidence,
            "probability_normal": float(proba[0][0]),
            "probability_failure": float(proba[0][1]),
            "input_data": {
                "temperature": sensor_data.temperature,
                "vibration": sensor_data.vibration,
                "pressure": sensor_data.pressure,
                "rpm": sensor_data.rpm,
                "current": sensor_data.current
            }
        }
    
    except Exception as e:
        logger.error(f"Prediction error: {str(e)}")
        return {
            "error": str(e),
            "prediction": "error",
            "confidence": 0.0
        }

@svc.api(input=JSON(pydantic_model=BatchSensorData), output=JSON())
async def predict_batch(batch_data: BatchSensorData) -> dict:
    """
    Batch prediction endpoint
    
    Args:
        batch_data: List of sensor readings
    
    Returns:
        dict: Batch prediction results
    """
    try:
        # Prepare features matrix
        features = np.array([[
            data.temperature,
            data.vibration,
            data.pressure,
            data.rpm,
            data.current
        ] for data in batch_data.data])
        
        # Make predictions
        predictions = await predictive_maintenance_runner.predict.async_run(features)
        probabilities = await predictive_maintenance_runner.predict_proba.async_run(features)
        
        # Format results
        results = []
        for i, (pred, proba) in enumerate(zip(predictions, probabilities)):
            predicted_class = "failure" if pred == 1 else "normal"
            confidence = float(np.max(proba))
            
            results.append({
                "index": i,
                "prediction": predicted_class,
                "confidence": confidence,
                "probability_normal": float(proba[0]),
                "probability_failure": float(proba[1])
            })
        
        # Calculate statistics
        failure_count = sum(1 for r in results if r["prediction"] == "failure")
        normal_count = len(results) - failure_count
        
        logger.info(f"Batch prediction: {len(results)} samples ({failure_count} failures, {normal_count} normal)")
        
        return {
            "predictions": results,
            "summary": {
                "total_samples": len(results),
                "failures_detected": failure_count,
                "normal_operations": normal_count,
                "failure_rate": failure_count / len(results) if len(results) > 0 else 0
            }
        }
    
    except Exception as e:
        logger.error(f"Batch prediction error: {str(e)}")
        return {
            "error": str(e),
            "predictions": []
        }

@svc.api(input=JSON(), output=JSON())
async def health() -> dict:
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "predictive_maintenance",
        "model_version": "2.0.0",
        "framework": "BentoML"
    }

@svc.api(input=JSON(), output=JSON())
async def model_info() -> dict:
    """Get model information"""
    model = bentoml.sklearn.get("predictive_maintenance_model:latest")
    
    return {
        "tag": str(model.tag),
        "framework": "sklearn",
        "metadata": model.info.metadata,
        "labels": model.info.labels,
        "creation_time": str(model.info.creation_time)
    }
