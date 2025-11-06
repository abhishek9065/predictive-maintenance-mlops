"""
Pipeline Orchestration - Complete ML Workflow
Simulates Airflow DAG without requiring Apache Airflow installation
"""

import sys
from pathlib import Path
from datetime import datetime
import json
import subprocess

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


class PipelineContext:
    """Stores data between pipeline tasks (like Airflow XCom)"""
    def __init__(self):
        self.storage = {}
    
    def set(self, key, value):
        self.storage[key] = value
    
    def get(self, key, default=None):
        return self.storage.get(key, default)


def task_1_collect_data(context):
    """Task 1: Verify sensor data availability"""
    print("\n" + "="*80)
    print("TASK 1: DATA COLLECTION CHECK")
    print("="*80)
    
    # Check for existing data files
    data_dir = project_root / "data/raw"
    historical_files = list(data_dir.glob("historical_*.json"))
    realtime_files = list(data_dir.glob("sensor_data_*.json"))
    
    print(f"[INFO] Data directory: {data_dir}")
    print(f"   Historical files: {len(historical_files)}")
    print(f"   Real-time files: {len(realtime_files)}")
    
    if not historical_files:
        print("\n[ERROR] No historical data found!")
        print("   Run: python test_simple.py (to generate data)")
        raise Exception("No training data available")
    
    # Load and validate latest historical file
    latest_file = max(historical_files, key=lambda p: p.stat().st_mtime)
    with open(latest_file, 'r') as f:
        data = json.load(f)
    
    print(f"\n   Latest file: {latest_file.name}")
    print(f"   Sample count: {len(data)}")
    
    total_files = len(historical_files) + len(realtime_files)
    
    print(f"\n[OK] Data validation passed")
    print(f"   Total files available: {total_files}")
    
    context.set('data_files_count', total_files)
    context.set('training_samples', len(data))
    return {"status": "success", "files": total_files}


def task_2_validate_data(context):
    """Task 2: Validate data quality"""
    print("\n" + "="*80)
    print("TASK 2: DATA QUALITY VALIDATION")
    print("="*80)
    
    data_dir = project_root / "data/raw"
    historical_files = sorted(data_dir.glob("historical_*.json"))
    
    if not historical_files:
        raise Exception("No historical data files found")
    
    with open(historical_files[-1], 'r') as f:
        data = json.load(f)
    
    print(f"[INFO] Loaded {len(data)} records from {historical_files[-1].name}")
    
    # Quality checks
    checks = []
    
    # Check 1: Sample size
    check_1 = len(data) >= 100
    checks.append(check_1)
    print(f"   {'[OK]' if check_1 else '[ERROR]'} Sample size: {len(data)} (min: 100)")
    
    # Check 2: Required fields
    required_fields = ['equipment_id', 'timestamp', 'sensors', 'is_failing']
    check_2 = all(field in data[0] for field in required_fields)
    checks.append(check_2)
    print(f"   {'[OK]' if check_2 else '[ERROR]'} Required fields present")
    
    # Check 3: Sensor data
    required_sensors = ['temperature', 'vibration', 'pressure', 'current', 'rpm']
    check_3 = all(sensor in data[0]['sensors'] for sensor in required_sensors)
    checks.append(check_3)
    print(f"   {'[OK]' if check_3 else '[ERROR]'} All sensors present")
    
    # Check 4: Class balance
    failure_rate = sum(1 for r in data if r['is_failing']) / len(data)
    check_4 = 0.05 <= failure_rate <= 0.30
    checks.append(check_4)
    print(f"   {'[OK]' if check_4 else '[WARNING]'} Failure rate: {failure_rate:.2%}")
    
    quality_score = sum(checks) / len(checks)
    print(f"\n[INFO] Quality Score: {quality_score:.1%} ({sum(checks)}/{len(checks)} checks passed)")
    
    context.set('quality_score', quality_score)
    context.set('sample_count', len(data))
    
    if quality_score < 0.75:
        raise Exception(f"Data quality too low: {quality_score:.1%}")
    
    return {"status": "success", "score": quality_score}


