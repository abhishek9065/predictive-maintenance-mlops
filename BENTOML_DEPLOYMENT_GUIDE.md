# 🚀 BentoML Production Deployment Guide

**Predictive Maintenance System - BentoML Serving**

---

## ✅ What Has Been Done

### 1. Model Saved to BentoML
✅ Production model successfully saved to BentoML model store
- **Model Tag**: `predictive_maintenance_model:i4c3aqn3cwbxtrbd`
- **Accuracy**: 95.46%
- **Precision**: 97.70%
- **Recall**: 92.09%
- **F1 Score**: 94.81%

### 2. BentoML Service Created
✅ Created `service.py` with 4 API endpoints:
- `/predict` - Single prediction
- `/predict_batch` - Batch predictions
- `/health` - Health check
- `/model_info` - Model information

### 3. Configuration Files
✅ Created `bentofile.yaml` for Bento packaging
✅ Created test suite `test_bentoml_service.py`

---

## 🎯 Deployment Options

### Option 1: Direct Serving (Development)

**Start the service:**
```bash
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Serve with BentoML
bentoml serve service:PredictiveMaintenanceService --port 3000
```

**Test the service:**
```bash
# Health check
curl http://localhost:3000/health

# Single prediction
curl -X POST http://localhost:3000/predict \
  -H "Content-Type: application/json" \
  -d '{"temperature": 72, "vibration": 0.35, "pressure": 95, "rpm": 1450, "current": 8.5}'

# Run test suite
python test_bentoml_service.py
```

### Option 2: Build and Containerize (Production)

**Build Bento:**
```bash
# Build the Bento
bentoml build

# List built Bentos
bentoml list

# Get the latest Bento tag
# Example: predictive_maintenance:abc123
```

**Containerize with Docker:**
```bash
# Build Docker image from Bento
bentoml containerize predictive_maintenance:latest -t predictive-maintenance:latest

# Run container
docker run -p 3000:3000 predictive-maintenance:latest

# Or run in detached mode
docker run -d -p 3000:3000 --name pm-api predictive-maintenance:latest
```

### Option 3: Production Deployment

**Deploy to Cloud:**

```bash
# Deploy to AWS Lambda
bentoml deploy predictive_maintenance:latest --platform aws-lambda

# Deploy to AWS SageMaker
bentoml deploy predictive_maintenance:latest --platform aws-sagemaker

# Deploy to Google Cloud Run
bentoml deploy predictive_maintenance:latest --platform google-cloud-run

# Deploy to Azure Container Instances
bentoml deploy predictive_maintenance:latest --platform azure-container-instances
```

---

## 📋 API Endpoints

### 1. Health Check
```bash
GET /health

Response:
{
  "status": "healthy",
  "service": "predictive_maintenance",
  "model_version": "2.0.0",
  "framework": "BentoML",
  "model_tag": "predictive_maintenance_model:i4c3aqn3cwbxtrbd"
}
```

### 2. Model Information
```bash
GET /model_info

Response:
{
  "tag": "predictive_maintenance_model:i4c3aqn3cwbxtrbd",
  "framework": "sklearn",
  "metadata": {
    "accuracy": 0.9546,
    "precision": 0.9770,
    "recall": 0.9209,
    "f1_score": 0.9481,
    ...
  }
}
```

### 3. Single Prediction
```bash
POST /predict
Content-Type: application/json

Request:
{
  "temperature": 72.0,
  "vibration": 0.35,
  "pressure": 95.0,
  "rpm": 1450.0,
  "current": 8.5
}

Response:
{
  "prediction": "normal",
  "confidence": 0.8040,
  "probability_normal": 0.8040,
  "probability_failure": 0.1960,
  "input_data": { ... }
}
```

### 4. Batch Prediction
```bash
POST /predict_batch
Content-Type: application/json

Request:
{
  "data": [
    {"temperature": 72, "vibration": 0.35, "pressure": 95, "rpm": 1450, "current": 8.5},
    {"temperature": 105, "vibration": 2.5, "pressure": 88, "rpm": 1550, "current": 15}
  ]
}

Response:
{
  "predictions": [
    {"index": 0, "prediction": "normal", "confidence": 0.8040, ...},
    {"index": 1, "prediction": "failure", "confidence": 1.0, ...}
  ],
  "summary": {
    "total_samples": 2,
    "failures_detected": 1,
    "normal_operations": 1,
    "failure_rate": 0.5
  }
}
```

---

## 🧪 Testing

### Run Comprehensive Tests
```bash
python test_bentoml_service.py
```

This will test:
- ✅ Health check
- ✅ Model info retrieval
- ✅ Normal prediction
- ✅ Failure detection
- ✅ Batch prediction

### Manual Testing
```bash
# Test with curl
curl -X POST http://localhost:3000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "temperature": 105,
    "vibration": 2.5,
    "pressure": 88,
    "rpm": 1550,
    "current": 15
  }'

# Test with Python
python -c "
import requests
data = {'temperature': 72, 'vibration': 0.35, 'pressure': 95, 'rpm': 1450, 'current': 8.5}
response = requests.post('http://localhost:3000/predict', json=data)
print(response.json())
"
```

