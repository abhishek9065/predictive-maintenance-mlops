# Advanced MLOps Components Implementation

## Overview

This document describes the implementation of advanced MLOps components:
1. **Hyperparameter Tuning** using Katib (Kubeflow)
2. **Containerization** using Docker and Kubernetes
3. **API Serving** using FastAPI and Flask
4. **Model Deployment** using BentoML

## 1. Hyperparameter Tuning with Katib

### Components

#### Training Script (`katib_tuning.py`)
- Supports 3 model types: RandomForest, GradientBoosting, LogisticRegression
- Accepts hyperparameters via command-line arguments
- Outputs metrics in Katib-compatible format (stdout parsing)
- Saves models to `models/katib/`

#### Katib Experiments (`kubernetes/katib-experiment.yaml`)

**Three experiment configurations:**

1. **Random Forest** (Random Search)
   - Parameters: n_estimators (50-200), max_depth (5-30), min_samples_split (2-10), min_samples_leaf (1-5)
   - 20 trials max, 3 parallel

2. **Gradient Boosting** (Bayesian Optimization)
   - Parameters: n_estimators (50-150), max_depth (3-10), learning_rate (0.01-0.3), min_samples_split (2-8)
   - 15 trials max, 2 parallel

3. **Logistic Regression** (Grid Search)
   - Parameters: C (0.01-10.0), max_iter (500-2000), penalty (l1/l2)
   - 24 trials max, 4 parallel

### Running Katib Experiments

```bash
# Apply namespace
kubectl apply -f kubernetes/namespace.yaml

# Create persistent volumes
kubectl apply -f kubernetes/persistent-volumes.yaml

# Run experiments
kubectl apply -f kubernetes/katib-experiment.yaml

# Monitor experiments
kubectl get experiments -n kubeflow
kubectl describe experiment predictive-maintenance-tuning -n kubeflow

# View trials
kubectl get trials -n kubeflow
kubectl logs <trial-pod-name> -n kubeflow

# Get best parameters
kubectl get experiment predictive-maintenance-tuning -n kubeflow -o yaml
```

## 2. Containerization

### Docker Images

#### Training Container (`Dockerfile`)
```bash
# Build
docker build -t mlops-predictive-maintenance:latest .

# Run locally
docker run -v $(pwd)/data:/app/data -v $(pwd)/models:/app/models \
  mlops-predictive-maintenance:latest \
  python katib_tuning.py --model=random_forest --n_estimators=100
```

#### API Container (`Dockerfile.api`)
```bash
# Build
docker build -f Dockerfile.api -t mlops-api:latest .

# Run locally
docker run -p 8000:8000 -v $(pwd)/models:/app/models mlops-api:latest

# Test
curl http://localhost:8000/health
```

#### MLflow Container (`Dockerfile.mlflow`)
```bash
# Build
docker build -f Dockerfile.mlflow -t mlops-mlflow:latest .

# Run
docker run -p 5000:5000 -v $(pwd)/mlruns:/mlflow/mlruns mlops-mlflow:latest
```

### Kubernetes Deployments

#### Deploy MLflow
```bash
kubectl apply -f kubernetes/mlflow-deployment.yaml

# Access MLflow UI
kubectl port-forward svc/mlflow-service 5000:5000 -n kubeflow
# Visit http://localhost:5000
```

#### Deploy API
```bash
kubectl apply -f kubernetes/api-deployment.yaml

# Get external IP
kubectl get svc mlops-api-service -n kubeflow

# Test
curl http://<external-ip>/health
```

### Features

- **Persistent Volumes**: Data and models persisted across pod restarts
- **Auto-scaling**: HPA configured (2-10 replicas based on CPU/memory)
- **Health Checks**: Liveness and readiness probes
- **Resource Limits**: CPU and memory constraints
- **Ingress**: External access configuration

## 3. API Serving

### FastAPI Implementation (`src/deployment/api_fastapi.py`)

**Features:**
- Pydantic models for request/response validation
- Prometheus metrics integration
- CORS middleware
- Auto-generated OpenAPI documentation
- Async support
- Health checks
- Model reload endpoint

**Endpoints:**
- `GET /` - API information
- `GET /health` - Health check
- `POST /predict` - Make predictions
- `GET /metrics` - Prometheus metrics
- `GET /model/info` - Model information
- `GET /model/metrics` - Performance metrics
- `POST /model/reload` - Reload model

**Usage:**
```bash
# Run locally
python src/deployment/api_fastapi.py

# Or with uvicorn
uvicorn src.deployment.api_fastapi:app --host 0.0.0.0 --port 8000

# Test prediction
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "data": [{
      "temperature": 75.0,
      "vibration": 3.5,
      "pressure": 100.0,
      "rpm": 1500.0,
      "power_consumption": 250.0
    }],
    "return_probability": true
  }'

# View docs
open http://localhost:8000/docs
```

### Flask Implementation (`src/deployment/api_flask.py`)

**Features:**
- Similar endpoints to FastAPI
- CORS support
- Prometheus metrics
- Error handling
- Request validation

**Usage:**
```bash
# Run
python src/deployment/api_flask.py

# Or with gunicorn (production)
gunicorn -w 4 -b 0.0.0.0:8000 src.deployment.api_flask:app
```

