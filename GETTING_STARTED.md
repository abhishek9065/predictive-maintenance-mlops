# Predictive Maintenance MLOps - Getting Started Guide

## 🚀 Quick Start Guide

This guide will help you set up and run the predictive maintenance MLOps project from scratch.

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.8 or higher** - [Download Python](https://www.python.org/downloads/)
- **Git** - [Download Git](https://git-scm.com/downloads)
- **Docker & Docker Compose** (optional, for containerized deployment) - [Download Docker](https://www.docker.com/get-started)
- **VS Code** (recommended) - [Download VS Code](https://code.visualstudio.com/)

## Step 1: Environment Setup

### 1.1 Create Virtual Environment

```powershell
# Navigate to project directory
cd "c:\Users\abhis\Downloads\Data Science 2.0\MLops"

# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# If you get an execution policy error, run:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 1.2 Install Dependencies

```powershell
# Upgrade pip
python -m pip install --upgrade pip

# Install all required packages
pip install -r requirements.txt
```

This will install all necessary libraries including:
- Machine Learning: scikit-learn, xgboost, tensorflow
- MLOps: mlflow, dvc
- API: fastapi, uvicorn
- Data Processing: pandas, numpy
- And many more...

## Step 2: Generate Sample Data

Before training models, you need data. Run the IoT simulator to generate sample sensor data:

```powershell
# Generate historical training data
python src/data_collection/iot_simulator.py
```

This will:
- Generate 5,000 historical data points
- Include both normal and failure scenarios
- Save data to `data/raw/` directory
- Simulate real-time sensor streams

Expected output:
```
============================================================
GENERATING HISTORICAL DATA FOR TRAINING
============================================================
Generating 10000 historical data points...
Historical data saved to data/raw/historical_data_YYYYMMDD_HHMMSS.json
```

## Step 3: Data Preprocessing

Clean and prepare the data for training:

```powershell
# Create a simple preprocessing script
python -c "
from src.preprocessing import DataCleaner, FeatureEngineer
import yaml
from pathlib import Path

# Load config
with open('config/config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Get latest data file
data_path = Path('data/raw')
data_files = sorted(data_path.glob('historical_data_*.json'))
latest_file = data_files[-1]

# Clean data
cleaner = DataCleaner(config)
df = cleaner.load_data(str(latest_file))
df_clean = cleaner.clean_pipeline(df, remove_outliers=True)

# Engineer features
engineer = FeatureEngineer(config)
df_features = engineer.engineer_features_pipeline(df_clean)

# Save
df_features.to_csv('data/features/features.csv', index=False)
print(f'Features created: {df_features.shape}')
"
```

## Step 4: Train Models

### 4.1 Start MLflow Tracking Server

Open a new terminal window:

```powershell
# Start MLflow server
mlflow server --host 0.0.0.0 --port 5000
```

Keep this running and access the UI at: http://localhost:5000

### 4.2 Train Models

In your original terminal:

```powershell
# Create and run training script
python -c "
import yaml
import pandas as pd
import mlflow
from src.models import RandomForestModel, XGBoostModel
from src.preprocessing import DataSplitter

# Load config
with open('config/config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Load features
df = pd.read_csv('data/features/features.csv')

# Split data
splitter = DataSplitter(config)
X_train, X_val, X_test, y_train, y_val, y_test = splitter.time_series_split(df)

# Set MLflow
mlflow.set_tracking_uri('http://localhost:5000')
mlflow.set_experiment('predictive_maintenance')

# Train Random Forest
print('Training Random Forest...')
rf_model = RandomForestModel(config)
rf_metrics = rf_model.train(X_train, y_train, X_val, y_val)
rf_model.save_model('models/random_forest_model.pkl')

# Train XGBoost
print('Training XGBoost...')
xgb_model = XGBoostModel(config)
xgb_metrics = xgb_model.train(X_train, y_train, X_val, y_val)
xgb_model.save_model('models/xgboost_model.pkl')

# Evaluate on test set
print('\\nTest Set Results:')
print('Random Forest:', rf_model.evaluate(X_test, y_test))
print('XGBoost:', xgb_model.evaluate(X_test, y_test))
"
```

## Step 5: Deploy API

### 5.1 Start the FastAPI Server

```powershell
# Run the API server
uvicorn src.deployment.api:app --reload --host 0.0.0.0 --port 8000
```

Access the interactive API documentation at: http://localhost:8000/docs

### 5.2 Test the API

Open a new terminal and test with curl or Python:

```powershell
# Using Python
python -c "
import requests
import json

# Prepare test data
data = {
    'equipment_id': 'PUMP_001',
    'sensor_data': {
        'temperature': 75.5,
        'vibration': 8.2,
        'pressure': 105.0,
        'current': 30.5,
        'rpm': 2500,
        'operating_hours': 500,
        'time_since_maintenance': 200
    },
    'model_name': 'random_forest'
}

# Make prediction
response = requests.post('http://localhost:8000/predict', json=data)
print(json.dumps(response.json(), indent=2))
"
```

Expected output:
```json
{
  "equipment_id": "PUMP_001",
  "timestamp": "2025-11-05T10:30:00",
  "prediction": 0,
  "failure_probability": 0.23,
  "risk_level": "low",
  "model_name": "random_forest",
  "processing_time_ms": 45.32
}
```

## Step 6: Run with Docker (Optional)

### 6.1 Start All Services

```powershell
# Build and start all containers
docker-compose up -d
```

This will start:
- **FastAPI API** - http://localhost:8000
- **MLflow** - http://localhost:5000
- **Airflow** - http://localhost:8080 (username: admin, password: admin)
- **Grafana** - http://localhost:3000 (username: admin, password: admin)
- **PostgreSQL** - localhost:5432

### 6.2 Check Container Status

```powershell
# View running containers
docker-compose ps

# View logs
docker-compose logs -f api
```

### 6.3 Stop Services

```powershell
# Stop all containers
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

## Step 7: Monitor Model Performance

### 7.1 Check Model Metrics

```powershell
python -c "
from src.monitoring import PerformanceMonitor
import yaml

with open('config/config.yaml', 'r') as f:
    config = yaml.safe_load(f)

monitor = PerformanceMonitor(config)
report = monitor.generate_performance_report(time_window_hours=24)
print(report)
"
```

### 7.2 Detect Data Drift

```powershell
python -c "
from src.monitoring import DriftDetector
import pandas as pd
import yaml

with open('config/config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Load reference and current data
reference_data = pd.read_csv('data/features/features.csv').head(1000)
current_data = pd.read_csv('data/features/features.csv').tail(100)

detector = DriftDetector(reference_data, config)
results = detector.detect_drift(current_data)

if results['drift_detected']:
    print(f'Drift detected in: {results[\"drifted_features\"]}')
else:
    print('No drift detected')
"
```

## Step 8: Run Airflow Pipelines

### 8.1 Access Airflow UI

Go to http://localhost:8080 (if using Docker)

Default credentials:
- Username: `admin`
- Password: `admin`

### 8.2 Enable DAGs

1. Navigate to the Airflow UI
2. Enable the following DAGs:
   - `data_pipeline` - Runs hourly for data collection
   - `training_pipeline` - Runs weekly for model retraining

### 8.3 Trigger Manual Run

Click on the DAG name, then click "Trigger DAG" button.

## Common Issues & Solutions

### Issue: Import errors when running scripts

**Solution:** Make sure you're in the project root directory and virtual environment is activated:
```powershell
cd "c:\Users\abhis\Downloads\Data Science 2.0\MLops"
.\venv\Scripts\Activate.ps1
```

### Issue: Port already in use

**Solution:** Change the port in the command:
```powershell
uvicorn src.deployment.api:app --reload --port 8001
```

### Issue: MLflow tracking URI error

**Solution:** Make sure MLflow server is running:
```powershell
mlflow server --host 0.0.0.0 --port 5000
```

### Issue: Docker containers won't start

**Solution:** Check Docker is running and ports are available:
```powershell
docker ps
docker-compose down
docker-compose up -d
```

## Next Steps

1. **Explore the API**: Visit http://localhost:8000/docs
2. **View Experiments**: Check MLflow at http://localhost:5000
3. **Monitor Pipelines**: Access Airflow at http://localhost:8080
4. **Customize Models**: Edit `config/config.yaml` to adjust parameters
5. **Add More Data**: Run the IoT simulator to generate more training data
6. **Deploy to Cloud**: Follow `docs/deployment_guide.md` for cloud deployment

## Additional Resources

- **API Documentation**: http://localhost:8000/docs
- **MLflow Tracking**: http://localhost:5000
- **Project Structure**: See `README.md`
- **Configuration**: Review `config/config.yaml`

## Need Help?

- Check the `docs/` folder for detailed documentation
- Review the code comments in `src/` files
- Consult the MLOps best practices documentation

---

**Congratulations! 🎉** You now have a fully functional predictive maintenance MLOps system running locally.
