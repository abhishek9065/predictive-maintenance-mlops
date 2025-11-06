"""
Performance Monitoring Module
Tracks model performance metrics and generates alerts.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging
from pathlib import Path
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """Monitor model performance in production."""
    
    def __init__(self, config: Dict):
        """
        Initialize performance monitor.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.monitoring_config = config.get('monitoring', {})
        self.thresholds = self.monitoring_config.get('thresholds', {})
        self.metrics_history = []
    
    def track_prediction(self, prediction: Dict):
        """
        Track a single prediction.
        
        Args:
            prediction: Prediction dictionary
        """
        prediction['tracked_at'] = datetime.now().isoformat()
        self.metrics_history.append(prediction)
    
    def calculate_performance_metrics(self, 
                                     y_true: np.ndarray,
                                     y_pred: np.ndarray,
                                     y_pred_proba: Optional[np.ndarray] = None) -> Dict:
        """
        Calculate performance metrics.
        
        Args:
            y_true: True labels
            y_pred: Predicted labels
            y_pred_proba: Prediction probabilities
            
        Returns:
            Dictionary of metrics
        """
        from sklearn.metrics import (
            accuracy_score, precision_score, recall_score,
            f1_score, roc_auc_score, confusion_matrix
        )
        
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'accuracy': accuracy_score(y_true, y_pred),
            'precision': precision_score(y_true, y_pred, average='binary', zero_division=0),
            'recall': recall_score(y_true, y_pred, average='binary', zero_division=0),
            'f1_score': f1_score(y_true, y_pred, average='binary', zero_division=0),
            'confusion_matrix': confusion_matrix(y_true, y_pred).tolist()
        }
        
        if y_pred_proba is not None:
            try:
                metrics['roc_auc'] = roc_auc_score(y_true, y_pred_proba)
            except ValueError:
                metrics['roc_auc'] = None
        
        return metrics
    
    def check_performance_thresholds(self, metrics: Dict) -> List[str]:
        """
        Check if metrics meet thresholds.
        
        Args:
            metrics: Calculated metrics
            
        Returns:
            List of alerts
        """
        alerts = []
        
        # Check accuracy threshold
        if metrics['accuracy'] < self.thresholds.get('accuracy_min', 0.85):
            alerts.append(
                f"Accuracy below threshold: {metrics['accuracy']:.3f} < "
                f"{self.thresholds['accuracy_min']}"
            )
        
        # Check precision threshold
        if metrics['precision'] < self.thresholds.get('precision_min', 0.80):
            alerts.append(
                f"Precision below threshold: {metrics['precision']:.3f} < "
                f"{self.thresholds['precision_min']}"
            )
        
        # Check recall threshold
        if metrics['recall'] < self.thresholds.get('recall_min', 0.80):
            alerts.append(
                f"Recall below threshold: {metrics['recall']:.3f} < "
                f"{self.thresholds['recall_min']}"
            )
        
        return alerts
    
    def generate_performance_report(self, 
                                   time_window_hours: int = 24) -> Dict:
        """
        Generate performance report for a time window.
        
        Args:
            time_window_hours: Time window in hours
            
        Returns:
            Performance report dictionary
        """
        cutoff_time = datetime.now() - timedelta(hours=time_window_hours)
        
        # Filter recent predictions
        recent_predictions = [
            p for p in self.metrics_history
            if datetime.fromisoformat(p['tracked_at']) > cutoff_time
        ]
        
        report = {
            'time_window_hours': time_window_hours,
            'total_predictions': len(recent_predictions),
            'generated_at': datetime.now().isoformat()
        }
        
        if recent_predictions:
            # Calculate statistics
            failure_predictions = sum(1 for p in recent_predictions if p.get('prediction') == 1)
            avg_probability = np.mean([p.get('failure_probability', 0) for p in recent_predictions])
            
            report.update({
                'failure_predictions': failure_predictions,
                'failure_rate': failure_predictions / len(recent_predictions),
                'average_failure_probability': float(avg_probability)
            })
        
        logger.info(f"Generated performance report: {report}")
        return report
    
    def save_metrics(self, file_path: str):
        """
        Save metrics history to file.
        
        Args:
            file_path: Output file path
        """
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w') as f:
            json.dump(self.metrics_history, f, indent=2)
        
        logger.info(f"Metrics saved to {file_path}")
    
    def load_metrics(self, file_path: str):
        """
        Load metrics history from file.
        
        Args:
            file_path: Input file path
        """
        with open(file_path, 'r') as f:
            self.metrics_history = json.load(f)
        
        logger.info(f"Loaded {len(self.metrics_history)} metrics from {file_path}")


def main():
    """Main function for testing performance monitor."""
    config = {
        'monitoring': {
            'thresholds': {
                'accuracy_min': 0.85,
                'precision_min': 0.80,
                'recall_min': 0.80
            }
        }
    }
    
    monitor = PerformanceMonitor(config)
    
    # Test with sample data
    y_true = np.array([0, 0, 1, 1, 0, 1, 1, 0])
    y_pred = np.array([0, 0, 1, 0, 0, 1, 1, 0])
    
    metrics = monitor.calculate_performance_metrics(y_true, y_pred)
    alerts = monitor.check_performance_thresholds(metrics)
    
    if alerts:
        logger.warning(f"Performance alerts: {alerts}")
    else:
        logger.info("All metrics within thresholds")


if __name__ == "__main__":
    main()
