"""
Airflow Quick Start - Run a single DAG task manually
Tests the Airflow pipeline without full Airflow installation
"""

import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("="*80)
print("AIRFLOW PIPELINE SIMULATION - Predictive Maintenance")
print("="*80)
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

# Import DAG tasks
from airflow.dags.predictive_maintenance_dag import (
    collect_sensor_data,
    validate_data_quality,
    train_models,
    evaluate_model_performance,
    deploy_model,
    send_notification
)


class MockTaskInstance:
    """Mock Airflow task instance for XCom"""
    def __init__(self):
        self.storage = {}
    
    def xcom_push(self, key, value):
        self.storage[key] = value
        print(f"   📤 XCom Push: {key} = {value}")
    
    def xcom_pull(self, task_ids, key):
        val = self.storage.get(key)
        print(f"   📥 XCom Pull: {key} = {val}")
        return val


def run_pipeline():
    """Execute the complete pipeline"""
    
    # Create mock context
    mock_ti = MockTaskInstance()
    context = {'task_instance': mock_ti}
    
    tasks = [
        ("1️⃣ Data Collection", collect_sensor_data),
        ("2️⃣ Data Validation", validate_data_quality),
        ("3️⃣ Model Training", train_models),
        ("4️⃣ Model Evaluation", evaluate_model_performance),
        ("5️⃣ Model Deployment", deploy_model),
        ("6️⃣ Notification", send_notification),
    ]
    
    results = []
    failed = False
    
    for i, (task_name, task_func) in enumerate(tasks, 1):
        try:
            print(f"\n{'='*80}")
            print(f"EXECUTING: {task_name}")
            print(f"{'='*80}\n")
            
            result = task_func(**context)
            results.append((task_name, "SUCCESS", result))
            
            print(f"\n✅ {task_name} completed successfully!")
            
        except Exception as e:
            print(f"\n❌ {task_name} failed!")
            print(f"Error: {str(e)}")
            results.append((task_name, "FAILED", str(e)))
            failed = True
            break
    
    # Final summary
    print("\n" + "="*80)
    print("PIPELINE EXECUTION SUMMARY")
    print("="*80)
    
    for task_name, status, result in results:
        status_icon = "✅" if status == "SUCCESS" else "❌"
        print(f"{status_icon} {task_name}: {status}")
    
    if not failed:
        print(f"\n🎉 Pipeline completed successfully!")
        print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"\n📊 Total tasks executed: {len(results)}/{len(tasks)}")
        return True
    else:
        print(f"\n⚠️ Pipeline failed at step {len(results)}")
        print(f"Failed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        return False


if __name__ == "__main__":
    print("\n🚀 Starting Airflow Pipeline Simulation...")
    print("   (Running DAG tasks sequentially without Airflow scheduler)\n")
    
    try:
        success = run_pipeline()
        
        if success:
            print("\n" + "="*80)
            print("NEXT STEPS:")
            print("="*80)
            print("1. Start FastAPI: python api_quickstart.py")
            print("2. Test predictions: http://localhost:8000/docs")
            print("3. View MLflow: http://localhost:5000")
            print("4. Install Airflow: pip install apache-airflow")
            print("5. Run with scheduler: airflow dags test predictive_maintenance_pipeline")
            
    except KeyboardInterrupt:
        print("\n\n⚠️ Pipeline interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Pipeline failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
