"""
MLflow Quickstart - Experiment Tracking & Model Registry
Run ML experiments with full tracking and model versioning
"""

import mlflow
import mlflow.sklearn
import numpy as np
import json
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
import warnings
warnings.filterwarnings('ignore')

print("="*80)
print("MLflow EXPERIMENT TRACKING - Predictive Maintenance")
print("="*80)

# Set MLflow tracking URI (local directory)
mlflow.set_tracking_uri("file:./mlruns")
print(f"\nMLflow Tracking URI: {mlflow.get_tracking_uri()}")

# Set experiment name
experiment_name = "predictive_maintenance"
mlflow.set_experiment(experiment_name)
print(f"Experiment: {experiment_name}")

# Load data
print("\n[1] Loading Training Data...")
data_dir = Path("data/raw")
data_files = list(data_dir.glob("historical_*.json"))

if not data_files:
    print("[ERROR] No historical data found!")
    print("Run: python src/data_collection/iot_simulator.py")
    exit(1)

with open(data_files[0], 'r') as f:
    data = json.load(f)

print(f"[OK] Loaded {len(data)} samples")

# Extract features
print("\n[2] Extracting Features...")
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
    labels.append(int(record['is_failing']))

X = np.array(features)
y = np.array(labels)

print(f"[OK] Features shape: {X.shape}")
print(f"[OK] Failure rate: {y.mean():.2%}")

# Split data
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print(f"[OK] Train: {len(X_train)} samples")
print(f"[OK] Test: {len(X_test)} samples")

# Feature names
feature_names = ['temperature', 'vibration', 'pressure', 'current', 'rpm']

# Experiment 1: Random Forest
print("\n" + "="*80)
print("[EXPERIMENT 1] Random Forest Classifier")
print("="*80)

with mlflow.start_run(run_name="RandomForest_Baseline"):
    # Log parameters
    rf_params = {
        'model_type': 'RandomForest',
        'n_estimators': 100,
        'max_depth': 10,
        'min_samples_split': 2,
        'random_state': 42
    }
    
    mlflow.log_params(rf_params)
    
    # Train model
    print("\nTraining Random Forest...")
    rf_model = RandomForestClassifier(**{k: v for k, v in rf_params.items() if k != 'model_type'})
    rf_model.fit(X_train, y_train)
    
    # Make predictions
    y_pred = rf_model.predict(X_test)
    y_pred_proba = rf_model.predict_proba(X_test)[:, 1]
    
    # Calculate metrics
    metrics = {
        'accuracy': accuracy_score(y_test, y_pred),
        'precision': precision_score(y_test, y_pred, zero_division=0),
        'recall': recall_score(y_test, y_pred, zero_division=0),
        'f1_score': f1_score(y_test, y_pred, zero_division=0),
        'roc_auc': roc_auc_score(y_test, y_pred_proba) if len(np.unique(y_test)) > 1 else 0
    }
    
    # Log metrics
    mlflow.log_metrics(metrics)
    
    # Log feature importance
    for i, (feature, importance) in enumerate(zip(feature_names, rf_model.feature_importances_)):
        mlflow.log_metric(f"feature_importance_{feature}", importance)
    
    # Log model
    mlflow.sklearn.log_model(rf_model, "model", input_example=X_train[:5])
    
    # Print results
    print("\n[OK] Random Forest Results:")
    for metric, value in metrics.items():
        print(f"   {metric}: {value:.4f}")
    
    run_id_rf = mlflow.active_run().info.run_id
    print(f"\n📊 Run ID: {run_id_rf}")

# Experiment 2: Random Forest (Tuned)
print("\n" + "="*80)
print("[EXPERIMENT 2] Random Forest - Tuned Hyperparameters")
print("="*80)

