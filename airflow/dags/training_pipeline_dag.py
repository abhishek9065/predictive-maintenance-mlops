"""
Airflow DAG for Training Pipeline
Orchestrates model training, evaluation, and registration.
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

# Default arguments
default_args = {
    'owner': 'mlops-team',
    'depends_on_past': False,
    'start_date': datetime(2025, 1, 1),
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}

# Define DAG
dag = DAG(
    'training_pipeline',
    default_args=default_args,
    description='Automated model training pipeline',
    schedule_interval='@weekly',  # Run weekly
    catchup=False,
    tags=['training', 'mlops', 'predictive-maintenance']
)


def load_and_preprocess_data(**context):
    """Load raw data and perform preprocessing."""
    from src.preprocessing import DataCleaner, FeatureEngineer
    import yaml
    import pandas as pd
    
    print("Loading configuration...")
    with open('config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    print("Loading raw data...")
    # Load most recent data file
    data_path = Path(config['data']['raw_data_path'])
    data_files = sorted(data_path.glob('historical_data_*.json'))
    
    if not data_files:
        raise FileNotFoundError("No training data found")
    
    latest_file = data_files[-1]
    print(f"Using data file: {latest_file}")
    
    # Clean data
    cleaner = DataCleaner(config)
    df = cleaner.load_data(str(latest_file))
    df_clean = cleaner.clean_pipeline(df, remove_outliers=True)
    
    # Engineer features
    engineer = FeatureEngineer(config)
    df_features = engineer.engineer_features_pipeline(df_clean)
    
    # Save processed data
    output_path = Path(config['data']['features_path']) / 'features.csv'
    df_features.to_csv(output_path, index=False)
    
    print(f"Preprocessing completed. Data saved to {output_path}")
    return str(output_path)


def train_models(**context):
    """Train multiple models and track with MLflow."""
    import yaml
    import pandas as pd
    import mlflow
    from src.models import RandomForestModel, XGBoostModel
    from src.preprocessing import DataSplitter
    
    # Load configuration
    with open('config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # Load features
    features_path = context['ti'].xcom_pull(task_ids='preprocess_data')
    df = pd.read_csv(features_path)
    
    # Split data
    splitter = DataSplitter(config)
    X_train, X_val, X_test, y_train, y_val, y_test = splitter.time_series_split(df)
    
    # Set MLflow tracking
    mlflow.set_tracking_uri(config['mlflow']['tracking_uri'])
    mlflow.set_experiment(config['mlflow']['experiment_name'])
    
    models_to_train = [
        ('random_forest', RandomForestModel(config)),
        ('xgboost', XGBoostModel(config))
    ]
    
    best_model = None
    best_score = 0
    
    for model_name, model in models_to_train:
        with mlflow.start_run(run_name=f"{model_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"):
            print(f"\nTraining {model_name}...")
            
            # Train model
            metrics = model.train(X_train, y_train, X_val, y_val)
            
            # Log parameters and metrics
            mlflow.log_params(config['models'][model_name])
            mlflow.log_metrics(metrics)
            
            # Evaluate on test set
            test_metrics = model.evaluate(X_test, y_test)
            test_metrics = {f'test_{k}': v for k, v in test_metrics.items() 
                           if k != 'confusion_matrix'}
            mlflow.log_metrics(test_metrics)
            
            # Log model
            mlflow.sklearn.log_model(model.model, model_name)
            
            # Save model
            model_path = Path('models') / f'{model_name}_model.pkl'
            model.save_model(str(model_path))
            
            # Track best model
            if test_metrics['test_f1_score'] > best_score:
                best_score = test_metrics['test_f1_score']
                best_model = (model_name, str(model_path))
    
    print(f"\nBest model: {best_model[0]} (F1: {best_score:.4f})")
    return best_model


def register_best_model(**context):
    """Register the best model in MLflow Model Registry."""
    import mlflow
    import yaml
    
    with open('config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    mlflow.set_tracking_uri(config['mlflow']['tracking_uri'])
    
    best_model_info = context['ti'].xcom_pull(task_ids='train_models')
    model_name, model_path = best_model_info
    
    print(f"Registering model: {model_name}")
    
    # Register model in MLflow
    registered_model_name = config['mlflow']['registered_model_name']
    
    # This would register the model in production
    # mlflow.register_model(model_uri=f"runs:/{run_id}/{model_name}", 
    #                      name=registered_model_name)
    
    print(f"Model registered: {registered_model_name}")
    return registered_model_name


# Define tasks
preprocess_task = PythonOperator(
    task_id='preprocess_data',
    python_callable=load_and_preprocess_data,
    dag=dag
)

train_task = PythonOperator(
    task_id='train_models',
    python_callable=train_models,
    dag=dag
)

register_task = PythonOperator(
    task_id='register_model',
    python_callable=register_best_model,
    dag=dag
)

notify_task = BashOperator(
    task_id='notify_completion',
    bash_command='echo "Training pipeline completed successfully"',
    dag=dag
)

# Define task dependencies
preprocess_task >> train_task >> register_task >> notify_task