## 4. BentoML Deployment

### Components

#### Service Definition (`src/deployment/bentoml_service.py`)
- Async prediction endpoint
- Health check
- Model info endpoint
- Automatic model loading from BentoML store

#### Model Saver (`src/deployment/bentoml_save.py`)
Save trained models to BentoML:
```bash
# Save production model
python src/deployment/bentoml_save.py --production

# Save specific model
python src/deployment/bentoml_save.py --model-path models/staging/model.pkl

# List models
python src/deployment/bentoml_save.py --list
```

#### Bento Configuration (`bentofile.yaml`)
Defines service packaging and dependencies

### Building and Deploying with BentoML

```bash
# 1. Save model to BentoML store
python src/deployment/bentoml_save.py --production

# 2. Build Bento
bentoml build

# 3. Serve locally
bentoml serve predictive_maintenance:latest

# 4. Build Docker image
bentoml containerize predictive_maintenance:latest -t mlops-bento:latest

# 5. Run container
docker run -p 3000:3000 mlops-bento:latest

# 6. Deploy to Kubernetes
bentoml deploy predictive_maintenance:latest --platform kubernetes -n kubeflow
```

### Testing BentoML API

```bash
# Health check
curl http://localhost:3000/health

# Prediction
curl -X POST http://localhost:3000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "data": [{
      "temperature": 75.0,
      "vibration": 3.5,
      "pressure": 100.0,
      "rpm": 1500.0,
      "power_consumption": 250.0
    }],
    "return_probability": true
  }'

# Model info
curl http://localhost:3000/model_info
```

## Complete Deployment Workflow

### Local Development

```bash
# 1. Train model with MLflow
python mlflow_advanced.py

# 2. Save to BentoML
python src/deployment/bentoml_save.py --production

# 3. Serve with BentoML
bentoml serve predictive_maintenance:latest

# 4. Test
curl http://localhost:3000/health
```

### Docker Deployment

```bash
# 1. Build images
docker build -t mlops-predictive-maintenance:latest .
docker build -f Dockerfile.api -t mlops-api:latest .
docker build -f Dockerfile.mlflow -t mlops-mlflow:latest .

# 2. Run with docker-compose
docker-compose up -d

# 3. Access services
# MLflow: http://localhost:5000
# API: http://localhost:8000
```

### Kubernetes Deployment

```bash
# 1. Create namespace and volumes
kubectl apply -f kubernetes/namespace.yaml
kubectl apply -f kubernetes/persistent-volumes.yaml

# 2. Deploy MLflow
kubectl apply -f kubernetes/mlflow-deployment.yaml

# 3. Deploy API
kubectl apply -f kubernetes/api-deployment.yaml

# 4. Run Katib experiments
kubectl apply -f kubernetes/katib-experiment.yaml

# 5. Monitor
kubectl get pods -n kubeflow
kubectl get svc -n kubeflow
kubectl get experiments -n kubeflow
```

## Performance Optimization

### API Performance
- **FastAPI**: Async support, ~10,000 req/s
- **Flask**: Sync, ~1,000 req/s with gunicorn
- **BentoML**: Optimized for ML serving, adaptive batching

### Scaling
- **Horizontal Pod Autoscaler**: 2-10 replicas based on load
- **Model caching**: In-memory model storage
- **Batch predictions**: Support up to 1000 records per request

### Monitoring
- **Prometheus metrics**: Request count, latency, errors
- **Health checks**: Liveness and readiness probes
- **Logging**: Structured logging with levels

## Best Practices

1. **Version Control**: Tag Docker images and models with versions
2. **Resource Limits**: Set CPU/memory limits to prevent resource exhaustion
3. **Health Checks**: Implement proper health and readiness checks
4. **Graceful Shutdown**: Handle SIGTERM for graceful pod termination
5. **Security**: Use secrets for sensitive data, run as non-root user
6. **Monitoring**: Collect metrics and logs for observability

## Troubleshooting

### Common Issues

**Model not loading:**
```bash
# Check model exists
ls -la models/production/

# Check logs
kubectl logs <pod-name> -n kubeflow

# Reload model
curl -X POST http://localhost:8000/model/reload
```

**Katib experiment failing:**
```bash
# Check trial logs
kubectl get trials -n kubeflow
kubectl logs <trial-pod> -n kubeflow

# Check events
kubectl describe experiment predictive-maintenance-tuning -n kubeflow
```

**API timeout:**
```bash
# Check resources
kubectl top pods -n kubeflow

# Increase timeout
# Edit deployment with longer timeouts
```

## Next Steps

1. **CI/CD Integration**: Set up GitHub Actions for automated builds
2. **Model Registry**: Use MLflow Model Registry for version control
3. **A/B Testing**: Deploy multiple model versions
4. **Feature Store**: Implement feature caching
5. **Drift Detection**: Monitor model performance over time

## References

- Kubeflow Katib: https://www.kubeflow.org/docs/components/katib/
- BentoML: https://docs.bentoml.org/
- FastAPI: https://fastapi.tiangolo.com/
- Kubernetes: https://kubernetes.io/docs/
