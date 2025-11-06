"""
Advanced Airflow Pipeline Simulator
Demonstrates: Branching, sensors, callbacks, conditional execution
"""

import sys
from pathlib import Path
from datetime import datetime
import json

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("="*100)
print("ADVANCED AIRFLOW PIPELINE ORCHESTRATION")
print("Demonstrates: Branching, Conditional Logic, Multi-Path Execution")
print("="*100)
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")


class PipelineContext:
    """Simulates Airflow XCom for data sharing"""
    def __init__(self):
        self.storage = {}
        self.execution_path = []
    
    def set(self, key, value):
        self.storage[key] = value
        print(f"      [XCom Push] {key} = {value}")
    
    def get(self, key, default=None):
        val = self.storage.get(key, default)
        print(f"      [XCom Pull] {key} = {val}")
        return val


def task_success_callback(task_name):
    """Simulates Airflow success callback"""
    print(f"      [Callback] {task_name} SUCCESS - Notification sent")


def task_failure_callback(task_name, error):
    """Simulates Airflow failure callback"""
    print(f"      [Callback] {task_name} FAILED - Alert sent: {error}")


def task_1_check_data(context):
    """Task 1: Check Data Availability"""
    print("\n" + "-"*100)
    print("[Task 1] CHECK DATA AVAILABILITY")
    print("-"*100)
    
    data_dir = project_root / "data/raw"
    historical_files = list(data_dir.glob("historical_*.json"))
    
    print(f"   Data directory: {data_dir}")
    print(f"   Historical files found: {len(historical_files)}")
    
    if len(historical_files) < 1:
        raise ValueError("Insufficient data files")
    
    context.set('data_files', len(historical_files))
    task_success_callback("check_data")
    
    return {"status": "success", "files": len(historical_files)}


def task_2_quality_gate(context):
    """Task 2: Data Quality Gate (BRANCHING DECISION)"""
    print("\n" + "-"*100)
    print("[Task 2] DATA QUALITY GATE (Branching Decision)")
    print("-"*100)
    
    data_dir = project_root / "data/raw"
    historical_files = sorted(data_dir.glob("historical_*.json"))
    
    with open(historical_files[-1], 'r') as f:
        data = json.load(f)
    
    sample_count = len(data)
    failure_rate = sum(1 for r in data if r['is_failing']) / len(data)
    
    print(f"   Sample count: {sample_count}")
    print(f"   Failure rate: {failure_rate:.2%}")
    print(f"   Quality thresholds: >= 1000 samples, 5-30% failure rate")
    
    # Decision logic
    high_quality = sample_count >= 1000 and 0.05 <= failure_rate <= 0.30
    
    if high_quality:
        print(f"\n   [DECISION] HIGH QUALITY DATA")
        print(f"   Branch: data_quality_passed -> train_all_models")
        context.set('quality_branch', 'high_quality')
        context.execution_path.append('high_quality_path')
        return 'train_all_models'
    else:
        print(f"\n   [DECISION] LOWER QUALITY DATA")
        print(f"   Branch: data_quality_failed -> train_baseline")
        context.set('quality_branch', 'low_quality')
        context.execution_path.append('low_quality_path')
        return 'train_baseline'


def task_3a_train_all_models(context):
    """Task 3a: Train All Models (High Quality Path)"""
    print("\n" + "-"*100)
    print("[Task 3a] TRAIN ALL MODELS (High Quality Path)")
    print("-"*100)
    
    import subprocess
    
    print("   Executing: mlflow_advanced.py")
    print("   Training: 5 models (RF baseline, RF tuned, GB baseline, GB tuned, LR)")
    
    result = subprocess.run(
        [sys.executable, str(project_root / "mlflow_advanced.py")],
        capture_output=True,
        text=True,
        timeout=600
    )
    
    if result.returncode != 0:
        error = f"Training failed: {result.stderr[:200]}"
        task_failure_callback("train_all_models", error)
        raise Exception(error)
    
    print("   [OK] All 5 models trained successfully")
    context.set('models_trained', 5)
    task_success_callback("train_all_models")
    
    return {"status": "success", "models": 5}