def task_3_train_models(context):
    """Task 3: Train ML models"""
    print("\n" + "="*80)
    print("TASK 3: MODEL TRAINING")
    print("="*80)
    
    # Train models directly in Python (avoid subprocess Unicode issues)
    import mlflow
    import numpy as np
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
    
    # Set MLflow tracking URI (Windows-compatible) - use file:/// for local paths
    mlflow_dir = (project_root / 'mlruns').resolve()
    mlflow.set_tracking_uri(f"file:///{mlflow_dir.as_posix()}")
    mlflow.set_experiment("predictive_maintenance")
    
    # Load data
    data_dir = project_root / "data/raw"
    historical_files = sorted(data_dir.glob("historical_*.json"))
    with open(historical_files[-1], 'r') as f:
        data = json.load(f)
    
    print(f"[*] Loaded {len(data)} samples")
    
    # Extract features
    X = np.array([[
        record['sensors']['temperature']['value'],
        record['sensors']['vibration']['value'],
        record['sensors']['pressure']['value'],
        record['sensors']['current']['value'],
        record['sensors']['rpm']['value']
    ] for record in data])
    
    y = np.array([record['is_failing'] for record in data])
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print(f"[*] Train: {len(X_train)} samples, Test: {len(X_test)} samples")
    
    run_ids = []
    
    # Experiment 1: Random Forest Baseline
    print("\n[1/3] Training Random Forest (baseline)...")
    with mlflow.start_run(run_name="random_forest_baseline") as run:
        try:
            model = RandomForestClassifier(n_estimators=100, random_state=42)
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
            
            # Calculate metrics
            acc = accuracy_score(y_test, y_pred)
            prec = precision_score(y_test, y_pred)
            rec = recall_score(y_test, y_pred)
            f1 = f1_score(y_test, y_pred)
            roc = roc_auc_score(y_test, y_pred)
            
            # Log params and metrics
            mlflow.log_param("model_type", "random_forest")
            mlflow.log_param("n_estimators", 100)
            mlflow.log_metric("accuracy", acc)
            mlflow.log_metric("precision", prec)
            mlflow.log_metric("recall", rec)
            mlflow.log_metric("f1_score", f1)
            mlflow.log_metric("roc_auc", roc)
            mlflow.sklearn.log_model(model, "model")
            
            run_ids.append(run.info.run_id)
            print(f"    Run ID: {run.info.run_id}")
            print(f"    Accuracy: {acc:.4f}")
        except Exception as e:
            print(f"    Error in Random Forest baseline: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    # Experiment 2: Tuned Random Forest
    print("\n[2/3] Training Random Forest (tuned)...")
    with mlflow.start_run(run_name="random_forest_tuned") as run:
        model = RandomForestClassifier(
            n_estimators=200,
            max_depth=20,
            min_samples_split=5,
            random_state=42
        )
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        
        mlflow.log_param("model_type", "random_forest_tuned")
        mlflow.log_param("n_estimators", 200)
        mlflow.log_param("max_depth", 20)
        mlflow.log_metric("accuracy", float(accuracy_score(y_test, y_pred)))
        mlflow.log_metric("precision", float(precision_score(y_test, y_pred)))
        mlflow.log_metric("recall", float(recall_score(y_test, y_pred)))
        mlflow.log_metric("f1_score", float(f1_score(y_test, y_pred)))
        mlflow.log_metric("roc_auc", float(roc_auc_score(y_test, y_pred)))
        mlflow.sklearn.log_model(model, "model")
        
        run_ids.append(run.info.run_id)
        print(f"    Run ID: {run.info.run_id}")
        print(f"    Accuracy: {accuracy_score(y_test, y_pred):.4f}")
    
    # Experiment 3: Gradient Boosting
    print("\n[3/3] Training Gradient Boosting...")
    with mlflow.start_run(run_name="gradient_boosting") as run:
        model = GradientBoostingClassifier(
            n_estimators=100,
            learning_rate=0.1,
            random_state=42
        )
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        
        mlflow.log_param("model_type", "gradient_boosting")
        mlflow.log_param("n_estimators", 100)
        mlflow.log_param("learning_rate", 0.1)
        mlflow.log_metric("accuracy", float(accuracy_score(y_test, y_pred)))
        mlflow.log_metric("precision", float(precision_score(y_test, y_pred)))
        mlflow.log_metric("recall", float(recall_score(y_test, y_pred)))
        mlflow.log_metric("f1_score", float(f1_score(y_test, y_pred)))
        mlflow.log_metric("roc_auc", float(roc_auc_score(y_test, y_pred)))
        mlflow.sklearn.log_model(model, "model")
        
        run_ids.append(run.info.run_id)
        print(f"    Run ID: {run.info.run_id}")
        print(f"    Accuracy: {accuracy_score(y_test, y_pred):.4f}")
    
    print(f"\n[OK] Model training completed")
    print(f"    Models trained: {len(run_ids)}")
    
    context.set('model_run_ids', run_ids)
    return {"status": "success", "models": len(run_ids)}


def task_4_evaluate_models(context):
    """Task 4: Evaluate and select best model"""
    print("\n" + "="*80)
    print("TASK 4: MODEL EVALUATION")
    print("="*80)
    
    import mlflow
    
    mlflow_dir = (project_root / 'mlruns').resolve()
    mlflow.set_tracking_uri(f"file:///{mlflow_dir.as_posix()}")
    
    # Get experiment
    client = mlflow.tracking.MlflowClient()
    experiment = client.get_experiment_by_name("predictive_maintenance")
    
    if experiment is None:
        raise Exception("No experiment found")
    
    # Get all runs
    runs = client.search_runs(
        experiment_ids=[experiment.experiment_id],
        order_by=["metrics.accuracy DESC"],
        max_results=10
    )
    
    if not runs:
        raise Exception("No model runs found")
    
    print(f"[INFO] Found {len(runs)} model runs")
    print("\n🏆 Top 3 Models:")
    
    for i, run in enumerate(runs[:3], 1):
        metrics = run.data.metrics
        params = run.data.params
        print(f"\n   {i}. Model: {params.get('model_type', 'Unknown')}")
        print(f"      Run ID: {run.info.run_id[:16]}...")
        print(f"      Accuracy: {metrics.get('accuracy', 0):.4f}")
        print(f"      F1 Score: {metrics.get('f1_score', 0):.4f}")
    
    # Select best
    best_run = runs[0]
    best_accuracy = best_run.data.metrics.get('accuracy', 0)
    
    print(f"\n[OK] Best model selected: {best_run.info.run_id[:16]}...")
    print(f"   Accuracy: {best_accuracy:.4f}")
    
    context.set('best_model_id', best_run.info.run_id)
    context.set('best_accuracy', best_accuracy)
    
    return {"status": "success", "accuracy": best_accuracy}


def task_5_deploy_model(context):
    """Task 5: Deploy best model to production"""
    print("\n" + "="*80)
    print("TASK 5: MODEL DEPLOYMENT")
    print("="*80)
    
    import mlflow
    import joblib
    
    best_model_id = context.get('best_model_id')
    if not best_model_id:
        raise Exception("No best model ID found")
    
    mlflow_dir = (project_root / 'mlruns').resolve()
    mlflow.set_tracking_uri(f"file:///{mlflow_dir.as_posix()}")
    
    print(f"📦 Loading model: {best_model_id[:16]}...")
    
    # Load model
    model_uri = f"runs:/{best_model_id}/model"
    model = mlflow.sklearn.load_model(model_uri)
    
    # Save to production
    production_path = project_root / "models/production_model.pkl"
    production_path.parent.mkdir(exist_ok=True)
    joblib.dump(model, production_path)
    
    print(f"[OK] Model deployed to: {production_path.name}")
    
    # Create metadata
    metadata = {
        "model_id": best_model_id,
        "deployed_at": datetime.now().isoformat(),
        "accuracy": context.get('best_accuracy'),
        "deployment_path": str(production_path)
    }
    
    metadata_path = project_root / "models/deployment_metadata.json"
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"[OK] Metadata saved to: {metadata_path.name}")
    
    context.set('production_path', str(production_path))
    return {"status": "success", "path": str(production_path)}