with mlflow.start_run(run_name="RandomForest_Tuned"):
    # Log parameters
    rf_tuned_params = {
        'model_type': 'RandomForest',
        'n_estimators': 200,
        'max_depth': 15,
        'min_samples_split': 5,
        'min_samples_leaf': 2,
        'random_state': 42
    }
    
    mlflow.log_params(rf_tuned_params)
    
    # Train model
    print("\nTraining Tuned Random Forest...")
    rf_tuned = RandomForestClassifier(**{k: v for k, v in rf_tuned_params.items() if k != 'model_type'})
    rf_tuned.fit(X_train, y_train)
    
    # Make predictions
    y_pred = rf_tuned.predict(X_test)
    y_pred_proba = rf_tuned.predict_proba(X_test)[:, 1]
    
    # Calculate metrics
    metrics = {
        'accuracy': accuracy_score(y_test, y_pred),
        'precision': precision_score(y_test, y_pred, zero_division=0),
        'recall': recall_score(y_test, y_pred, zero_division=0),
        'f1_score': f1_score(y_test, y_pred, zero_division=0),
        'roc_auc': roc_auc_score(y_test, y_pred_proba) if len(np.unique(y_test)) > 1 else 0
    }
    
    # Log metrics
    mlflow.log_metrics(metrics)
    
    # Log feature importance
    for feature, importance in zip(feature_names, rf_tuned.feature_importances_):
        mlflow.log_metric(f"feature_importance_{feature}", importance)
    
    # Log model
    mlflow.sklearn.log_model(rf_tuned, "model", input_example=X_train[:5])
    
    # Print results
    print("\n[OK] Tuned Random Forest Results:")
    for metric, value in metrics.items():
        print(f"   {metric}: {value:.4f}")
    
    run_id_rf_tuned = mlflow.active_run().info.run_id
    print(f"\n📊 Run ID: {run_id_rf_tuned}")

# Experiment 3: Gradient Boosting
print("\n" + "="*80)
print("[EXPERIMENT 3] Gradient Boosting Classifier")
print("="*80)

with mlflow.start_run(run_name="GradientBoosting"):
    # Log parameters
    gb_params = {
        'model_type': 'GradientBoosting',
        'n_estimators': 100,
        'learning_rate': 0.1,
        'max_depth': 5,
        'random_state': 42
    }
    
    mlflow.log_params(gb_params)
    
    # Train model
    print("\nTraining Gradient Boosting...")
    gb_model = GradientBoostingClassifier(**{k: v for k, v in gb_params.items() if k != 'model_type'})
    gb_model.fit(X_train, y_train)
    
    # Make predictions
    y_pred = gb_model.predict(X_test)
    y_pred_proba = gb_model.predict_proba(X_test)[:, 1]
    
    # Calculate metrics
    metrics = {
        'accuracy': accuracy_score(y_test, y_pred),
        'precision': precision_score(y_test, y_pred, zero_division=0),
        'recall': recall_score(y_test, y_pred, zero_division=0),
        'f1_score': f1_score(y_test, y_pred, zero_division=0),
        'roc_auc': roc_auc_score(y_test, y_pred_proba) if len(np.unique(y_test)) > 1 else 0
    }
    
    # Log metrics
    mlflow.log_metrics(metrics)
    
    # Log feature importance
    for feature, importance in zip(feature_names, gb_model.feature_importances_):
        mlflow.log_metric(f"feature_importance_{feature}", importance)
    
    # Log model
    mlflow.sklearn.log_model(gb_model, "model", input_example=X_train[:5])
    
    # Print results
    print("\n[OK] Gradient Boosting Results:")
    for metric, value in metrics.items():
        print(f"   {metric}: {value:.4f}")
    
    run_id_gb = mlflow.active_run().info.run_id
    print(f"\n📊 Run ID: {run_id_gb}")

# Summary
print("\n" + "="*80)
print("📊 EXPERIMENT SUMMARY")
print("="*80)

print("\n[OK] 3 experiments completed successfully!")
print(f"\nExperiment tracking saved to: {Path('mlruns').absolute()}")

print("\n🎯 NEXT STEPS:")
print("="*80)
print("\n1. View Results in MLflow UI:")
print("   mlflow ui --port 5000")
print("   Then open: http://localhost:5000")
print("\n2. Compare Experiments:")
print("   - View all runs in the MLflow UI")
print("   - Compare metrics across models")
print("   - Visualize parameter impact")
print("\n3. Load Best Model:")
print("   - Register the best model")
print("   - Deploy to production")
print("   - Track model versions")

print("\n" + "="*80)
print("[OK] MLflow experiment tracking complete!")
print("="*80)