def task_3b_train_baseline(context):
    """Task 3b: Train Baseline Model (Low Quality Path)"""
    print("\n" + "-"*100)
    print("[Task 3b] TRAIN BASELINE MODEL (Low Quality Path)")
    print("-"*100)
    
    import mlflow
    import numpy as np
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score
    
    print("   Quick baseline training (simplified pipeline)")
    
    # Load data
    data_dir = project_root / "data/raw"
    historical_files = sorted(data_dir.glob("historical_*.json"))
    
    with open(historical_files[-1], 'r') as f:
        data = json.load(f)
    
    # Extract features
    X = np.array([[
        record['sensors']['temperature']['value'],
        record['sensors']['vibration']['value'],
        record['sensors']['pressure']['value'],
        record['sensors']['current']['value'],
        record['sensors']['rpm']['value']
    ] for record in data])
    
    y = np.array([record['is_failing'] for record in data])
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    # Train
    mlflow_dir = (project_root / 'mlruns').resolve()
    mlflow.set_tracking_uri(f"file:///{mlflow_dir.as_posix()}")
    mlflow.set_experiment("predictive_maintenance")
    
    with mlflow.start_run(run_name="baseline_quick"):
        model = RandomForestClassifier(n_estimators=50, random_state=42)
        model.fit(X_train, y_train)
        
        accuracy = accuracy_score(y_test, model.predict(X_test))
        mlflow.log_metric("test_accuracy", float(accuracy))
        mlflow.sklearn.log_model(model, "model")
    
    print(f"   [OK] Baseline model trained: {accuracy:.4f} accuracy")
    context.set('models_trained', 1)
    task_success_callback("train_baseline")
    
    return {"status": "success", "models": 1}


def task_4_validate_model(context):
    """Task 4: Validate Model Performance"""
    print("\n" + "-"*100)
    print("[Task 4] VALIDATE MODEL PERFORMANCE")
    print("-"*100)
    
    import mlflow
    
    mlflow_dir = (project_root / 'mlruns').resolve()
    mlflow.set_tracking_uri(f"file:///{mlflow_dir.as_posix()}")
    
    client = mlflow.tracking.MlflowClient()
    experiment = client.get_experiment_by_name("predictive_maintenance")
    
    # Get best run
    runs = client.search_runs(
        experiment_ids=[experiment.experiment_id],
        order_by=["metrics.test_accuracy DESC"],
        max_results=1
    )
    
    if not runs:
        raise ValueError("No models found for validation")
    
    best_accuracy = runs[0].data.metrics.get('test_accuracy', 0)
    min_required = 0.90
    
    print(f"   Best model accuracy: {best_accuracy:.4f}")
    print(f"   Minimum required: {min_required:.4f}")
    
    if best_accuracy < min_required:
        error = f"Performance too low: {best_accuracy:.4f} < {min_required}"
        task_failure_callback("validate_model", error)
        raise ValueError(error)
    
    print(f"   [OK] Validation PASSED")
    context.set('best_accuracy', best_accuracy)
    task_success_callback("validate_model")
    
    return {"status": "success", "accuracy": best_accuracy}


def task_5_deploy_staging(context):
    """Task 5: Deploy to Staging"""
    print("\n" + "-"*100)
    print("[Task 5] DEPLOY TO STAGING ENVIRONMENT")
    print("-"*100)
    
    import mlflow
    import joblib
    
    mlflow_dir = (project_root / 'mlruns').resolve()
    mlflow.set_tracking_uri(f"file:///{mlflow_dir.as_posix()}")
    
    client = mlflow.tracking.MlflowClient()
    experiment = client.get_experiment_by_name("predictive_maintenance")
    
    # Get best model
    runs = client.search_runs(
        experiment_ids=[experiment.experiment_id],
        order_by=["metrics.test_accuracy DESC"],
        max_results=1
    )
    
    best_run = runs[0]
    model_uri = f"runs:/{best_run.info.run_id}/model"
    model = mlflow.sklearn.load_model(model_uri)
    
    # Save to staging
    staging_path = project_root / "models/staging_model.pkl"
    staging_path.parent.mkdir(exist_ok=True)
    joblib.dump(model, staging_path)
    
    # Metadata
    metadata = {
        "model_id": best_run.info.run_id,
        "deployed_at": datetime.now().isoformat(),
        "environment": "staging",
        "accuracy": best_run.data.metrics.get('test_accuracy', 0)
    }
    
    metadata_path = project_root / "models/staging_metadata.json"
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"   Model deployed: {staging_path.name}")
    print(f"   Metadata saved: {metadata_path.name}")
    context.set('staging_path', str(staging_path))
    task_success_callback("deploy_staging")
    
    return {"status": "success"}


