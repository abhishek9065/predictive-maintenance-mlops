# Deployment Guide

## Deployment Options

This guide covers deploying the predictive maintenance system to various environments.

## Local Deployment

### Prerequisites
- Python 3.9+
- Docker & Docker Compose

### Steps

1. **Clone and Setup**
```bash
cd MLops
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Start Services**
```bash
docker-compose up -d
```

3. **Access Services**
- API: http://localhost:8000
- MLflow: http://localhost:5000
- Airflow: http://localhost:8080

## AWS Deployment

### Architecture on AWS

```
Internet Gateway
       │
    ALB (Load Balancer)
       │
    ┌──┴──┐
    │ ECS │ (API Containers)
    └──┬──┘
       │
   ┌───┼───┐
   │       │
  RDS   S3 Bucket
```

### Step 1: Prepare AWS Infrastructure

```bash
# Install AWS CLI
pip install awscli

# Configure credentials
aws configure
```

### Step 2: Create ECR Repository

```bash
# Create repository
aws ecr create-repository --repository-name predictive-maintenance

# Get login command
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

# Build and push image
docker build -t predictive-maintenance:latest -f deployment/Dockerfile .
docker tag predictive-maintenance:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/predictive-maintenance:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/predictive-maintenance:latest
```

### Step 3: Deploy with AWS SageMaker

```python
import sagemaker
from sagemaker.sklearn import SKLearnModel

# Create SageMaker model
sklearn_model = SKLearnModel(
    model_data='s3://your-bucket/model.tar.gz',
    role='SageMakerRole',
    entry_point='inference.py',
    framework_version='1.0-1'
)

# Deploy endpoint
predictor = sklearn_model.deploy(
    instance_type='ml.m5.xlarge',
    initial_instance_count=2
)
```

### Step 4: Set up Monitoring

```bash
# Create CloudWatch dashboard
aws cloudwatch put-dashboard --dashboard-name PredictiveMaintenance --dashboard-body file://cloudwatch-dashboard.json
```

## Azure Deployment

### Architecture on Azure

```
Azure Front Door
       │
  App Service / AKS
       │
   ┌───┼───┐
   │       │
Azure SQL  Blob Storage
```

### Step 1: Create Azure Resources

```bash
# Install Azure CLI
pip install azure-cli

# Login
az login

# Create resource group
az group create --name ml-resources --location eastus

# Create container registry
az acr create --resource-group ml-resources --name mlopsregistry --sku Basic
```

### Step 2: Push Docker Image

```bash
# Login to ACR
az acr login --name mlopsregistry

# Build and push
docker build -t mlopsregistry.azurecr.io/predictive-maintenance:latest .
docker push mlopsregistry.azurecr.io/predictive-maintenance:latest
```

### Step 3: Deploy to Azure ML

```python
from azureml.core import Workspace, Model, Environment
from azureml.core.webservice import AciWebservice, Webservice

# Connect to workspace
ws = Workspace.from_config()

# Register model
model = Model.register(
    workspace=ws,
    model_path='models/random_forest_model.pkl',
    model_name='maintenance-predictor'
)

# Deploy
aci_config = AciWebservice.deploy_configuration(
    cpu_cores=2,
    memory_gb=4,
    auth_enabled=True
)

service = Model.deploy(
    workspace=ws,
    name='maintenance-api',
    models=[model],
    deployment_config=aci_config
)
```

## Kubernetes Deployment

### Step 1: Create Kubernetes Manifests

`deployment/kubernetes/deployment.yaml`:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: predictive-maintenance
spec:
  replicas: 3
  selector:
    matchLabels:
      app: predictive-maintenance
  template:
    metadata:
      labels:
        app: predictive-maintenance
    spec:
      containers:
      - name: api
        image: your-registry/predictive-maintenance:latest
        ports:
        - containerPort: 8000
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        env:
        - name: MLFLOW_TRACKING_URI
          value: "http://mlflow-service:5000"
```

### Step 2: Deploy to Kubernetes

```bash
# Apply deployment
kubectl apply -f deployment/kubernetes/deployment.yaml

# Apply service
kubectl apply -f deployment/kubernetes/service.yaml

# Check status
kubectl get pods
kubectl get services
```

### Step 3: Set up Ingress

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: predictive-maintenance-ingress
spec:
  rules:
  - host: api.predictive-maintenance.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: predictive-maintenance
            port:
              number: 8000
```

## Edge Deployment

### Convert Model to ONNX

```python
import torch
import onnx
from skl2onnx import convert_sklearn

# Convert sklearn model
onnx_model = convert_sklearn(
    sklearn_model,
    initial_types=[('input', FloatTensorType([None, n_features]))]
)

# Save
with open("model.onnx", "wb") as f:
    f.write(onnx_model.SerializeToString())
```

### Deploy to Edge Device

```python
import onnxruntime as rt

# Load model on edge device
session = rt.InferenceSession("model.onnx")

# Make prediction
input_name = session.get_inputs()[0].name
prediction = session.run(None, {input_name: input_data})
```

## Production Checklist

### Before Deployment
- [ ] All tests passing
- [ ] Models validated on test set
- [ ] API documentation complete
- [ ] Environment variables configured
- [ ] Secrets management set up
- [ ] Monitoring configured
- [ ] Backup strategy defined
- [ ] Disaster recovery plan ready

### After Deployment
- [ ] Health checks passing
- [ ] Monitoring dashboards active
- [ ] Alerts configured
- [ ] Performance baseline established
- [ ] Documentation updated
- [ ] Team trained on operations
- [ ] Incident response plan ready

## Rollback Strategy

```bash
# Kubernetes rollback
kubectl rollout undo deployment/predictive-maintenance

# Docker rollback
docker-compose down
docker-compose up -d --force-recreate

# SageMaker rollback
# Deploy previous model version
```

## Performance Optimization

### API Optimization
- Use connection pooling
- Enable response caching
- Implement request batching
- Use async endpoints where possible

### Model Optimization
- Model quantization for edge deployment
- Feature selection to reduce input size
- Model ensembling for better accuracy
- A/B testing for model comparison

### Infrastructure Optimization
- Auto-scaling based on load
- Use CDN for static assets
- Database query optimization
- Implement rate limiting
