"""
BentoML Service for Predictive Maintenance (BentoML 1.4+)
Production-ready ML model serving
"""

from __future__ import annotations
import bentoml
import numpy as np
from typing import Dict

# Load the model
model_ref = bentoml.models.get("predictive_maintenance_model:latest")

@bentoml.service(
    resources={"cpu": "2"},
    traffic={"timeout": 10},
)
class PredictiveMaintenanceService:
    """Predictive Maintenance Service"""
    
    def __init__(self):
        """Initialize the service"""
        # Load the model
        self.model = bentoml.sklearn.load_model(model_ref)
    
    @bentoml.api
    def predict(self, sensor_data: Dict) -> Dict:
        """
        Single prediction endpoint
        
        Input:
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
            prediction = self.model.predict(features)
            proba = self.model.predict_proba(features)
            
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
    
    @bentoml.api
    def predict_batch(self, batch_data: Dict) -> Dict:
        """
        Batch prediction endpoint
        
        Input:
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
            predictions = self.model.predict(features)
            probabilities = self.model.predict_proba(features)
            
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
    
    @bentoml.api
    def health(self) -> Dict:
        """Health check endpoint"""
        return {
            "status": "healthy",
            "service": "predictive_maintenance",
            "model_version": "2.0.0",
            "framework": "BentoML",
            "model_tag": str(model_ref.tag)
        }
    
    @bentoml.api
    def model_info(self) -> Dict:
        """Get model information"""
        try:
            return {
                "tag": str(model_ref.tag),
                "framework": "sklearn",
                "metadata": model_ref.info.metadata if hasattr(model_ref.info, 'metadata') else {},
                "labels": model_ref.info.labels if hasattr(model_ref.info, 'labels') else {},
                "creation_time": str(model_ref.info.creation_time) if hasattr(model_ref.info, 'creation_time') else ""
            }
        except Exception as e:
            return {
                "error": str(e)
            }
