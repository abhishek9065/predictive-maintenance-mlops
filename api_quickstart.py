"""
FastAPI Application for Predictive Maintenance - Quick Start Version
This version loads a trained model on the fly for immediate testing
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
import numpy as np
from datetime import datetime
import joblib
from pathlib import Path
import json

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

# Global model - will be loaded on first prediction
_model = None
_model_info = {}


def get_model():
    """Load or train a model if not already loaded"""
    global _model, _model_info
    
    if _model is None:
        # Try to load existing model
        models_dir = Path("models")
        model_files = list(models_dir.glob("*.pkl")) if models_dir.exists() else []
        
        if model_files:
            # Load the first available model
            model_path = model_files[0]
            _model = joblib.load(model_path)
            _model_info = {
                "model_type": "Loaded from file",
                "model_path": str(model_path),
                "loaded_at": datetime.now().isoformat()
            }
        else:
            # Train a quick model from available data
            from sklearn.ensemble import RandomForestClassifier
            
            data_dir = Path("data/raw")
            data_files = list(data_dir.glob("historical_*.json"))
            
            if data_files:
                # Load data
                with open(data_files[0], 'r') as f:
                    data = json.load(f)
                
                # Extract features
                features = []
                labels = []
                
                for record in data:
                    sensors = record['sensors']
                    features.append([
                        sensors['temperature']['value'],
                        sensors['vibration']['value'],
                        sensors['pressure']['value'],
                        sensors['current']['value'],
                        sensors['rpm']['value']
                    ])
                    labels.append(record['is_failing'])
                
                X = np.array(features)
                y = np.array(labels)
                
                # Train model
                _model = RandomForestClassifier(
                    n_estimators=100,
                    max_depth=10,
                    random_state=42,
                    n_jobs=-1
                )
                _model.fit(X, y)
                
                # Save model
                models_dir.mkdir(exist_ok=True)
                model_path = models_dir / "quick_model.pkl"
                joblib.dump(_model, model_path)
                
                _model_info = {
                    "model_type": "RandomForestClassifier",
                    "n_estimators": 100,
                    "training_samples": len(X),
                    "trained_at": datetime.now().isoformat(),
                    "model_path": str(model_path)
                }
            else:
                raise HTTPException(
                    status_code=503,
                    detail="No data available. Please run: python src/data_collection/iot_simulator.py"
                )
    
    return _model


# Pydantic models for request/response
class SensorData(BaseModel):
    """Schema for sensor data input."""
    temperature: float = Field(..., ge=0, le=150, description="Temperature in celsius")
    vibration: float = Field(..., ge=0, le=20, description="Vibration in mm/s")
    pressure: float = Field(..., ge=0, le=200, description="Pressure in psi")
    current: float = Field(..., ge=0, le=100, description="Current in amperes")
    rpm: float = Field(..., ge=0, le=3000, description="RPM")

    class Config:
        json_schema_extra = {
            "example": {
                "temperature": 75.5,
                "vibration": 8.2,
                "pressure": 95.3,
                "current": 22.1,
                "rpm": 1450.0
            }
        }


class PredictionResponse(BaseModel):
    """Schema for prediction response."""
    prediction: str
    probability: float
    risk_level: str
    confidence: float
    timestamp: str
    sensor_readings: Dict[str, float]


class BatchSensorData(BaseModel):
    """Schema for batch prediction request."""
    data: List[SensorData]


class BatchPredictionResponse(BaseModel):
    """Schema for batch prediction response."""
    predictions: List[PredictionResponse]
    total_predictions: int


class HealthResponse(BaseModel):
    """Schema for health check response."""
    status: str
    timestamp: str
    model_loaded: bool
    model_info: Dict


# API Endpoints
@app.get("/", tags=["General"])
async def root():
    """Root endpoint - API information"""
    return {
        "message": "Predictive Maintenance API",
        "version": "1.0.0",
        "status": "active",
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "predict": "/predict",
            "predict_batch": "/predict/batch"
        }
    }


@app.get("/health", response_model=HealthResponse, tags=["General"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "model_loaded": _model is not None,
        "model_info": _model_info if _model_info else {}
    }


@app.post("/predict", response_model=PredictionResponse, tags=["Predictions"])
async def predict(sensor_data: SensorData):
    """
    Make a prediction for equipment failure based on sensor readings.
    
    Returns:
    - prediction: "NORMAL" or "FAILURE"
    - probability: Probability of failure (0-1)
    - risk_level: "LOW", "MEDIUM", or "HIGH"
    - confidence: Prediction confidence (0-1)
    """
    try:
        # Get model
        model = get_model()
        
        # Prepare features
        features = np.array([[
            sensor_data.temperature,
            sensor_data.vibration,
            sensor_data.pressure,
            sensor_data.current,
            sensor_data.rpm
        ]])
        
        # Make prediction
        prediction = model.predict(features)[0]
        probabilities = model.predict_proba(features)[0]
        
        # Get failure probability
        failure_prob = probabilities[1]
        
        # Determine risk level
        if failure_prob < 0.3:
            risk_level = "LOW"
        elif failure_prob < 0.7:
            risk_level = "MEDIUM"
        else:
            risk_level = "HIGH"
        
        # Prepare response
        return {
            "prediction": "FAILURE" if prediction == 1 else "NORMAL",
            "probability": float(failure_prob),
            "risk_level": risk_level,
            "confidence": float(max(probabilities)),
            "timestamp": datetime.now().isoformat(),
            "sensor_readings": {
                "temperature": sensor_data.temperature,
                "vibration": sensor_data.vibration,
                "pressure": sensor_data.pressure,
                "current": sensor_data.current,
                "rpm": sensor_data.rpm
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/predict/batch", response_model=BatchPredictionResponse, tags=["Predictions"])
async def predict_batch(batch_data: BatchSensorData):
    """
    Make predictions for multiple equipment sensor readings.
    
    Useful for processing historical data or multiple equipment simultaneously.
    """
    try:
        model = get_model()
        predictions = []
        
        for sensor_data in batch_data.data:
            # Prepare features
            features = np.array([[
                sensor_data.temperature,
                sensor_data.vibration,
                sensor_data.pressure,
                sensor_data.current,
                sensor_data.rpm
            ]])
            
            # Make prediction
            prediction = model.predict(features)[0]
            probabilities = model.predict_proba(features)[0]
            failure_prob = probabilities[1]
            
            # Determine risk level
            if failure_prob < 0.3:
                risk_level = "LOW"
            elif failure_prob < 0.7:
                risk_level = "MEDIUM"
            else:
                risk_level = "HIGH"
            
            predictions.append({
                "prediction": "FAILURE" if prediction == 1 else "NORMAL",
                "probability": float(failure_prob),
                "risk_level": risk_level,
                "confidence": float(max(probabilities)),
                "timestamp": datetime.now().isoformat(),
                "sensor_readings": {
                    "temperature": sensor_data.temperature,
                    "vibration": sensor_data.vibration,
                    "pressure": sensor_data.pressure,
                    "current": sensor_data.current,
                    "rpm": sensor_data.rpm
                }
            })
        
        return {
            "predictions": predictions,
            "total_predictions": len(predictions)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/model/info", tags=["Model"])
async def model_info():
    """Get information about the loaded model"""
    if _model is None:
        return {
            "status": "not_loaded",
            "message": "Model will be loaded on first prediction"
        }
    
    return {
        "status": "loaded",
        "info": _model_info,
        "feature_names": ["temperature", "vibration", "pressure", "current", "rpm"]
    }


# For running with: python api_quickstart.py
if __name__ == "__main__":
    import uvicorn
    print("Starting Predictive Maintenance API...")
    print("Visit http://localhost:8000/docs for interactive documentation")
    uvicorn.run(app, host="0.0.0.0", port=8000)
