# Production Deployment Guide

## Quick Start - Local Production

### 1. Prepare Production Model
```bash
python prepare_production_model.py
```

### 2. Start Production API
```bash
python production_api.py
```

### 3. Test Production API
```bash
# In another terminal
python test_production_api.py
```

## Production Deployment Options

### Option 1: Docker (Recommended)

#### Build and Run
```bash
# Build image
docker build -f Dockerfile.production -t predictive-maintenance:prod .

# Run container
docker run -d -p 8000:8000 --name pm-api predictive-maintenance:prod

# Check logs
docker logs -f pm-api

# Stop
docker stop pm-api
```

### Option 2: Docker Compose (Full Stack)

```bash
# Start all services
docker-compose -f docker-compose.production.yml up -d

# Check status
docker-compose -f docker-compose.production.yml ps

# View logs
docker-compose -f docker-compose.production.yml logs -f api

# Stop all
docker-compose -f docker-compose.production.yml down
```

### Option 3: Kubernetes

```bash
# Apply deployment
kubectl apply -f k8s/production/

# Check status
kubectl get pods
kubectl get services

# Scale
kubectl scale deployment pm-api --replicas=3

# Monitor
kubectl logs -f deployment/pm-api
```

## API Endpoints

### Health Check
```bash
curl http://localhost:8000/health
```

### Single Prediction
```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "temperature": 75.0,
    "vibration": 0.5,
    "pressure": 95.0,
    "rpm": 1450.0,
    "current": 9.0
  }'
```

### Batch Prediction
```bash
curl -X POST http://localhost:8000/predict/batch \
  -H "Content-Type: application/json" \
  -d '[
    {"temperature": 75.0, "vibration": 0.5, "pressure": 95.0, "rpm": 1450.0, "current": 9.0},
    {"temperature": 105.0, "vibration": 2.5, "pressure": 88.0, "rpm": 1550.0, "current": 15.0}
  ]'
```

### Model Info
```bash
curl http://localhost:8000/model/info
```

## Monitoring

### Access Grafana (if using Docker Compose)
- URL: http://localhost:3000
- Username: admin
- Password: admin

### Access Prometheus
- URL: http://localhost:9090

## Production Checklist

- [x] Model trained and validated
- [x] Production API server created
- [x] Docker container configured
- [x] Health checks implemented
- [x] API documentation available
- [x] Testing script ready
- [x] Monitoring setup (optional)
- [x] Deployment guide complete

## Performance Targets

- Response Time: < 100ms per prediction
- Throughput: > 100 requests/second
- Availability: 99.9% uptime
- Model Accuracy: > 90%

## Troubleshooting

### API won't start
```bash
# Check if port 8000 is in use
netstat -ano | findstr :8000

# Kill process if needed
taskkill /PID <PID> /F
```

### Model not loading
```bash
# Check model file exists
ls models/production_model.pkl

# Retrain if needed
python prepare_production_model.py
```

### Docker issues
```bash
# Rebuild image
docker build --no-cache -f Dockerfile.production -t predictive-maintenance:prod .

# Check container logs
docker logs pm-api
```

## Support

For issues or questions:
1. Check logs: `docker logs pm-api` or server console
2. Review API docs: http://localhost:8000/docs
3. Run tests: `python test_production_api.py`
