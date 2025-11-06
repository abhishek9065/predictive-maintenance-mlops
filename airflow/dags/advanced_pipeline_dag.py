"""
Advanced Airflow DAG - Predictive Maintenance Pipeline
Features: Task dependencies, branching, sensors, callbacks, monitoring
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.operators.bash import BashOperator
from airflow.sensors.filesystem import FileSensor
from airflow.operators.dummy import DummyOperator
from airflow.utils.trigger_rule import TriggerRule
from pathlib import Path
import json
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Project root
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Default arguments
default_args = {
    'owner': 'mlops_team',
    'depends_on_past': False,
    'start_date': datetime(2025, 11, 1),
    'email': ['mlops@example.com'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'execution_timeout': timedelta(minutes=30),
}

# Create DAG
dag = DAG(
    'predictive_maintenance_advanced',
    default_args=default_args,
    description='Advanced ML pipeline with branching, sensors, and monitoring',
    schedule_interval='0 2 * * *',  # Daily at 2 AM
    catchup=False,
    max_active_runs=1,
    tags=['ml', 'production', 'predictive-maintenance'],
)


# Callback Functions
def task_success_callback(context):
    """Called when a task succeeds"""
    task_id = context['task_instance'].task_id
    logger.info(f"[SUCCESS] Task {task_id} completed successfully")
    # Could send Slack notification, update dashboard, etc.


def task_failure_callback(context):
    """Called when a task fails"""
    task_id = context['task_instance'].task_id
    exception = context.get('exception')
    logger.error(f"[FAILURE] Task {task_id} failed: {exception}")
    # Could send alert to PagerDuty, Slack, etc.


def dag_success_callback(context):
    """Called when entire DAG succeeds"""
    logger.info("[SUCCESS] Entire pipeline completed successfully!")
    # Send summary report, update production status, etc.


# Task 1: Check Data Availability (Sensor)
def check_data_files(**context):
    """Verify minimum data requirements"""
    data_dir = PROJECT_ROOT / "data/raw"
    historical_files = list(data_dir.glob("historical_*.json"))
    
    min_required = 1
    if len(historical_files) < min_required:
        raise ValueError(f"Insufficient data: {len(historical_files)}/{min_required} files")
    
    # Push to XCom
    context['task_instance'].xcom_push(key='data_files', value=len(historical_files))
    logger.info(f"Data check passed: {len(historical_files)} files found")
    return True


# Task 2: Data Quality Gate (Branch Decision)
def evaluate_data_quality(**context):
    """Decide whether to proceed based on data quality"""
    import numpy as np
    
    data_dir = PROJECT_ROOT / "data/raw"
    historical_files = sorted(data_dir.glob("historical_*.json"))
    
    with open(historical_files[-1], 'r') as f:
        data = json.load(f)
    
    # Quality checks
    sample_count = len(data)
    failure_rate = sum(1 for r in data if r['is_failing']) / len(data)
    
    # Decision criteria
    if sample_count >= 1000 and 0.05 <= failure_rate <= 0.30:
        logger.info(f"Quality PASSED: {sample_count} samples, {failure_rate:.2%} failure rate")
        return 'data_quality_passed'
    else:
        logger.warning(f"Quality FAILED: {sample_count} samples, {failure_rate:.2%} failure rate")
        return 'data_quality_failed'


# Task 3a: High Quality Path - Full Training
def train_all_models(**context):
    """Train comprehensive model suite (high quality data)"""
    import subprocess
    import sys
    
    logger.info("High quality data - training all models")
    
    result = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "mlflow_advanced.py")],
        capture_output=True,
        text=True,
        timeout=600
    )
    
    if result.returncode != 0:
        raise Exception(f"Training failed: {result.stderr}")
    
    logger.info("All models trained successfully")
    context['task_instance'].xcom_push(key='models_trained', value=5)


# Task 3b: Low Quality Path - Quick Baseline
def train_baseline_model(**context):
    """Train only baseline model (lower quality data)"""
    import mlflow
    import numpy as np
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score
    
    logger.info("Lower quality data - training baseline model only")
    
    # Load data
    data_dir = PROJECT_ROOT / "data/raw"
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
    
    # Train baseline
    mlflow_dir = (PROJECT_ROOT / 'mlruns').resolve()
    mlflow.set_tracking_uri(f"file:///{mlflow_dir.as_posix()}")
    mlflow.set_experiment("predictive_maintenance")
    
    with mlflow.start_run(run_name="baseline_quick"):
        model = RandomForestClassifier(n_estimators=50, random_state=42)
        model.fit(X_train, y_train)
        
        accuracy = accuracy_score(y_test, model.predict(X_test))
        mlflow.log_metric("test_accuracy", float(accuracy))
        mlflow.sklearn.log_model(model, "model")
    
    logger.info(f"Baseline model trained: {accuracy:.4f} accuracy")
    context['task_instance'].xcom_push(key='models_trained', value=1)


# Task 4: Model Validation
def validate_model_performance(**context):
    """Validate that best model meets minimum requirements"""
    import mlflow
    
    mlflow_dir = (PROJECT_ROOT / 'mlruns').resolve()
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
    min_required_accuracy = 0.90
    
    if best_accuracy < min_required_accuracy:
        raise ValueError(
            f"Model performance too low: {best_accuracy:.4f} < {min_required_accuracy}"
        )
    
    logger.info(f"Model validation PASSED: {best_accuracy:.4f} accuracy")
    context['task_instance'].xcom_push(key='best_accuracy', value=best_accuracy)
    
    return best_accuracy >= 0.95  # True if excellent, False if acceptable


# Task 5: Deploy to Staging
def deploy_to_staging(**context):
    """Deploy model to staging environment"""
    import mlflow
    import joblib
    
    logger.info("Deploying to STAGING environment")
    
    mlflow_dir = (PROJECT_ROOT / 'mlruns').resolve()
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
    staging_path = PROJECT_ROOT / "models/staging_model.pkl"
    staging_path.parent.mkdir(exist_ok=True)
    joblib.dump(model, staging_path)
    
    # Metadata
    metadata = {
        "model_id": best_run.info.run_id,
        "deployed_at": datetime.now().isoformat(),
        "environment": "staging",
        "accuracy": best_run.data.metrics.get('test_accuracy', 0)
    }
    
    metadata_path = PROJECT_ROOT / "models/staging_metadata.json"
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    logger.info(f"Model deployed to staging: {staging_path}")
    context['task_instance'].xcom_push(key='staging_path', value=str(staging_path))


# Task 6a: Deploy to Production (High Performance)
def deploy_to_production(**context):
    """Deploy model to production environment"""
    import mlflow
    import joblib
    import shutil
    
    logger.info("Deploying to PRODUCTION environment")
    
    # Copy from staging to production
    staging_path = PROJECT_ROOT / "models/staging_model.pkl"
    production_path = PROJECT_ROOT / "models/production_model.pkl"
    
    shutil.copy2(staging_path, production_path)
    
    # Update metadata
    staging_metadata_path = PROJECT_ROOT / "models/staging_metadata.json"
    with open(staging_metadata_path, 'r') as f:
        metadata = json.load(f)
    
    metadata['environment'] = 'production'
    metadata['promoted_at'] = datetime.now().isoformat()
    
    production_metadata_path = PROJECT_ROOT / "models/production_metadata.json"
    with open(production_metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    logger.info(f"Model promoted to production: {production_path}")
    context['task_instance'].xcom_push(key='production_path', value=str(production_path))


# Task 6b: Hold for Review (Acceptable Performance)
def hold_for_manual_review(**context):
    """Flag model for manual review before production deployment"""
    logger.info("Model performance acceptable but not excellent - MANUAL REVIEW REQUIRED")
    
    best_accuracy = context['task_instance'].xcom_pull(
        task_ids='validate_model',
        key='best_accuracy'
    )
    
    review_data = {
        "status": "pending_review",
        "accuracy": best_accuracy,
        "flagged_at": datetime.now().isoformat(),
        "reason": "Performance between 0.90 and 0.95 - requires review"
    }
    
    review_path = PROJECT_ROOT / "models/review_required.json"
    with open(review_path, 'w') as f:
        json.dump(review_data, f, indent=2)
    
    logger.info(f"Review request created: {review_path}")


# Task 7: Generate Report
def generate_pipeline_report(**context):
    """Generate comprehensive pipeline execution report"""
    
    # Gather metrics from XCom
    data_files = context['task_instance'].xcom_pull(
        task_ids='check_data',
        key='data_files'
    )
    
    models_trained = context['task_instance'].xcom_pull(
        task_ids=['train_all_models', 'train_baseline'],
        key='models_trained'
    )
    models_trained = max([m for m in models_trained if m is not None], default=0)
    
    best_accuracy = context['task_instance'].xcom_pull(
        task_ids='validate_model',
        key='best_accuracy'
    )
    
    # Create report
    report = {
        "pipeline_name": "predictive_maintenance_advanced",
        "execution_date": context['execution_date'].isoformat(),
        "dag_run_id": context['dag_run'].run_id,
        "metrics": {
            "data_files_processed": data_files,
            "models_trained": models_trained,
            "best_model_accuracy": best_accuracy,
        },
        "status": "success",
        "completed_at": datetime.now().isoformat()
    }
    
    report_path = PROJECT_ROOT / "airflow_pipeline_report.json"
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Pipeline report generated: {report_path}")
    
    print("\n" + "="*80)
    print("PIPELINE EXECUTION REPORT")
    print("="*80)
    print(f"Data Files: {data_files}")
    print(f"Models Trained: {models_trained}")
    print(f"Best Accuracy: {best_accuracy:.4f}")
    print(f"Status: SUCCESS")
    print("="*80)


# Task 8: Cleanup
def cleanup_temporary_files(**context):
    """Clean up temporary files and artifacts"""
    import shutil
    
    logger.info("Cleaning up temporary files")
    
    # Clean up temp files
    temp_patterns = ['temp_*.png', '*.tmp', '.cache/*']
    cleaned = 0
    
    for pattern in temp_patterns:
        for file in PROJECT_ROOT.glob(pattern):
            try:
                if file.is_file():
                    file.unlink()
                    cleaned += 1
            except Exception as e:
                logger.warning(f"Could not delete {file}: {e}")
    
    logger.info(f"Cleaned up {cleaned} temporary files")


# Define Tasks
start = DummyOperator(
    task_id='start',
    dag=dag,
)

check_data = PythonOperator(
    task_id='check_data',
    python_callable=check_data_files,
    on_success_callback=task_success_callback,
    on_failure_callback=task_failure_callback,
    dag=dag,
)

quality_gate = BranchPythonOperator(
    task_id='quality_gate',
    python_callable=evaluate_data_quality,
    dag=dag,
)

quality_passed = DummyOperator(
    task_id='data_quality_passed',
    dag=dag,
)

quality_failed = DummyOperator(
    task_id='data_quality_failed',
    dag=dag,
)

train_all = PythonOperator(
    task_id='train_all_models',
    python_callable=train_all_models,
    on_success_callback=task_success_callback,
    dag=dag,
)

train_baseline = PythonOperator(
    task_id='train_baseline',
    python_callable=train_baseline_model,
    on_success_callback=task_success_callback,
    dag=dag,
)

# Convergence point - both paths lead here
training_complete = DummyOperator(
    task_id='training_complete',
    trigger_rule=TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS,
    dag=dag,
)

validate_model = PythonOperator(
    task_id='validate_model',
    python_callable=validate_model_performance,
    dag=dag,
)

deploy_staging = PythonOperator(
    task_id='deploy_staging',
    python_callable=deploy_to_staging,
    on_success_callback=task_success_callback,
    dag=dag,
)

# Branch based on model performance
performance_decision = BranchPythonOperator(
    task_id='performance_decision',
    python_callable=lambda **context: (
        'deploy_production' 
        if context['task_instance'].xcom_pull(task_ids='validate_model', key='best_accuracy') >= 0.95
        else 'hold_for_review'
    ),
    dag=dag,
)

deploy_prod = PythonOperator(
    task_id='deploy_production',
    python_callable=deploy_to_production,
    on_success_callback=task_success_callback,
    dag=dag,
)

hold_review = PythonOperator(
    task_id='hold_for_review',
    python_callable=hold_for_manual_review,
    dag=dag,
)

# Convergence for final tasks
deployment_complete = DummyOperator(
    task_id='deployment_complete',
    trigger_rule=TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS,
    dag=dag,
)

generate_report = PythonOperator(
    task_id='generate_report',
    python_callable=generate_pipeline_report,
    trigger_rule=TriggerRule.ALL_DONE,
    dag=dag,
)

cleanup = PythonOperator(
    task_id='cleanup',
    python_callable=cleanup_temporary_files,
    trigger_rule=TriggerRule.ALL_DONE,
    dag=dag,
)

end = DummyOperator(
    task_id='end',
    trigger_rule=TriggerRule.ALL_DONE,
    on_success_callback=dag_success_callback,
    dag=dag,
)

# Define Dependencies
start >> check_data >> quality_gate

# Quality gate branches
quality_gate >> quality_passed >> train_all >> training_complete
quality_gate >> quality_failed >> train_baseline >> training_complete

# Main pipeline flow
training_complete >> validate_model >> deploy_staging >> performance_decision

# Performance decision branches
performance_decision >> deploy_prod >> deployment_complete
performance_decision >> hold_review >> deployment_complete

# Final tasks
deployment_complete >> generate_report >> cleanup >> end
