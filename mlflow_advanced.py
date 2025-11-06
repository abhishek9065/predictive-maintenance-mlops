"""
MLflow Advanced Experiment Tracking & Model Management
Comprehensive system for tracking, comparing, and managing ML models
"""

import mlflow
import mlflow.sklearn
from mlflow.tracking import MlflowClient
from pathlib import Path
import json
import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, 
    roc_auc_score, confusion_matrix, classification_report
)
import matplotlib.pyplot as plt
import seaborn as sns


class MLflowExperimentManager:
    """Manages MLflow experiments, tracking, and model registry"""
    
    def __init__(self, experiment_name="predictive_maintenance", tracking_uri=None):
        self.project_root = Path(__file__).parent
        
        # Set tracking URI
        if tracking_uri is None:
            mlruns_dir = (self.project_root / 'mlruns').resolve()
            tracking_uri = f"file:///{mlruns_dir.as_posix()}"
        
        mlflow.set_tracking_uri(tracking_uri)
        
        # Set or create experiment
        self.experiment_name = experiment_name
        mlflow.set_experiment(experiment_name)
        
        self.client = MlflowClient()
        self.experiment = self.client.get_experiment_by_name(experiment_name)
        
        print(f"[*] MLflow Experiment Manager Initialized")
        print(f"    Tracking URI: {tracking_uri}")
        print(f"    Experiment: {experiment_name}")
        print(f"    Experiment ID: {self.experiment.experiment_id}")
    
    def load_data(self):
        """Load and prepare training data"""
        data_dir = self.project_root / "data/raw"
        historical_files = sorted(data_dir.glob("historical_*.json"))
        
        if not historical_files:
            raise FileNotFoundError("No historical data found")
        
        with open(historical_files[-1], 'r') as f:
            data = json.load(f)
        
        print(f"\n[*] Data loaded: {len(data)} samples")
        
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
        
        print(f"    Train: {len(X_train)} samples")
        print(f"    Test: {len(X_test)} samples")
        print(f"    Failure rate: {y.mean():.2%}")
        
        return X_train, X_test, y_train, y_test
    
    def train_model_with_tracking(self, model, model_name, params, X_train, y_train, X_test, y_test):
        """Train a model with comprehensive MLflow tracking"""
        
        with mlflow.start_run(run_name=model_name) as run:
            print(f"\n[*] Training: {model_name}")
            print(f"    Run ID: {run.info.run_id}")
            
            # Train model
            start_time = datetime.now()
            model.fit(X_train, y_train)
            training_time = (datetime.now() - start_time).total_seconds()
            
            # Predictions
            y_train_pred = model.predict(X_train)
            y_test_pred = model.predict(X_test)
            y_test_proba = model.predict_proba(X_test)[:, 1] if hasattr(model, 'predict_proba') else None
            
            # Calculate metrics
            metrics = {
                # Test metrics
                'test_accuracy': float(accuracy_score(y_test, y_test_pred)),
                'test_precision': float(precision_score(y_test, y_test_pred)),
                'test_recall': float(recall_score(y_test, y_test_pred)),
                'test_f1_score': float(f1_score(y_test, y_test_pred)),
                
                # Train metrics
                'train_accuracy': float(accuracy_score(y_train, y_train_pred)),
                'train_precision': float(precision_score(y_train, y_train_pred)),
                'train_recall': float(recall_score(y_train, y_train_pred)),
                'train_f1_score': float(f1_score(y_train, y_train_pred)),
                
                # Additional metrics
                'training_time_seconds': training_time,
                'n_samples_train': len(X_train),
                'n_samples_test': len(X_test),
            }
            
            # ROC AUC if probability available
            if y_test_proba is not None:
                metrics['test_roc_auc'] = float(roc_auc_score(y_test, y_test_proba))
            
            # Overfitting detection
            metrics['overfitting_gap'] = metrics['train_accuracy'] - metrics['test_accuracy']
            
            # Log parameters
            for param_name, param_value in params.items():
                mlflow.log_param(param_name, param_value)
            
            # Log metrics
            for metric_name, metric_value in metrics.items():
                mlflow.log_metric(metric_name, metric_value)
            
            # Log model
            mlflow.sklearn.log_model(model, "model")
            
            # Log confusion matrix as artifact
            cm = confusion_matrix(y_test, y_test_pred)
            self._log_confusion_matrix(cm, model_name)
            
            # Log feature importance if available
            if hasattr(model, 'feature_importances_'):
                self._log_feature_importance(model.feature_importances_, model_name)
            
            # Log classification report
            report = classification_report(y_test, y_test_pred, output_dict=True)
            mlflow.log_dict(report, "classification_report.json")
            
            # Add tags
            mlflow.set_tags({
                "model_type": type(model).__name__,
                "training_date": datetime.now().isoformat(),
                "data_version": "v1.0"
            })
            
            print(f"    Test Accuracy: {metrics['test_accuracy']:.4f}")
            print(f"    Test F1 Score: {metrics['test_f1_score']:.4f}")
            print(f"    Training Time: {training_time:.2f}s")
            
            return run.info.run_id, metrics
    
    def _log_confusion_matrix(self, cm, model_name):
        """Create and log confusion matrix visualization"""
        plt.figure(figsize=(8, 6))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                    xticklabels=['Normal', 'Failing'],
                    yticklabels=['Normal', 'Failing'])
        plt.title(f'Confusion Matrix - {model_name}')
        plt.ylabel('True Label')
        plt.xlabel('Predicted Label')
        
        # Save and log
        cm_path = self.project_root / "temp_confusion_matrix.png"
        plt.savefig(cm_path, bbox_inches='tight', dpi=150)
        mlflow.log_artifact(str(cm_path), "plots")
        plt.close()
        
        # Clean up
        if cm_path.exists():
            cm_path.unlink()
    
    def _log_feature_importance(self, importances, model_name):
        """Create and log feature importance visualization"""
        feature_names = ['Temperature', 'Vibration', 'Pressure', 'Current', 'RPM']
        
        plt.figure(figsize=(10, 6))
        indices = np.argsort(importances)[::-1]
        plt.bar(range(len(importances)), importances[indices])
        plt.xticks(range(len(importances)), [feature_names[i] for i in indices], rotation=45)
        plt.title(f'Feature Importance - {model_name}')
        plt.ylabel('Importance')
        plt.xlabel('Feature')
        plt.tight_layout()
        
        # Save and log
        fi_path = self.project_root / "temp_feature_importance.png"
        plt.savefig(fi_path, bbox_inches='tight', dpi=150)
        mlflow.log_artifact(str(fi_path), "plots")
        plt.close()
        
        # Also log as dict
        fi_dict = {feature_names[i]: float(importances[i]) for i in range(len(importances))}
        mlflow.log_dict(fi_dict, "feature_importance.json")
        
        # Clean up
        if fi_path.exists():
            fi_path.unlink()
    
    def compare_experiments(self, metric='test_accuracy', top_n=5):
        """Compare all experiments and return top performers"""
        print(f"\n[*] Comparing Experiments by {metric}")
        print("="*80)
        
        # Get all runs
        runs = self.client.search_runs(
            experiment_ids=[self.experiment.experiment_id],
            order_by=[f"metrics.{metric} DESC"],
            max_results=top_n
        )
        
        if not runs:
            print("    No runs found")
            return []
        
        # Create comparison table
        comparison_data = []
        for i, run in enumerate(runs, 1):
            metrics = run.data.metrics
            params = run.data.params
            tags = run.data.tags
            
            comparison_data.append({
                'Rank': i,
                'Run ID': run.info.run_id[:8],
                'Model': tags.get('model_type', params.get('model_type', 'Unknown')),
                'Test Accuracy': metrics.get('test_accuracy', 0),
                'Test F1': metrics.get('test_f1_score', 0),
                'Test Precision': metrics.get('test_precision', 0),
                'Test Recall': metrics.get('test_recall', 0),
                'Training Time': metrics.get('training_time_seconds', 0),
                'Date': tags.get('training_date', 'Unknown')[:10]
            })
        
        df = pd.DataFrame(comparison_data)
        print(df.to_string(index=False))
        
        print(f"\n[OK] Top model: {comparison_data[0]['Model']}")
        print(f"    Run ID: {comparison_data[0]['Run ID']}")
        print(f"    {metric}: {comparison_data[0]['Test Accuracy']:.4f}")
        
        return comparison_data
    
    def register_model(self, run_id, model_name="predictive_maintenance_model"):
        """Register model in MLflow Model Registry"""
        print(f"\n[*] Registering Model to Registry")
        
        # Note: Model Registry requires a database backend
        # For local file-based tracking, we'll use a simplified approach
        model_uri = f"runs:/{run_id}/model"
        
        try:
            # Try to register (works with database backend)
            model_version = mlflow.register_model(model_uri, model_name)
            print(f"    [OK] Model registered: {model_name}")
            print(f"    Version: {model_version.version}")
            return model_version
        except Exception as e:
            print(f"    [INFO] Model Registry not available (requires DB backend)")
            print(f"    Model URI: {model_uri}")
            print(f"    Use this URI to load the model directly")
            return None
    
    def load_best_model(self, metric='test_accuracy'):
        """Load the best performing model"""
        print(f"\n[*] Loading Best Model by {metric}")
        
        # Get best run
        runs = self.client.search_runs(
            experiment_ids=[self.experiment.experiment_id],
            order_by=[f"metrics.{metric} DESC"],
            max_results=1
        )
        
        if not runs:
            raise ValueError("No models found")
        
        best_run = runs[0]
        run_id = best_run.info.run_id
        
        print(f"    Run ID: {run_id[:16]}...")
        print(f"    {metric}: {best_run.data.metrics.get(metric, 0):.4f}")
        
        # Load model
        model_uri = f"runs:/{run_id}/model"
        model = mlflow.sklearn.load_model(model_uri)
        
        print(f"    [OK] Model loaded successfully")
        
        return model, run_id
    
    def generate_experiment_report(self):
        """Generate comprehensive experiment tracking report"""
        print(f"\n[*] Generating Experiment Report")
        print("="*80)
        
        # Get all runs
        runs = self.client.search_runs(
            experiment_ids=[self.experiment.experiment_id]
        )
        
        report = {
            "experiment_name": self.experiment_name,
            "experiment_id": self.experiment.experiment_id,
            "total_runs": len(runs),
            "generated_at": datetime.now().isoformat(),
            "runs": []
        }
        
        for run in runs:
            run_info = {
                "run_id": run.info.run_id,
                "start_time": datetime.fromtimestamp(run.info.start_time / 1000).isoformat(),
                "status": run.info.status,
                "metrics": run.data.metrics,
                "params": run.data.params,
                "tags": run.data.tags
            }
            report["runs"].append(run_info)
        
        # Save report
        report_path = self.project_root / "mlflow_experiment_report.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"    Total Runs: {len(runs)}")
        print(f"    Report saved: {report_path.name}")
        print(f"    [OK] Report generated successfully")
        
        return report