def task_6_notify(context):
    """Task 6: Send completion notification"""
    print("\n" + "="*80)
    print("TASK 6: PIPELINE COMPLETION NOTIFICATION")
    print("="*80)
    
    # Gather metrics
    data_files = context.get('data_files_count', 'N/A')
    sample_count = context.get('sample_count', 'N/A')
    quality_score = context.get('quality_score', 0)
    models_trained = len(context.get('model_run_ids', []))
    best_accuracy = context.get('best_accuracy', 0)
    
    summary = f"""
+============================================================+
|   PREDICTIVE MAINTENANCE PIPELINE - COMPLETED             |
+============================================================+

Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

[INFO] Pipeline Results:
   - Data Files: {data_files}
   - Training Samples: {sample_count}
   - Data Quality: {quality_score:.1%}
   - Models Trained: {models_trained}
   - Best Accuracy: {best_accuracy:.4f}
   - Status: SUCCESS [OK]

[SUCCESS] Model deployed and ready for predictions!

Quick Access:
   - API Docs: http://localhost:8000/docs
   - MLflow UI: http://localhost:5000
   - Production Model: models/production_model.pkl
"""
    
    print(summary)
    
    # Save notification
    notification_path = project_root / "pipeline_results.txt"
    with open(notification_path, 'w') as f:
        f.write(summary)
    
    return {"status": "success", "summary": summary}


