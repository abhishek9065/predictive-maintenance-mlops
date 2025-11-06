# MLOps Deployment Scripts

This directory contains automated deployment scripts for the MLOps project.

## deploy.py - Unified Deployment Manager

A comprehensive Python script for managing Docker builds, Kubernetes deployments, and BentoML operations.

### Prerequisites

```bash
# Install required tools
pip install requests

# Ensure you have:
# - Docker
# - kubectl (configured for your cluster)
# - bentoml
```

### Usage

#### 1. Build Docker Images

```bash
# Build all images
python deploy.py docker

# Build and push to registry
python deploy.py docker --push --registry your-registry.com
```

#### 2. Deploy to Kubernetes

```bash
# Deploy all resources
python deploy.py k8s

# Cleanup resources
python deploy.py k8s --cleanup
```

#### 3. BentoML Operations

```bash
# Save model to BentoML
python deploy.py bento --save

# Build Bento package
python deploy.py bento --build

# Containerize Bento
python deploy.py bento --containerize

# Serve locally
python deploy.py bento --serve
```

#### 4. Test API

```bash
# Test local API
python deploy.py test

# Test remote API
python deploy.py test --url http://your-api-url
```

#### 5. Full Deployment

```bash
# Complete deployment workflow
python deploy.py full

# Skip Docker build
python deploy.py full --skip-docker

# Skip Kubernetes deployment
python deploy.py full --skip-k8s
```

## PowerShell Scripts (Windows)

### build-all.ps1

```powershell
# Build all Docker images
.\scripts\build-all.ps1
```

### deploy-k8s.ps1

```powershell
# Deploy to Kubernetes
.\scripts\deploy-k8s.ps1

# With cleanup
.\scripts\deploy-k8s.ps1 -Cleanup
```

## Bash Scripts (Linux/Mac)

### build-all.sh

```bash
# Build all Docker images
./scripts/build-all.sh
```

### deploy-k8s.sh

```bash
# Deploy to Kubernetes
./scripts/deploy-k8s.sh

# With cleanup
./scripts/deploy-k8s.sh --cleanup
```

## Deployment Workflows

### Local Development

```bash
# 1. Build images
python deploy.py docker

# 2. Run with docker-compose
docker-compose up -d

# 3. Test
python deploy.py test
```

### Kubernetes Production

```bash
# 1. Build and push images
python deploy.py docker --push --registry your-registry.com

# 2. Deploy to cluster
python deploy.py k8s

# 3. Monitor
kubectl get pods -n kubeflow -w
```

### BentoML Deployment

```bash
# 1. Train and save model
python mlflow_advanced.py

# 2. Save to BentoML
python deploy.py bento --save

# 3. Build Bento
python deploy.py bento --build

# 4. Serve
python deploy.py bento --serve
```

## Troubleshooting

### Docker build fails
```bash
# Check Docker daemon
docker info

# Clean build cache
docker system prune -a
```

### Kubernetes deployment fails
```bash
# Check cluster connection
kubectl cluster-info

# Check namespace
kubectl get ns kubeflow

# View logs
kubectl logs <pod-name> -n kubeflow
```

### BentoML issues
```bash
# List models
bentoml models list

# Check service
bentoml list

# Clean cache
bentoml clean
```

## Environment Variables

Set these for custom configurations:

```bash
# Docker registry
export DOCKER_REGISTRY=your-registry.com

# Kubernetes namespace
export K8S_NAMESPACE=kubeflow

# API URL
export API_URL=http://api.mlops.local

# Model path
export MODEL_PATH=models/production
```

## CI/CD Integration

The deployment scripts can be integrated into CI/CD pipelines:

### GitHub Actions Example

```yaml
- name: Build and Deploy
  run: |
    python deploy.py docker --push --registry ${{ secrets.REGISTRY }}
    python deploy.py k8s
```

### GitLab CI Example

```yaml
deploy:
  script:
    - python deploy.py full
```

## Advanced Options

### Custom Docker Registry

```bash
# Build and push to custom registry
python deploy.py docker --push --registry harbor.mycompany.com/mlops
```

### Selective Deployment

```python
from deploy import DeploymentManager

manager = DeploymentManager()

# Build specific image
manager.docker_build("mlops-api", "Dockerfile.api")

# Deploy specific manifest
manager.k8s_apply("api-deployment.yaml")
```

## Monitoring Deployment

```bash
# Watch pods
kubectl get pods -n kubeflow -w

# View logs
kubectl logs -f <pod-name> -n kubeflow

# Check services
kubectl get svc -n kubeflow

# Port forward
kubectl port-forward svc/mlops-api-service 8000:80 -n kubeflow
```
