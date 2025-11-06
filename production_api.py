"""
Production API Server with Health Checks and Monitoring
Optimized for real-world deployment
"""

import os
import pickle
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, List

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import numpy as np
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="Predictive Maintenance API - Production",
    description="Production-ready ML API for equipment failure prediction",
    version="2.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response Models
class SensorData(BaseModel):
    """Single sensor reading"""
    temperature: float = Field(..., description="Temperature in Celsius")
    vibration: float = Field(..., description="Vibration level")
    pressure: float = Field(..., description="Pressure in PSI")
    rpm: float = Field(..., description="RPM")
    current: float = Field(..., description="Current in Amps")

class PredictionResponse(BaseModel):
    """Prediction response"""
    prediction: str
    probability: float
    timestamp: str
    model_version: str

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    model_loaded: bool
    uptime_seconds: float
    total_predictions: int

# Global state
class AppState:
    def __init__(self):
        self.model = None
        self.model_loaded = False
        self.start_time = time.time()
        self.prediction_count = 0
        self.model_path = Path("models/production_model.pkl")
        
state = AppState()

def load_production_model():
    """Load the production model"""
    try:
        # Try multiple model locations
        model_paths = [
            Path("models/production_model.pkl"),
            Path("models/best_model.pkl"),
            Path("models/quick_model.pkl")
        ]
        
        for model_path in model_paths:
            if model_path.exists():
                logger.info(f"Loading model from {model_path}")
                with open(model_path, 'rb') as f:
                    state.model = pickle.load(f)
                state.model_loaded = True
                state.model_path = model_path
                logger.info(f"✅ Model loaded successfully from {model_path}")
                return True
        
        logger.error("❌ No model file found")
        return False
        
    except Exception as e:
        logger.error(f"❌ Error loading model: {e}")
        return False

@app.on_event("startup")
async def startup_event():
    """Load model on startup"""
    logger.info("🚀 Starting Production API Server...")
    load_production_model()
    logger.info("✅ API Server Ready!")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Predictive Maintenance API - Production",
        "version": "2.0.0",
        "status": "operational",
        "endpoints": {
            "health": "/health",
            "predict": "/predict",
            "docs": "/docs"
        }
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    uptime = time.time() - state.start_time
    return HealthResponse(
        status="healthy" if state.model_loaded else "unhealthy",
        model_loaded=state.model_loaded,
        uptime_seconds=uptime,
        total_predictions=state.prediction_count
    )

@app.post("/predict", response_model=PredictionResponse)
async def predict(data: SensorData, background_tasks: BackgroundTasks):
    """Make a prediction"""
    
    if not state.model_loaded:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
        # Prepare features
        features = np.array([[
            data.temperature,
            data.vibration,
            data.pressure,
            data.rpm,
            data.current
        ]])
        
        # Make prediction
        start_time = time.time()
        prediction = state.model.predict(features)[0]
        
        # Get probability if available
        try:
            proba = state.model.predict_proba(features)[0]
            probability = float(proba[prediction])
        except:
            probability = 1.0 if prediction == 1 else 0.0
        
        inference_time = (time.time() - start_time) * 1000
        
        # Update counter
        state.prediction_count += 1
        
        # Log prediction
        logger.info(f"Prediction: {prediction} | Probability: {probability:.4f} | Time: {inference_time:.2f}ms")
        
        return PredictionResponse(
            prediction="FAILURE" if prediction == 1 else "NORMAL",
            probability=probability,
            timestamp=datetime.now().isoformat(),
            model_version=str(state.model_path.name)
        )
        
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/predict/batch")
async def predict_batch(data: List[SensorData]):
    """Batch prediction endpoint"""
    
    if not state.model_loaded:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
        # Prepare features
        features = np.array([[
            d.temperature, d.vibration, d.pressure, d.rpm, d.current
        ] for d in data])
        
        # Make predictions
        predictions = state.model.predict(features)
        
        # Get probabilities
        try:
            probas = state.model.predict_proba(features)
            probabilities = [float(probas[i][pred]) for i, pred in enumerate(predictions)]
        except:
            probabilities = [1.0 if p == 1 else 0.0 for p in predictions]
        
        state.prediction_count += len(data)
        
        return {
            "predictions": ["FAILURE" if p == 1 else "NORMAL" for p in predictions],
            "probabilities": probabilities,
            "count": len(data),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Batch prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/model/info")
async def model_info():
    """Get model information"""
    if not state.model_loaded:
        return {"status": "not_loaded"}
    
    return {
        "status": "loaded",
        "model_type": type(state.model).__name__,
        "model_path": str(state.model_path),
        "predictions_made": state.prediction_count,
        "uptime_hours": (time.time() - state.start_time) / 3600
    }

if __name__ == "__main__":
    print("="*80)
    print("  🚀 STARTING PRODUCTION API SERVER")
    print("="*80)
    print("\n📍 Server: http://0.0.0.0:8000")
    print("📖 API Docs: http://localhost:8000/docs")
    print("🏥 Health: http://localhost:8000/health")
    print("\n" + "="*80 + "\n")
    
    uvicorn.run(
        "production_api:app",
        host="0.0.0.0",
        port=8001,
        reload=False,
        log_level="info"
    )
