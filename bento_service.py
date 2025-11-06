"""
BentoML Service for Predictive Maintenance
Production-ready ML model serving with BentoML 1.4
"""

import bentoml
import numpy as np
from typing import Dict, List

# Load the model runner
model_runner = bentoml.sklearn.get("predictive_maintenance_model:latest").to_runner()

# Create the service
svc = bentoml.Service("predictive_maintenance")

@svc.api(
    input=bentoml.io.JSON(),
    output=bentoml.io.JSON()
)
async def predict(sensor_data: Dict) -> Dict:
    """
    Single prediction endpoint
    
    Input format:
    {
        "temperature": 72.0,
        "vibration": 0.35,
        "pressure": 95.0,
        "rpm": 1450.0,
        "current": 8.5
    }
    """
    try:
        # Extract features
        features = np.array([[
            sensor_data["temperature"],
            sensor_data["vibration"],
            sensor_data["pressure"],
            sensor_data["rpm"],
            sensor_data["current"]
        ]])
        
        # Make prediction
        prediction = await model_runner.predict.async_run(features)
        proba = await model_runner.predict_proba.async_run(features)
        
        # Get confidence
        confidence = float(np.max(proba[0]))
        predicted_class = "failure" if prediction[0] == 1 else "normal"
        
        return {
            "prediction": predicted_class,
            "confidence": confidence,
            "probability_normal": float(proba[0][0]),
            "probability_failure": float(proba[0][1]),
            "input_data": sensor_data
        }
    
    except Exception as e:
        return {
            "error": str(e),
            "prediction": "error",
            "confidence": 0.0
        }

@svc.api(
    input=bentoml.io.JSON(),
    output=bentoml.io.JSON()
)
async def predict_batch(batch_data: Dict) -> Dict:
    """
    Batch prediction endpoint
    
    Input format:
    {
        "data": [
            {"temperature": 72.0, "vibration": 0.35, "pressure": 95.0, "rpm": 1450.0, "current": 8.5},
            {"temperature": 105.0, "vibration": 2.5, "pressure": 88.0, "rpm": 1550.0, "current": 15.0}
        ]
    }
    """
    try:
        data_list = batch_data.get("data", [])
        
        # Prepare features matrix
        features = np.array([[
            item["temperature"],
            item["vibration"],
            item["pressure"],
            item["rpm"],
            item["current"]
        ] for item in data_list])
        
        # Make predictions
        predictions = await model_runner.predict.async_run(features)
        probabilities = await model_runner.predict_proba.async_run(features)
        
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
        return {
            "error": str(e),
            "predictions": []
        }

@svc.api(
    input=bentoml.io.JSON(),
    output=bentoml.io.JSON()
)
def health() -> Dict:
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "predictive_maintenance",
        "model_version": "2.0.0",
        "framework": "BentoML"
    }

@svc.api(
    input=bentoml.io.JSON(),
    output=bentoml.io.JSON()
)
def model_info() -> Dict:
    """Get model information"""
    try:
        model = bentoml.sklearn.get("predictive_maintenance_model:latest")
        
        return {
            "tag": str(model.tag),
            "framework": "sklearn",
            "metadata": model.info.metadata if hasattr(model.info, 'metadata') else {},
            "labels": model.info.labels if hasattr(model.info, 'labels') else{},
            "creation_time": str(model.info.creation_time) if hasattr(model.info, 'creation_time') else ""
        }
    except Exception as e:
        return {
            "error": str(e)
        }
