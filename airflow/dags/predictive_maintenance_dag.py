"""
Apache Airflow DAG - Predictive Maintenance Pipeline
Orchestrates the complete ML workflow: Data Collection -> Training -> Deployment
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from pathlib import Path
import json

# Default arguments for the DAG
default_args = {
    'owner': 'mlops_team',
    'depends_on_past': False,
    'start_date': datetime(2025, 11, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Create DAG
dag = DAG(
    'predictive_maintenance_pipeline',
    default_args=default_args,
    description='End-to-end ML pipeline for predictive maintenance',
    schedule_interval='@daily',  # Run daily
    catchup=False,
    tags=['ml', 'predictive-maintenance', 'mlops'],
)


def collect_sensor_data(**context):
    """Task 1: Collect sensor data from IoT devices"""
    import sys
    from pathlib import Path
    import subprocess
    
    project_root = Path(__file__).parent.parent.parent
    
    print("="*80)
    print("TASK 1: Data Collection")
    print("="*80)
    
    # Run IoT simulator (generate small batch for demo)
    result = subprocess.run(
        [sys.executable, str(project_root / "src/data_collection/iot_simulator.py"), "--samples", "1000"],
        capture_output=True,
        text=True,
        timeout=60
    )
    
    if result.returncode == 0:
        print("✅ Data collection completed successfully")
        print(result.stdout[-500:])  # Last 500 chars
        
        # Count data files
        data_dir = project_root / "data/raw"
        files = list(data_dir.glob("*.json"))
        
        context['task_instance'].xcom_push(key='data_files_count', value=len(files))
        return {"status": "success", "files": len(files)}
    else:
        print("❌ Data collection failed")
        print(result.stderr)
        raise Exception("Data collection failed")


def validate_data_quality(**context):
    """Task 2: Validate data quality"""
    from pathlib import Path
    import json
    import numpy as np
    
    project_root = Path(__file__).parent.parent.parent
    data_dir = project_root / "data/raw"
    
    print("="*80)
    print("TASK 2: Data Quality Validation")
    print("="*80)
    
    # Load latest historical data
    historical_files = sorted(data_dir.glob("historical_*.json"))
    
    if not historical_files:
        raise Exception("No historical data files found")
    
    with open(historical_files[-1], 'r') as f:
        data = json.load(f)
    
    print(f"📊 Loaded {len(data)} records")
    
    # Quality checks
    checks_passed = 0
    checks_total = 0
    
    # Check 1: Minimum sample size
    checks_total += 1
    if len(data) >= 100:
        print("✅ Check 1: Sample size >= 100")
        checks_passed += 1
    else:
        print(f"❌ Check 1: Sample size too small ({len(data)})")
    
    # Check 2: Required fields
    checks_total += 1
    required_fields = ['equipment_id', 'timestamp', 'sensors', 'is_failing']
    if all(field in data[0] for field in required_fields):
        print("✅ Check 2: All required fields present")
        checks_passed += 1
    else:
        print("❌ Check 2: Missing required fields")
    
    # Check 3: Sensor data completeness
    checks_total += 1
    required_sensors = ['temperature', 'vibration', 'pressure', 'current', 'rpm']
    if all(sensor in data[0]['sensors'] for sensor in required_sensors):
        print("✅ Check 3: All sensors present")
        checks_passed += 1
    else:
        print("❌ Check 3: Missing sensor data")
    
    # Check 4: Class balance
    checks_total += 1
    failure_rate = sum(1 for r in data if r['is_failing']) / len(data)
    if 0.05 <= failure_rate <= 0.30:
        print(f"✅ Check 4: Class balance OK ({failure_rate:.2%} failures)")
        checks_passed += 1
    else:
        print(f"⚠️ Check 4: Unusual class balance ({failure_rate:.2%} failures)")
    
    print(f"\n📊 Quality Score: {checks_passed}/{checks_total} checks passed")
    
    context['task_instance'].xcom_push(key='quality_score', value=checks_passed/checks_total)
    
    if checks_passed < checks_total * 0.75:  # Require 75% pass rate
        raise Exception(f"Data quality too low: {checks_passed}/{checks_total}")
    
    return {"status": "success", "score": checks_passed/checks_total}


def train_models(**context):
    """Task 3: Train ML models"""
    import sys
    from pathlib import Path
    import subprocess
    
    project_root = Path(__file__).parent.parent.parent
    
    print("="*80)
    print("TASK 3: Model Training")
    print("="*80)
    
    # Run MLflow training
    result = subprocess.run(
        [sys.executable, str(project_root / "mlflow_quickstart.py")],
        capture_output=True,
        text=True,
        timeout=300  # 5 minute timeout
    )
    
    if "✅ MLflow experiment tracking complete!" in result.stdout:
        print("✅ Model training completed successfully")
        
        # Extract run IDs from output
        lines = result.stdout.split('\n')
        run_ids = [line.split(': ')[1] for line in lines if 'Run ID:' in line]
        
        print(f"📊 Trained {len(run_ids)} models")
        
        context['task_instance'].xcom_push(key='model_run_ids', value=run_ids)
        return {"status": "success", "models": len(run_ids)}
    else:
        print("❌ Model training failed")
        print(result.stderr)
        raise Exception("Model training failed")


def evaluate_model_performance(**context):
    """Task 4: Evaluate and select best model"""
    import mlflow
    from pathlib import Path
    
    project_root = Path(__file__).parent.parent.parent
    mlflow.set_tracking_uri(f"file://{project_root / 'mlruns'}")
    
    print("="*80)
    print("TASK 4: Model Evaluation")
    print("="*80)
    
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
    
    print(f"📊 Found {len(runs)} model runs")
    
    # Display top models
    print("\n🏆 Top Models:")
    for i, run in enumerate(runs[:3], 1):
        metrics = run.data.metrics
        params = run.data.params
        print(f"\n  {i}. Run ID: {run.info.run_id[:8]}...")
        print(f"     Model: {params.get('model_type', 'Unknown')}")
        print(f"     Accuracy: {metrics.get('accuracy', 0):.4f}")
        print(f"     F1 Score: {metrics.get('f1_score', 0):.4f}")
    
    # Select best model
    best_run = runs[0]
    best_run_id = best_run.info.run_id
    best_accuracy = best_run.data.metrics.get('accuracy', 0)
    
    print(f"\n✅ Best Model Selected: {best_run_id[:8]}... (Accuracy: {best_accuracy:.4f})")
    
    context['task_instance'].xcom_push(key='best_model_id', value=best_run_id)
    context['task_instance'].xcom_push(key='best_accuracy', value=best_accuracy)
    
    return {"status": "success", "best_model": best_run_id, "accuracy": best_accuracy}


def deploy_model(**context):
    """Task 5: Deploy best model"""
    import mlflow
    import joblib
    from pathlib import Path
    
    project_root = Path(__file__).parent.parent.parent
    mlflow.set_tracking_uri(f"file://{project_root / 'mlruns'}")
    
    print("="*80)
    print("TASK 5: Model Deployment")
    print("="*80)
    
    # Get best model ID from previous task
    best_model_id = context['task_instance'].xcom_pull(
        task_ids='evaluate_model', 
        key='best_model_id'
    )
    
    if not best_model_id:
        raise Exception("No best model ID found")
    
    print(f"📦 Deploying model: {best_model_id[:8]}...")
    
    # Load model from MLflow
    model_uri = f"runs:/{best_model_id}/model"
    model = mlflow.sklearn.load_model(model_uri)
    
    # Save to production location
    production_path = project_root / "models/production_model.pkl"
    production_path.parent.mkdir(exist_ok=True)
    joblib.dump(model, production_path)
    
    print(f"✅ Model deployed to: {production_path}")
    
    # Create deployment metadata
    metadata = {
        "model_id": best_model_id,
        "deployed_at": datetime.now().isoformat(),
        "accuracy": context['task_instance'].xcom_pull(
            task_ids='evaluate_model',
            key='best_accuracy'
        ),
        "deployment_path": str(production_path)
    }
    
    metadata_path = project_root / "models/deployment_metadata.json"
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"✅ Metadata saved to: {metadata_path}")
    
    return {"status": "success", "model_path": str(production_path)}


def send_notification(**context):
    """Task 6: Send pipeline completion notification"""
    print("="*80)
    print("TASK 6: Pipeline Notification")
    print("="*80)
    
    # Get metrics from previous tasks
    data_files = context['task_instance'].xcom_pull(
        task_ids='collect_data',
        key='data_files_count'
    )
    
    quality_score = context['task_instance'].xcom_pull(
        task_ids='validate_data',
        key='quality_score'
    )
    
    best_accuracy = context['task_instance'].xcom_pull(
        task_ids='evaluate_model',
        key='best_accuracy'
    )
    
    # Create summary
    summary = f"""
    ╔════════════════════════════════════════════════════════╗
    ║   PREDICTIVE MAINTENANCE PIPELINE - COMPLETED         ║
    ╚════════════════════════════════════════════════════════╝
    
    📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    
    📊 Pipeline Results:
       • Data Files Collected: {data_files or 'N/A'}
       • Data Quality Score: {quality_score:.2%}
       • Best Model Accuracy: {best_accuracy:.4f}
       • Status: SUCCESS ✅
    
    🚀 Model deployed and ready for predictions!
    
    Next: Access API at http://localhost:8000/docs
    """
    
    print(summary)
    
    # In production, this would send email/Slack notification
    return {"status": "success", "summary": summary}


# Define task dependencies
task_1_collect = PythonOperator(
    task_id='collect_data',
    python_callable=collect_sensor_data,
    dag=dag,
)

task_2_validate = PythonOperator(
    task_id='validate_data',
    python_callable=validate_data_quality,
    dag=dag,
)

task_3_train = PythonOperator(
    task_id='train_models',
    python_callable=train_models,
    dag=dag,
)

task_4_evaluate = PythonOperator(
    task_id='evaluate_model',
    python_callable=evaluate_model_performance,
    dag=dag,
)

task_5_deploy = PythonOperator(
    task_id='deploy_model',
    python_callable=deploy_model,
    dag=dag,
)

task_6_notify = PythonOperator(
    task_id='send_notification',
    python_callable=send_notification,
    dag=dag,
)

# Set task dependencies (linear pipeline)
task_1_collect >> task_2_validate >> task_3_train >> task_4_evaluate >> task_5_deploy >> task_6_notify
