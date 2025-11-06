"""
BentoML Service for Predictive Maintenance
Production-ready model serving with BentoML
"""

import json
import logging
from pathlib import Path
from typing import List

import bentoml
from bentoml.io import JSON, NumpyNdarray
import numpy as np
import pandas as pd
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define input schema
class SensorData(BaseModel):
    temperature: float = Field(..., ge=-50, le=200)
    vibration: float = Field(..., ge=0, le=100)
    pressure: float = Field(..., ge=0, le=1000)
    rpm: float = Field(..., ge=0, le=10000)
    power_consumption: float = Field(..., ge=0, le=10000)

class PredictionInput(BaseModel):
    data: List[SensorData]
    return_probability: bool = True

# Load the model (BentoML will handle model loading)
# This is a placeholder - actual model will be loaded from BentoML store
model_ref = bentoml.sklearn.get("predictive_maintenance_model:latest")

# Create the service
svc = bentoml.Service("predictive_maintenance", runners=[model_ref.to_runner()])

@svc.api(input=JSON(pydantic_model=PredictionInput), output=JSON())
async def predict(input_data: PredictionInput) -> dict:
    """
    Make predictions on sensor data
    
    Args:
        input_data: List of sensor readings
    
    Returns:
        Predictions with optional probabilities
    """
    try:
        # Convert input to DataFrame
        data_dicts = [sensor.dict() for sensor in input_data.data]
        df = pd.DataFrame(data_dicts)
        
        # Make predictions
        predictions = await model_ref.async_run(df.values)
        
        # Get probabilities if available
        probabilities = None
        if input_data.return_probability:
            try:
                probabilities = await model_ref.async_run_batch([df.values], method="predict_proba")
                probabilities = probabilities[0].tolist()
            except Exception as e:
                logger.warning(f"Could not get probabilities: {e}")
        
        # Prepare response
        response = {
            "predictions": predictions.tolist() if hasattr(predictions, 'tolist') else predictions,
            "count": len(predictions),
            "model_version": str(model_ref.tag)
        }
        
        if probabilities is not None:
            response["probabilities"] = probabilities
        
        return response
    
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        return {"error": str(e), "success": False}

@svc.api(input=JSON(), output=JSON())
async def health() -> dict:
    """Health check endpoint"""
    return {
        "status": "healthy",
        "model_version": str(model_ref.tag),
        "service": "predictive_maintenance"
    }

@svc.api(input=JSON(), output=JSON())
async def model_info() -> dict:
    """Get model information"""
    try:
        # Get metadata from BentoML model
        metadata = model_ref.custom_objects.get("metadata", {})
        
        return {
            "model_type": metadata.get("model_type", "unknown"),
            "version": str(model_ref.tag),
            "training_date": metadata.get("training_date", "unknown"),
            "metrics": metadata.get("metrics", {}),
            "features": metadata.get("features", [])
        }
    except Exception as e:
        logger.error(f"Error getting model info: {e}")
        return {"error": str(e)}