def run_pipeline():
    """Execute the complete ML pipeline"""
    
    print("="*80)
    print("AIRFLOW-STYLE PIPELINE ORCHESTRATION")
    print("Predictive Maintenance ML Workflow")
    print("="*80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Create context
    context = PipelineContext()
    
    # Define pipeline tasks
    tasks = [
        ("Data Collection", task_1_collect_data),
        ("Data Validation", task_2_validate_data),
        ("Model Training", task_3_train_models),
        ("Model Evaluation", task_4_evaluate_models),
        ("Model Deployment", task_5_deploy_model),
        ("Notification", task_6_notify),
    ]
    
    results = []
    
    for i, (task_name, task_func) in enumerate(tasks, 1):
        try:
            print(f"\n{'-'*40}")
            print(f"[{i}/{len(tasks)}] Executing: {task_name}")
            print(f"{'-'*40}")
            
            result = task_func(context)
            results.append((task_name, "SUCCESS", result))
            
        except Exception as e:
            print(f"\n[ERROR] Task '{task_name}' FAILED!")
            print(f"   Error: {str(e)}")
            results.append((task_name, "FAILED", str(e)))
            
            # Show partial results
            print(f"\n[WARNING] Pipeline stopped at task {i}/{len(tasks)}")
            return False
    
    # Success summary
    print("\n" + "="*80)
    print("PIPELINE EXECUTION SUMMARY")
    print("="*80)
    
    for task_name, status, _ in results:
        icon = "[OK]" if status == "SUCCESS" else "[ERROR]"
        print(f"{icon} {task_name}: {status}")
    
    print(f"\n[SUCCESS] All {len(tasks)} tasks completed successfully!")
    print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return True


if __name__ == "__main__":
    print("\n[START] Starting ML Pipeline Orchestration...\n")
    
    try:
        success = run_pipeline()
        
        if success:
            print("\n" + "="*80)
            print("NEXT STEPS:")
            print("="*80)
            print("1. Start API: python api_quickstart.py")
            print("2. Test predictions: http://localhost:8000/docs")
            print("3. View experiments: http://localhost:5000")
            print("4. Check results: pipeline_results.txt")
            print("\n[TIP] To install real Airflow:")
            print("   pip install apache-airflow")
            
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n\n[WARNING] Pipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n[ERROR] Pipeline failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
