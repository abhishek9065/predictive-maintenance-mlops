"""
FastAPI-based ML Model Serving API
Provides endpoints for predictive maintenance predictions
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

from fastapi import FastAPI, HTTPException, status, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
import joblib
import numpy as np
import pandas as pd
from prometheus_client import Counter, Histogram, generate_latest
from prometheus_client import CONTENT_TYPE_LATEST
from starlette.responses import Response

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Predictive Maintenance API",
    description="ML-powered API for equipment failure prediction",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics (use try-except to avoid duplication)
try:
    from prometheus_client import REGISTRY
    # Clear existing metrics to avoid duplication
    collectors = list(REGISTRY._collector_to_names.keys())
    for collector in collectors:
        try:
            REGISTRY.unregister(collector)
        except Exception:
            pass
except Exception:
    pass

prediction_counter = Counter('predictions_total', 'Total number of predictions made')
prediction_latency = Histogram('prediction_latency_seconds', 'Prediction latency in seconds')
error_counter = Counter('prediction_errors_total', 'Total number of prediction errors')

# Pydantic models for request/response
class SensorData(BaseModel):
    """Single sensor reading"""
    temperature: float = Field(..., ge=-50, le=200, description="Temperature in Celsius")
    vibration: float = Field(..., ge=0, le=100, description="Vibration level")
    pressure: float = Field(..., ge=0, le=1000, description="Pressure in PSI")
    current: float = Field(..., ge=0, le=10000, description="Electrical current in Amps")
    rpm: float = Field(..., ge=0, le=10000, description="Rotations per minute")
    
    @validator('*', pre=True)
    def check_not_nan(cls, v):
        if isinstance(v, float) and (np.isnan(v) or np.isinf(v)):
            raise ValueError('Invalid numeric value')
        return v

class PredictionRequest(BaseModel):
    """Batch prediction request"""
    data: List[SensorData] = Field(..., min_items=1, max_items=1000)
    return_probability: bool = Field(default=True, description="Return prediction probabilities")

class PredictionResponse(BaseModel):
    """Prediction response"""
    predictions: List[int]
    probabilities: Optional[List[List[float]]] = None
    timestamp: str
    model_version: str
    count: int

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    model_loaded: bool
    model_version: Optional[str]
    timestamp: str

class MetricsResponse(BaseModel):
    """Model metrics response"""
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    model_type: str
    training_date: str

# Global model storage
class ModelStore:
    def __init__(self):
        self.model = None
        self.scaler = None
        self.metadata = None
        self.model_path = Path(os.getenv("MODEL_PATH", "models/production"))
    
    def load_model(self):
        """Load model from disk"""
        try:
            # Try different model file locations (prioritize best model)
            model_files = [
                Path("models/best_model.pkl"),
                Path("models/production_model.pkl"),
                Path("models/staging_model.pkl"),
                Path("models/quick_model.pkl"),
                self.model_path / "model.pkl",
                Path("models/production/model.pkl"),
                Path("models/staging/model.pkl"),
            ]
            
            model_file = None
            for mf in model_files:
                if mf.exists():
                    model_file = mf
                    break
            
            if model_file is None:
                logger.error("No model file found in any location")
                return False
            
            self.model = joblib.load(model_file)
            logger.info(f"Model loaded from {model_file}")
            
            # Load scaler if exists (try multiple locations)
            scaler_files = [
                model_file.parent / "scaler.pkl",
                Path("models/scaler.pkl"),
            ]
            for scaler_file in scaler_files:
                if scaler_file.exists():
                    self.scaler = joblib.load(scaler_file)
                    logger.info(f"Scaler loaded from {scaler_file}")
                    break
            
            # Load metadata (try multiple locations)
            metadata_files = [
                Path("models/best_model_metrics.json"),
                Path("models/model_info.json"),
                Path("models/production_metadata.json"),
                Path("models/staging_metadata.json"),
                Path("models/deployment_metadata.json"),
                self.model_path / "metadata.json",
            ]
            for metadata_file in metadata_files:
                if metadata_file.exists():
                    with open(metadata_file, 'r') as f:
                        self.metadata = json.load(f)
                    logger.info(f"Metadata loaded from {metadata_file}: {self.metadata.get('model_type', 'Unknown')}")
                    break
            
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

@app.on_event("startup")
async def startup_event():
    """Load model on startup"""
    logger.info("Starting FastAPI application...")
    success = model_store.load_model()
    if success:
        logger.info("Model loaded successfully")
    else:
        logger.warning("Failed to load model - predictions will fail")

@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint"""
    return {
        "message": "Predictive Maintenance API",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy" if model_store.model is not None else "degraded",
        model_loaded=model_store.model is not None,
        model_version=model_store.metadata.get('version', 'unknown') if model_store.metadata else None,
        timestamp=datetime.now().isoformat()
    )

