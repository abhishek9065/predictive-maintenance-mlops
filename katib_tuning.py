"""
Hyperparameter Tuning with Katib (Kubeflow)
Optimizes model hyperparameters using Kubernetes-native tuning
"""

import json
import os
import argparse
import mlflow
import numpy as np
import tempfile
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import joblib


class KatibHyperparameterTuning:
    """Hyperparameter tuning compatible with Katib"""
    
    def __init__(self, data_path='data/raw'):
        self.data_path = data_path
        self.X_train = None
        self.X_test = None
        self.y_train = None
        self.y_test = None
        
    def load_data(self):
        """Load and prepare data for training"""
        print("[INFO] Loading data...")
        
        # Try CSV files first (new format)
        import glob
        csv_files = glob.glob(f'{self.data_path}/*.csv')
        
        if csv_files and any('train' in f for f in csv_files):
            # Use CSV data
            train_file = [f for f in csv_files if 'train' in f][0]
            print(f"[INFO] Using CSV data file: {train_file}")
            
            import pandas as pd
            df = pd.read_csv(train_file)
            
            # Extract features and labels
            # Try both old and new column names
            if 'current' in df.columns:
                feature_cols = ['temperature', 'vibration', 'pressure', 'rpm', 'current']
            else:
                feature_cols = ['temperature', 'vibration', 'pressure', 'rpm', 'power_consumption']
            X = df[feature_cols].values
            y = df['failure'].values
            
        else:
            # Try JSON files (old format)
            data_files = glob.glob(f'{self.data_path}/historical_*.json')
            if not data_files:
                raise FileNotFoundError("No data files found. Run: python generate_sample_data.py")
            
            latest_file = sorted(data_files)[-1]
            print(f"[INFO] Using JSON data file: {latest_file}")
            
            with open(latest_file, 'r') as f:
                data = json.load(f)
            
            # Extract features
            X = []
            y = []
            
            for record in data:
                features = [
                    record['sensors']['temperature']['value'],
                    record['sensors']['vibration']['value'],
                    record['sensors']['pressure']['value'],
                    record['sensors'].get('humidity', {}).get('value', 0),  # Default if missing
                    record['sensors'].get('speed', record['sensors'].get('power_consumption', {})).get('value', 0)
                ]
                X.append(features)
                y.append(1 if record['failure'] else 0)
            
            X = np.array(X)
            y = np.array(y)
        
        # Split data
        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        print(f"[INFO] Training samples: {len(self.X_train)}")
        print(f"[INFO] Test samples: {len(self.X_test)}")
        
    def train_random_forest(self, n_estimators, max_depth, min_samples_split, min_samples_leaf):
        """Train Random Forest with given hyperparameters"""
        print(f"[TRAINING] Random Forest: n_estimators={n_estimators}, max_depth={max_depth}")
        
        model = RandomForestClassifier(
            n_estimators=int(n_estimators),
            max_depth=int(max_depth) if max_depth > 0 else None,
            min_samples_split=int(min_samples_split),
            min_samples_leaf=int(min_samples_leaf),
            random_state=42
        )
        
        model.fit(self.X_train, self.y_train)
        
        # Evaluate
        y_pred = model.predict(self.X_test)
        metrics = self.calculate_metrics(y_pred)
        
        return model, metrics
    
    def train_gradient_boosting(self, n_estimators, max_depth, learning_rate, min_samples_split):
        """Train Gradient Boosting with given hyperparameters"""
        print(f"[TRAINING] Gradient Boosting: n_estimators={n_estimators}, lr={learning_rate}")
        
        model = GradientBoostingClassifier(
            n_estimators=int(n_estimators),
            max_depth=int(max_depth),
            learning_rate=float(learning_rate),
            min_samples_split=int(min_samples_split),
            random_state=42
        )
        
        model.fit(self.X_train, self.y_train)
        
        # Evaluate
        y_pred = model.predict(self.X_test)
        metrics = self.calculate_metrics(y_pred)
        
        return model, metrics
    
    def train_logistic_regression(self, C, max_iter, penalty):
        """Train Logistic Regression with given hyperparameters"""
        print(f"[TRAINING] Logistic Regression: C={C}, penalty={penalty}")
        
        model = LogisticRegression(
            C=float(C),
            max_iter=int(max_iter),
            penalty=penalty,
            random_state=42,
            solver='liblinear'
        )
        
        model.fit(self.X_train, self.y_train)
        
        # Evaluate
        y_pred = model.predict(self.X_test)
        metrics = self.calculate_metrics(y_pred)
        
        return model, metrics
    
    def calculate_metrics(self, y_pred):
        """Calculate evaluation metrics"""
        accuracy = accuracy_score(self.y_test, y_pred)
        precision = precision_score(self.y_test, y_pred, zero_division=0)
        recall = recall_score(self.y_test, y_pred, zero_division=0)
        f1 = f1_score(self.y_test, y_pred, zero_division=0)
        
        metrics = {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1': f1
        }
        
        print(f"[METRICS] Accuracy: {accuracy:.4f}, F1: {f1:.4f}")
        return metrics
    
    def save_model(self, model, model_name, metrics):
        """Save model and metrics"""
        os.makedirs('models/katib', exist_ok=True)
        
        model_path = f'models/katib/{model_name}.pkl'
        joblib.dump(model, model_path)
        print(f"[SAVED] Model: {model_path}")
        
        metrics_path = f'models/katib/{model_name}_metrics.json'
        with open(metrics_path, 'w') as f:
            json.dump(metrics, f, indent=2)
        print(f"[SAVED] Metrics: {metrics_path}")
        
        return model_path