---

## 📦 BentoML Commands Reference

### Model Management
```bash
# List all models
bentoml models list

# Get model details
bentoml models get predictive_maintenance_model:latest

# Delete a model
bentoml models delete predictive_maintenance_model:version

# Export model
bentoml models export predictive_maintenance_model:latest output_path/
```

### Bento Management
```bash
# Build Bento
bentoml build

# List Bentos
bentoml list

# Serve Bento
bentoml serve predictive_maintenance:latest --port 3000

# Delete Bento
bentoml delete predictive_maintenance:version
```

### Containerization
```bash
# Build Docker image
bentoml containerize predictive_maintenance:latest

# Build with custom tag
bentoml containerize predictive_maintenance:latest -t my-registry/pm-api:v1

# Push to registry
docker push my-registry/pm-api:v1
```

---

## 🚀 Production Readiness Checklist

### ✅ Completed
- [x] Model trained and validated (95.46% accuracy)
- [x] Model saved to BentoML store
- [x] Service implementation complete
- [x] API endpoints defined
- [x] Configuration files created
- [x] Test suite implemented

### 📋 Deployment Steps
- [ ] Test service locally (Option 1)
- [ ] Build Bento package (Option 2)
- [ ] Containerize with Docker (Option 2)
- [ ] Deploy to production (Option 3)
- [ ] Set up monitoring
- [ ] Configure auto-scaling
- [ ] Implement CI/CD pipeline

---

## 🔧 Troubleshooting

### Service Won't Start
```bash
# Check if port is in use
netstat -ano | findstr :3000

# Kill process
taskkill /F /PID <process_id>

# Try different port
bentoml serve service:PredictiveMaintenanceService --port 3001
```

### Model Not Found
```bash
# List all models
bentoml models list

# Re-save model
python save_to_bentoml.py
```

### Build Fails
```bash
# Check bentofile.yaml
cat bentofile.yaml

# Verify model files exist
ls models/

# Clean build cache
rm -rf .bentoml/
```

---

## 📊 Performance Optimization

### 1. Batch Processing
Use `/predict_batch` endpoint for multiple predictions to reduce overhead.

### 2. Caching
BentoML automatically caches models in memory for fast inference.

### 3. Scaling
```bash
# Run multiple workers
bentoml serve service:PredictiveMaintenanceService --workers 4

# Enable GPU (if available)
bentoml serve service:PredictiveMaintenanceService --enable-gpu
```

### 4. Monitoring
```bash
# Enable metrics
bentoml serve service:PredictiveMaintenanceService --enable-metrics

# Access metrics at /metrics endpoint
curl http://localhost:3000/metrics
```

---

## 🌐 Integration Examples

### Python Client
```python
import requests

class PredictiveMaintenanceClient:
    def __init__(self, base_url="http://localhost:3000"):
        self.base_url = base_url
    
    def predict(self, sensor_data):
        response = requests.post(
            f"{self.base_url}/predict",
            json=sensor_data
        )
        return response.json()
    
    def health_check(self):
        response = requests.get(f"{self.base_url}/health")
        return response.json()

# Usage
client = PredictiveMaintenanceClient()
result = client.predict({
    "temperature": 72,
    "vibration": 0.35,
    "pressure": 95,
    "rpm": 1450,
    "current": 8.5
})
print(result["prediction"])
```

### JavaScript Client
```javascript
async function predictMaintenance(sensorData) {
  const response = await fetch('http://localhost:3000/predict', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(sensorData)
  });
  return await response.json();
}

// Usage
const result = await predictMaintenance({
  temperature: 72,
  vibration: 0.35,
  pressure: 95,
  rpm: 1450,
  current: 8.5
});
console.log(result.prediction);
```

---

## 📈 Monitoring & Logging

### Enable Logging
```python
# In service.py
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
```

### Metrics Collection
```bash
# Prometheus metrics at /metrics
curl http://localhost:3000/metrics

# Integrate with Grafana for visualization
```

### Health Monitoring
```bash
# Set up health check alerts
curl http://localhost:3000/health

# Integrate with monitoring tools (Datadog, New Relic, etc.)
```

---

## ✅ Summary

**BentoML deployment is ready!** You have:

1. ✅ Model saved to BentoML (`predictive_maintenance_model:i4c3aqn3cwbxtrbd`)
2. ✅ Service implementation (`service.py`)
3. ✅ Configuration (`bentofile.yaml`)
4. ✅ Test suite (`test_bentoml_service.py`)
5. ✅ Deployment guide (this document)

**Next Steps:**
1. Start the service: `bentoml serve service:PredictiveMaintenanceService --port 3000`
2. Test endpoints: `python test_bentoml_service.py`
3. Build Bento: `bentoml build`
4. Containerize: `bentoml containerize predictive_maintenance:latest`
5. Deploy to production!

---

**Need Help?**
- BentoML Docs: https://docs.bentoml.org/
- BentoML GitHub: https://github.com/bentoml/BentoML
- Community: https://bentoml.org/community