@app.post("/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest):
    """Make predictions on sensor data"""
    try:
        # Start timing
        start_time = datetime.now()
        
        # Check if model is loaded
        if model_store.model is None:
            error_counter.inc()
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Model not loaded"
            )
        
        # Convert request to DataFrame
        data_dicts = [sensor.dict() for sensor in request.data]
        df = pd.DataFrame(data_dicts)
        
        # Make predictions
        predictions, probabilities = model_store.predict(df.values)
        
        # Update metrics
        prediction_counter.inc(len(predictions))
        prediction_latency.observe((datetime.now() - start_time).total_seconds())
        
        # Prepare response
        response = PredictionResponse(
            predictions=predictions,
            probabilities=probabilities if request.return_probability else None,
            timestamp=datetime.now().isoformat(),
            model_version=model_store.metadata.get('version', 'unknown') if model_store.metadata else 'unknown',
            count=len(predictions)
        )
        
        logger.info(f"Predictions made: {len(predictions)}")
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        error_counter.inc()
        logger.error(f"Prediction error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {str(e)}"
        )

@app.post("/predict/single")
async def predict_single(sensor_data: SensorData):
    """Make a single prediction (simplified endpoint)"""
    try:
        # Check if model is loaded
        if model_store.model is None:
            error_counter.inc()
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Model not loaded"
            )
        
        # Convert to array for prediction
        data_array = np.array([[
            sensor_data.temperature,
            sensor_data.vibration,
            sensor_data.pressure,
            sensor_data.rpm,
            sensor_data.current
        ]])
        
        # Make prediction
        predictions, probabilities = model_store.predict(data_array)
        
        # Update metrics
        prediction_counter.inc()
        
        # Return simple response
        return {
            "prediction": "FAILURE" if predictions[0] == 1 else "NORMAL",
            "failure_probability": float(probabilities[0][1]) if len(probabilities[0]) > 1 else float(predictions[0]),
            "confidence": float(max(probabilities[0])) if len(probabilities[0]) > 1 else 1.0,
            "timestamp": datetime.now().isoformat(),
            "sensor_data": sensor_data.dict()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        error_counter.inc()
        logger.error(f"Prediction error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {str(e)}"
        )

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/model/info", response_model=Dict)
async def model_info():
    """Get model information"""
    if model_store.metadata is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model metadata not available"
        )
    
    return {
        "model_type": model_store.metadata.get('model_type', 'unknown'),
        "version": model_store.metadata.get('version', 'unknown'),
        "training_date": model_store.metadata.get('training_date', 'unknown'),
        "metrics": model_store.metadata.get('metrics', {}),
        "features": model_store.metadata.get('features', [])
    }

@app.get("/model/metrics", response_model=MetricsResponse)
async def model_metrics():
    """Get model performance metrics"""
    if model_store.metadata is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model metadata not available"
        )
    
    metrics = model_store.metadata.get('metrics', {})
    
    return MetricsResponse(
        accuracy=metrics.get('accuracy', 0.0),
        precision=metrics.get('precision', 0.0),
        recall=metrics.get('recall', 0.0),
        f1_score=metrics.get('f1_score', 0.0),
        model_type=model_store.metadata.get('model_type', 'unknown'),
        training_date=model_store.metadata.get('training_date', 'unknown')
    )

@app.post("/model/reload")
async def reload_model():
    """Reload model from disk"""
    try:
        success = model_store.load_model()
        if success:
            return {"status": "success", "message": "Model reloaded successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to reload model"
            )
    except Exception as e:
        logger.error(f"Error reloading model: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Reload failed: {str(e)}"
        )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api_fastapi:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
