"""
FastAPI Application for Model Serving
Provides REST API endpoints for predictive maintenance predictions.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
import pandas as pd
import numpy as np
from datetime import datetime
import logging
import uvicorn

from .model_loader import ModelLoader
from ..utils.logger import setup_logger

# Setup logging
logger = setup_logger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Predictive Maintenance API",
    description="REST API for equipment failure prediction",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global model loader
model_loader = ModelLoader()


# Pydantic models for request/response
class SensorData(BaseModel):
    """Schema for sensor data input."""
    temperature: float = Field(..., description="Temperature in celsius")
    vibration: float = Field(..., description="Vibration in mm/s")
    pressure: float = Field(..., description="Pressure in psi")
    current: float = Field(..., description="Current in amperes")
    rpm: float = Field(..., description="RPM")
    operating_hours: Optional[float] = Field(0, description="Operating hours")
    time_since_maintenance: Optional[float] = Field(0, description="Hours since maintenance")


class PredictionRequest(BaseModel):
    """Schema for prediction request."""
    equipment_id: str = Field(..., description="Equipment identifier")
    timestamp: Optional[str] = Field(None, description="Timestamp of reading")
    sensor_data: SensorData
    model_name: Optional[str] = Field("random_forest", description="Model to use for prediction")


class PredictionResponse(BaseModel):
    """Schema for prediction response."""
    equipment_id: str
    timestamp: str
    prediction: int
    failure_probability: float
    risk_level: str
    model_name: str
    processing_time_ms: float


class HealthResponse(BaseModel):
    """Schema for health check response."""
    status: str
    timestamp: str
    models_loaded: List[str]
    version: str


@app.on_event("startup")
async def startup_event():
    """Initialize models on startup."""
    logger.info("Starting Predictive Maintenance API...")
    try:
        # Load default models
        model_loader.load_model("random_forest", "models/random_forest_model.pkl")
        logger.info("Models loaded successfully")
    except Exception as e:
        logger.warning(f"Could not load models on startup: {e}")


@app.get("/", response_model=Dict)
async def root():
    """Root endpoint."""
    return {
        "message": "Predictive Maintenance API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        models_loaded=model_loader.list_models(),
        version="1.0.0"
    )


@app.post("/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest):
    """
    Predict equipment failure.
    
    Args:
        request: Prediction request with sensor data
        
    Returns:
        Prediction response with failure probability
    """
    start_time = datetime.now()
    
    try:
        # Prepare input data
        input_data = pd.DataFrame([{
            'temperature': request.sensor_data.temperature,
            'vibration': request.sensor_data.vibration,
            'pressure': request.sensor_data.pressure,
            'current': request.sensor_data.current,
            'rpm': request.sensor_data.rpm,
            'operating_hours': request.sensor_data.operating_hours,
            'time_since_maintenance': request.sensor_data.time_since_maintenance
        }])
        
        # Get model
        model = model_loader.get_model(request.model_name)
        if model is None:
            raise HTTPException(
                status_code=404,
                detail=f"Model '{request.model_name}' not found"
            )
        
        # Make prediction
        prediction = model.predict(input_data)[0]
        probability = model.predict_proba(input_data)[0, 1]
        
        # Determine risk level
        if probability >= 0.8:
            risk_level = "critical"
        elif probability >= 0.5:
            risk_level = "high"
        elif probability >= 0.3:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Prepare response
        response = PredictionResponse(
            equipment_id=request.equipment_id,
            timestamp=request.timestamp or datetime.now().isoformat(),
            prediction=int(prediction),
            failure_probability=float(probability),
            risk_level=risk_level,
            model_name=request.model_name,
            processing_time_ms=round(processing_time, 2)
        )
        
        logger.info(f"Prediction for {request.equipment_id}: "
                   f"probability={probability:.3f}, risk={risk_level}")
        
        return response
    
    except Exception as e:
        logger.error(f"Prediction error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/predict/batch")
async def predict_batch(requests: List[PredictionRequest]):
    """
    Batch prediction endpoint.
    
    Args:
        requests: List of prediction requests
        
    Returns:
        List of predictions
    """
    try:
        predictions = []
        for request in requests:
            prediction = await predict(request)
            predictions.append(prediction)
        
        logger.info(f"Batch prediction completed: {len(predictions)} predictions")
        return predictions
    
    except Exception as e:
        logger.error(f"Batch prediction error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/models/load")
async def load_model(model_name: str, model_path: str):
    """
    Load a model into memory.
    
    Args:
        model_name: Name to assign to the model
        model_path: Path to the model file
        
    Returns:
        Success message
    """
    try:
        model_loader.load_model(model_name, model_path)
        logger.info(f"Model '{model_name}' loaded from {model_path}")
        return {"message": f"Model '{model_name}' loaded successfully"}
    
    except Exception as e:
        logger.error(f"Failed to load model: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/models")
async def list_models():
    """
    List all loaded models.
    
    Returns:
        List of model names
    """
    models = model_loader.list_models()
    return {"models": models, "count": len(models)}


@app.delete("/models/{model_name}")
async def unload_model(model_name: str):
    """
    Unload a model from memory.
    
    Args:
        model_name: Name of the model to unload
        
    Returns:
        Success message
    """
    try:
        model_loader.unload_model(model_name)
        logger.info(f"Model '{model_name}' unloaded")
        return {"message": f"Model '{model_name}' unloaded successfully"}
    
    except Exception as e:
        logger.error(f"Failed to unload model: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))


def main():
    """Run the FastAPI application."""
    uvicorn.run(
        "src.deployment.api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )


if __name__ == "__main__":
    main()