def task_6_performance_decision(context):
    """Task 6: Performance-Based Branching"""
    print("\n" + "-"*100)
    print("[Task 6] PERFORMANCE DECISION (Conditional Branching)")
    print("-"*100)
    
    best_accuracy = context.get('best_accuracy')
    excellent_threshold = 0.95
    
    print(f"   Model accuracy: {best_accuracy:.4f}")
    print(f"   Excellence threshold: {excellent_threshold:.4f}")
    
    if best_accuracy >= excellent_threshold:
        print(f"\n   [DECISION] EXCELLENT PERFORMANCE")
        print(f"   Branch: deploy_production (automatic deployment)")
        context.execution_path.append('auto_production_path')
        return 'deploy_production'
    else:
        print(f"\n   [DECISION] ACCEPTABLE PERFORMANCE")
        print(f"   Branch: hold_for_review (manual approval required)")
        context.execution_path.append('manual_review_path')
        return 'hold_for_review'


def task_7a_deploy_production(context):
    """Task 7a: Deploy to Production (High Performance Path)"""
    print("\n" + "-"*100)
    print("[Task 7a] DEPLOY TO PRODUCTION (Automatic)")
    print("-"*100)
    
    import shutil
    
    staging_path = project_root / "models/staging_model.pkl"
    production_path = project_root / "models/production_model.pkl"
    
    shutil.copy2(staging_path, production_path)
    
    # Update metadata
    staging_metadata_path = project_root / "models/staging_metadata.json"
    with open(staging_metadata_path, 'r') as f:
        metadata = json.load(f)
    
    metadata['environment'] = 'production'
    metadata['promoted_at'] = datetime.now().isoformat()
    metadata['deployment_type'] = 'automatic'
    
    production_metadata_path = project_root / "models/production_metadata.json"
    with open(production_metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"   [OK] Model promoted to PRODUCTION")
    print(f"   Path: {production_path.name}")
    context.set('production_deployed', True)
    task_success_callback("deploy_production")
    
    return {"status": "success"}


def task_7b_hold_for_review(context):
    """Task 7b: Hold for Manual Review (Acceptable Performance Path)"""
    print("\n" + "-"*100)
    print("[Task 7b] HOLD FOR MANUAL REVIEW")
    print("-"*100)
    
    best_accuracy = context.get('best_accuracy')
    
    review_data = {
        "status": "pending_review",
        "accuracy": best_accuracy,
        "flagged_at": datetime.now().isoformat(),
        "reason": "Performance between 0.90 and 0.95 - requires manual approval",
        "action_required": "Review model and approve for production deployment"
    }
    
    review_path = project_root / "models/review_required.json"
    with open(review_path, 'w') as f:
        json.dump(review_data, f, indent=2)
    
    print(f"   [REVIEW] Manual approval required")
    print(f"   Accuracy: {best_accuracy:.4f}")
    print(f"   Review file: {review_path.name}")
    context.set('production_deployed', False)
    
    return {"status": "pending_review"}


def task_8_generate_report(context):
    """Task 8: Generate Pipeline Report"""
    print("\n" + "-"*100)
    print("[Task 8] GENERATE PIPELINE REPORT")
    print("-"*100)
    
    # Gather metrics
    data_files = context.get('data_files')
    models_trained = context.get('models_trained')
    best_accuracy = context.get('best_accuracy')
    production_deployed = context.get('production_deployed', False)
    
    report = {
        "pipeline_name": "predictive_maintenance_advanced",
        "execution_date": datetime.now().isoformat(),
        "execution_path": context.execution_path,
        "metrics": {
            "data_files_processed": data_files,
            "models_trained": models_trained,
            "best_model_accuracy": best_accuracy,
            "production_deployed": production_deployed
        },
        "branching_decisions": {
            "quality_gate": context.get('quality_branch'),
            "performance_gate": 'auto_deploy' if production_deployed else 'manual_review'
        },
        "status": "success",
        "completed_at": datetime.now().isoformat()
    }
    
    report_path = project_root / "airflow_advanced_report.json"
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"   Report saved: {report_path.name}")
    task_success_callback("generate_report")
    
    return report


