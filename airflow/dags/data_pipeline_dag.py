"""
Airflow DAG for Data Pipeline
Orchestrates data collection, ingestion, and storage.
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator

# Default arguments
default_args = {
    'owner': 'mlops-team',
    'depends_on_past': False,
    'start_date': datetime(2025, 1, 1),
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

# Define DAG
dag = DAG(
    'data_pipeline',
    default_args=default_args,
    description='Automated data collection and processing pipeline',
    schedule_interval='@hourly',  # Run hourly
    catchup=False,
    tags=['data', 'ingestion', 'predictive-maintenance']
)


def collect_sensor_data(**context):
    """Collect sensor data from IoT devices."""
    from src.data_collection import IoTSensorSimulator
    
    print("Collecting sensor data...")
    simulator = IoTSensorSimulator()
    
    # Generate data for the past hour
    simulator.stream_data(duration_minutes=60, interval_seconds=60, save_to_file=True)
    
    print("Data collection completed")
    return "data/raw"


def validate_data(**context):
    """Validate collected data quality."""
    from src.preprocessing import DataCleaner
    import yaml
    from pathlib import Path
    
    with open('config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    cleaner = DataCleaner(config)
    
    # Load most recent data
    data_path = Path('data/raw')
    data_files = sorted(data_path.glob('sensor_data_*.json'))
    
    if not data_files:
        raise ValueError("No data files found")
    
    latest_file = data_files[-1]
    df = cleaner.load_data(str(latest_file))
    
    # Validate
    is_valid, errors = cleaner.validate_data_ranges(df)
    
    if not is_valid:
        print(f"Data validation warnings: {errors}")
    else:
        print("Data validation passed")
    
    return is_valid


def store_to_cloud(**context):
    """Store data to cloud storage."""
    print("Storing data to cloud storage...")
    # Implementation would depend on cloud provider
    # Example: Upload to S3, Azure Blob, or GCS
    print("Data stored to cloud")
    return True


# Define tasks
collect_task = PythonOperator(
    task_id='collect_data',
    python_callable=collect_sensor_data,
    dag=dag
)

validate_task = PythonOperator(
    task_id='validate_data',
    python_callable=validate_data,
    dag=dag
)

store_task = PythonOperator(
    task_id='store_to_cloud',
    python_callable=store_to_cloud,
    dag=dag
)

cleanup_task = BashOperator(
    task_id='cleanup',
    bash_command='echo "Data pipeline completed"',
    dag=dag
)

# Define task dependencies
collect_task >> validate_task >> store_task >> cleanup_task