def main():
    """Run comprehensive MLflow experiment tracking"""
    
    print("="*80)
    print("MLflow Advanced Experiment Tracking & Model Management")
    print("="*80)
    
    # Initialize manager
    manager = MLflowExperimentManager()
    
    # Load data
    X_train, X_test, y_train, y_test = manager.load_data()
    
    # Define models to experiment with
    models_config = [
        {
            "model": RandomForestClassifier(n_estimators=100, random_state=42),
            "name": "random_forest_baseline",
            "params": {
                "model_type": "RandomForest",
                "n_estimators": 100,
                "max_depth": None,
                "random_state": 42
            }
        },
        {
            "model": RandomForestClassifier(
                n_estimators=200, 
                max_depth=20, 
                min_samples_split=5,
                random_state=42
            ),
            "name": "random_forest_tuned",
            "params": {
                "model_type": "RandomForest",
                "n_estimators": 200,
                "max_depth": 20,
                "min_samples_split": 5,
                "random_state": 42
            }
        },
        {
            "model": GradientBoostingClassifier(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=5,
                random_state=42
            ),
            "name": "gradient_boosting",
            "params": {
                "model_type": "GradientBoosting",
                "n_estimators": 100,
                "learning_rate": 0.1,
                "max_depth": 5,
                "random_state": 42
            }
        },
        {
            "model": GradientBoostingClassifier(
                n_estimators=200,
                learning_rate=0.05,
                max_depth=7,
                subsample=0.8,
                random_state=42
            ),
            "name": "gradient_boosting_tuned",
            "params": {
                "model_type": "GradientBoosting",
                "n_estimators": 200,
                "learning_rate": 0.05,
                "max_depth": 7,
                "subsample": 0.8,
                "random_state": 42
            }
        },
        {
            "model": LogisticRegression(max_iter=1000, random_state=42),
            "name": "logistic_regression",
            "params": {
                "model_type": "LogisticRegression",
                "max_iter": 1000,
                "solver": "lbfgs",
                "random_state": 42
            }
        }
    ]
    
    # Train all models with tracking
    print("\n" + "="*80)
    print("TRAINING MODELS WITH MLFLOW TRACKING")
    print("="*80)
    
    run_ids = []
    for config in models_config:
        run_id, metrics = manager.train_model_with_tracking(
            model=config["model"],
            model_name=config["name"],
            params=config["params"],
            X_train=X_train,
            y_train=y_train,
            X_test=X_test,
            y_test=y_test
        )
        run_ids.append(run_id)
    
    print(f"\n[OK] Trained {len(models_config)} models successfully!")
    
    # Compare experiments
    comparison = manager.compare_experiments(metric='test_accuracy', top_n=5)
    
    # Generate report
    report = manager.generate_experiment_report()
    
    # Load and test best model
    best_model, best_run_id = manager.load_best_model(metric='test_accuracy')
    
    # Make a test prediction
    print(f"\n[*] Testing Best Model Predictions")
    test_sample = X_test[0:1]
    prediction = best_model.predict(test_sample)
    proba = best_model.predict_proba(test_sample)[0] if hasattr(best_model, 'predict_proba') else None
    
    print(f"    Test Sample: {test_sample[0]}")
    print(f"    Prediction: {'Failing' if prediction[0] else 'Normal'}")
    if proba is not None:
        print(f"    Confidence: {max(proba):.2%}")
    
    print("\n" + "="*80)
    print("MLFLOW EXPERIMENT TRACKING COMPLETE!")
    print("="*80)
    print("\n[SUCCESS] All tasks completed successfully!")
    print(f"\nNext Steps:")
    print(f"1. View experiments: http://localhost:5000")
    print(f"2. Check report: mlflow_experiment_report.json")
    print(f"3. Compare models in MLflow UI")
    print(f"4. Deploy best model to production")


if __name__ == "__main__":
    main()