def task_9_cleanup(context):
    """Task 9: Cleanup Temporary Files"""
    print("\n" + "-"*100)
    print("[Task 9] CLEANUP TEMPORARY FILES")
    print("-"*100)
    
    temp_files = list(project_root.glob("temp_*.png"))
    cleaned = 0
    
    for file in temp_files:
        try:
            file.unlink()
            cleaned += 1
        except Exception as e:
            print(f"   Warning: Could not delete {file.name}: {e}")
    
    print(f"   Cleaned up {cleaned} temporary files")
    
    return {"status": "success", "cleaned": cleaned}


def run_advanced_pipeline():
    """Execute pipeline with branching logic"""
    
    context = PipelineContext()
    results = []
    
    try:
        # Task 1: Check Data
        print("\n" + "="*100)
        print("PIPELINE EXECUTION START")
        print("="*100)
        result = task_1_check_data(context)
        results.append(("Task 1: Check Data", "SUCCESS", result))
        
        # Task 2: Quality Gate (Branching)
        branch = task_2_quality_gate(context)
        results.append(("Task 2: Quality Gate", "SUCCESS", {"branch": branch}))
        
        # Task 3: Training (Conditional)
        if branch == 'train_all_models':
            result = task_3a_train_all_models(context)
            results.append(("Task 3a: Train All Models", "SUCCESS", result))
        else:
            result = task_3b_train_baseline(context)
            results.append(("Task 3b: Train Baseline", "SUCCESS", result))
        
        # Task 4: Validate
        result = task_4_validate_model(context)
        results.append(("Task 4: Validate Model", "SUCCESS", result))
        
        # Task 5: Deploy Staging
        result = task_5_deploy_staging(context)
        results.append(("Task 5: Deploy Staging", "SUCCESS", result))
        
        # Task 6: Performance Decision (Branching)
        branch = task_6_performance_decision(context)
        results.append(("Task 6: Performance Decision", "SUCCESS", {"branch": branch}))
        
        # Task 7: Deployment (Conditional)
        if branch == 'deploy_production':
            result = task_7a_deploy_production(context)
            results.append(("Task 7a: Deploy Production", "SUCCESS", result))
        else:
            result = task_7b_hold_for_review(context)
            results.append(("Task 7b: Hold for Review", "SUCCESS", result))
        
        # Task 8: Generate Report
        report = task_8_generate_report(context)
        results.append(("Task 8: Generate Report", "SUCCESS", report))
        
        # Task 9: Cleanup
        result = task_9_cleanup(context)
        results.append(("Task 9: Cleanup", "SUCCESS", result))
        
    except Exception as e:
        print(f"\n[ERROR] Pipeline failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, results
    
    # Final Summary
    print("\n" + "="*100)
    print("PIPELINE EXECUTION SUMMARY")
    print("="*100)
    
    for task_name, status, result in results:
        print(f"[OK] {task_name}: {status}")
    
    print(f"\n[SUCCESS] Pipeline completed successfully!")
    print(f"Execution Path: {' -> '.join(context.execution_path)}")
    print(f"Total Tasks: {len(results)}")
    print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Display branching visualization
    print("\n" + "="*100)
    print("BRANCHING VISUALIZATION")
    print("="*100)
    print("""
    START
      |
      v
    [Check Data]
      |
      v
    [Quality Gate] ----+
      |                |
      v                v
    HIGH QUALITY    LOW QUALITY
      |                |
      v                v
    [Train All]    [Train Baseline]
      |                |
      +--------+-------+
               v
          [Validate]
               |
               v
          [Deploy Staging]
               |
               v
       [Performance Decision] ----+
               |                  |
               v                  v
          EXCELLENT           ACCEPTABLE
               |                  |
               v                  v
       [Deploy Production]  [Hold for Review]
               |                  |
               +--------+---------+
                        v
                  [Generate Report]
                        |
                        v
                    [Cleanup]
                        |
                        v
                      END
    """)
    
    print("\n" + "="*100)
    print("NEXT STEPS")
    print("="*100)
    print("1. Review report: airflow_advanced_report.json")
    print("2. Check staging model: models/staging_model.pkl")
    if context.get('production_deployed'):
        print("3. Production model deployed: models/production_model.pkl")
    else:
        print("3. Manual review required: models/review_required.json")
    print("4. Install Apache Airflow: pip install apache-airflow")
    print("5. Run real DAG: airflow dags test predictive_maintenance_advanced")
    
    return True, results


if __name__ == "__main__":
    print("\n[START] Launching Advanced Airflow Pipeline Simulator...\n")
    
    try:
        success, results = run_advanced_pipeline()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] Pipeline stopped by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n[ERROR] Pipeline failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