def main():
    """Main training function for Katib"""
    parser = argparse.ArgumentParser(description='Katib Hyperparameter Tuning')
    
    # Model selection
    parser.add_argument('--model', type=str, default='random_forest',
                        choices=['random_forest', 'gradient_boosting', 'logistic_regression'],
                        help='Model type')
    
    # Random Forest hyperparameters
    parser.add_argument('--n_estimators', type=int, default=100)
    parser.add_argument('--max_depth', type=int, default=10)
    parser.add_argument('--min_samples_split', type=int, default=2)
    parser.add_argument('--min_samples_leaf', type=int, default=1)
    
    # Gradient Boosting hyperparameters
    parser.add_argument('--learning_rate', type=float, default=0.1)
    
    # Logistic Regression hyperparameters
    parser.add_argument('--C', type=float, default=1.0)
    parser.add_argument('--max_iter', type=int, default=1000)
    parser.add_argument('--penalty', type=str, default='l2', choices=['l1', 'l2'])
    
    # Data path
    parser.add_argument('--data_path', type=str, default='data/raw')
    
    args = parser.parse_args()
    
    print("="*70)
    print("KATIB HYPERPARAMETER TUNING")
    print("="*70)
    print(f"Model: {args.model}")
    print(f"Parameters: {vars(args)}")
    print()
    
    # Initialize tuner
    tuner = KatibHyperparameterTuning(data_path=args.data_path)
    tuner.load_data()
    
    # Train based on model type
    if args.model == 'random_forest':
        model, metrics = tuner.train_random_forest(
            n_estimators=args.n_estimators,
            max_depth=args.max_depth,
            min_samples_split=args.min_samples_split,
            min_samples_leaf=args.min_samples_leaf
        )
        model_name = f"rf_ne{args.n_estimators}_md{args.max_depth}"
        
    elif args.model == 'gradient_boosting':
        model, metrics = tuner.train_gradient_boosting(
            n_estimators=args.n_estimators,
            max_depth=args.max_depth,
            learning_rate=args.learning_rate,
            min_samples_split=args.min_samples_split
        )
        model_name = f"gb_ne{args.n_estimators}_lr{args.learning_rate}"
        
    elif args.model == 'logistic_regression':
        model, metrics = tuner.train_logistic_regression(
            C=args.C,
            max_iter=args.max_iter,
            penalty=args.penalty
        )
        model_name = f"lr_C{args.C}_{args.penalty}"
    
    # Save model
    model_path = tuner.save_model(model, model_name, metrics)
    
    # Output metrics for Katib (prints to stdout for Katib to parse)
    print()
    print("="*70)
    print("KATIB METRICS OUTPUT")
    print("="*70)
    # Katib looks for these specific metric names
    print(f"accuracy={metrics['accuracy']:.6f}")
    print(f"precision={metrics['precision']:.6f}")
    print(f"recall={metrics['recall']:.6f}")
    print(f"f1_score={metrics['f1']:.6f}")
    print("="*70)
    
    # Save best metrics for Katib to read
    # Use temp directory that works on both Unix and Windows
    import tempfile
    metrics_file = Path(tempfile.gettempdir()) / 'katib_metrics.json'
    with open(metrics_file, 'w') as f:
        json.dump(metrics, f)
    print(f"[INFO] Metrics saved to: {metrics_file}")
    
    return metrics['accuracy']


if __name__ == '__main__':
    accuracy = main()
    print(f"\n[FINAL] Accuracy: {accuracy:.6f}")
