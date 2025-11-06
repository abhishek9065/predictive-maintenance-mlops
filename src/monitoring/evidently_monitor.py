"""
Evidently AI - Model Monitoring & Explainability
Monitors model drift, data quality, and generates explainability reports
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional, List
import json
import logging
from datetime import datetime

try:
    from evidently.report import Report
    from evidently.metric_preset import DataDriftPreset, DataQualityPreset, TargetDriftPreset
    from evidently.metrics import *
    EVIDENTLY_AVAILABLE = True
except ImportError:
    EVIDENTLY_AVAILABLE = False
    logging.warning("Evidently AI not installed. Install with: pip install evidently")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ModelMonitor:
    """Monitor model performance and data drift using Evidently AI"""
    
    def __init__(self, output_dir: str = "reports/evidently"):
        """
        Initialize model monitor
        
        Args:
            output_dir: Directory to save reports
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        if not EVIDENTLY_AVAILABLE:
            raise ImportError("Evidently AI not installed. Run: pip install evidently")
    
    def create_column_mapping(self) -> ColumnMapping:
        """
        Create column mapping for Evidently
        
        Returns:
            ColumnMapping object
        """
        column_mapping = ColumnMapping()
        column_mapping.target = 'failure'
        column_mapping.prediction = 'prediction'
        column_mapping.numerical_features = [
            'temperature', 'vibration', 'pressure', 'rpm', 'power_consumption'
        ]
        
        return column_mapping
    
    def generate_data_drift_report(self, reference_data: pd.DataFrame,
                                   current_data: pd.DataFrame,
                                   save_html: bool = True) -> Dict[str, Any]:
        """
        Generate data drift report
        
        Args:
            reference_data: Reference/training data
            current_data: Current/production data
            save_html: Whether to save HTML report
            
        Returns:
            Drift metrics
        """
        logger.info("Generating data drift report...")
        
        column_mapping = self.create_column_mapping()
        
        # Create report
        report = Report(metrics=[
            DataDriftPreset(),
        ])
        
        report.run(
            reference_data=reference_data,
            current_data=current_data,
            column_mapping=column_mapping
        )
        
        # Save HTML report
        if save_html:
            html_path = self.output_dir / f"data_drift_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            report.save_html(str(html_path))
            logger.info(f"Data drift report saved: {html_path}")
        
        # Extract metrics
        report_dict = report.as_dict()
        
        metrics = {
            "dataset_drift_detected": report_dict['metrics'][0]['result']['dataset_drift'],
            "drift_share": report_dict['metrics'][0]['result']['drift_share'],
            "number_of_drifted_columns": report_dict['metrics'][0]['result']['number_of_drifted_columns'],
            "timestamp": datetime.now().isoformat()
        }
        
        # Save JSON metrics
        json_path = self.output_dir / f"data_drift_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(json_path, 'w') as f:
            json.dump(metrics, f, indent=2)
        
        logger.info(f"Drift detected: {metrics['dataset_drift_detected']}")
        logger.info(f"Drift share: {metrics['drift_share']:.2%}")
        
        return metrics
    
    def generate_data_quality_report(self, data: pd.DataFrame,
                                    save_html: bool = True) -> Dict[str, Any]:
        """
        Generate data quality report
        
        Args:
            data: Dataset to analyze
            save_html: Whether to save HTML report
            
        Returns:
            Quality metrics
        """
        logger.info("Generating data quality report...")
        
        column_mapping = self.create_column_mapping()
        
        # Create report
        report = Report(metrics=[
            DataQualityPreset(),
        ])
        
        report.run(
            reference_data=data,
            current_data=None,
            column_mapping=column_mapping
        )
        
        # Save HTML report
        if save_html:
            html_path = self.output_dir / f"data_quality_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            report.save_html(str(html_path))
            logger.info(f"Data quality report saved: {html_path}")
        
        # Save JSON report
        json_path = self.output_dir / f"data_quality_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report.save_json(str(json_path))
        
        logger.info("Data quality report generated")
        
        return {"status": "success", "report_path": str(html_path)}
    
    def generate_target_drift_report(self, reference_data: pd.DataFrame,
                                    current_data: pd.DataFrame,
                                    save_html: bool = True) -> Dict[str, Any]:
        """
        Generate target drift report
        
        Args:
            reference_data: Reference/training data
            current_data: Current/production data
            save_html: Whether to save HTML report
            
        Returns:
            Target drift metrics
        """
        logger.info("Generating target drift report...")
        
        column_mapping = self.create_column_mapping()
        
        # Create report
        report = Report(metrics=[
            TargetDriftPreset(),
        ])
        
        report.run(
            reference_data=reference_data,
            current_data=current_data,
            column_mapping=column_mapping
        )
        
        # Save HTML report
        if save_html:
            html_path = self.output_dir / f"target_drift_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            report.save_html(str(html_path))
            logger.info(f"Target drift report saved: {html_path}")
        
        # Save JSON report
        json_path = self.output_dir / f"target_drift_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report.save_json(str(json_path))
        
        logger.info("Target drift report generated")
        
        return {"status": "success", "report_path": str(html_path)}
    
    def generate_model_performance_report(self, reference_data: pd.DataFrame,
                                         current_data: pd.DataFrame,
                                         save_html: bool = True) -> Dict[str, Any]:
        """
        Generate comprehensive model performance report
        
        Args:
            reference_data: Reference data with predictions
            current_data: Current data with predictions
            save_html: Whether to save HTML report
            
        Returns:
            Performance metrics
        """
        logger.info("Generating model performance report...")
        
        column_mapping = self.create_column_mapping()
        
        # Create comprehensive report
        report = Report(metrics=[
            ClassificationQualityMetric(),
            ClassificationClassBalance(),
            ClassificationConfusionMatrix(),
            ClassificationQualityByClass(),
        ])
        
        report.run(
            reference_data=reference_data,
            current_data=current_data,
            column_mapping=column_mapping
        )
        
        # Save HTML report
        if save_html:
            html_path = self.output_dir / f"model_performance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            report.save_html(str(html_path))
            logger.info(f"Model performance report saved: {html_path}")
        
        # Save JSON report
        json_path = self.output_dir / f"model_performance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report.save_json(str(json_path))
        
        logger.info("Model performance report generated")
        
        return {"status": "success", "report_path": str(html_path)}
    
    def continuous_monitoring(self, reference_data: pd.DataFrame,
                            current_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Run continuous monitoring pipeline
        
        Args:
            reference_data: Reference/training data
            current_data: Current/production data
            
        Returns:
            Complete monitoring results
        """
        logger.info("=" * 70)
        logger.info("EVIDENTLY AI - CONTINUOUS MONITORING")
        logger.info("=" * 70)
        
        results = {}
        
        # 1. Data Drift
        results['data_drift'] = self.generate_data_drift_report(reference_data, current_data)
        
        # 2. Data Quality
        results['data_quality'] = self.generate_data_quality_report(current_data)
        
        # 3. Target Drift (if target is available)
        if 'failure' in current_data.columns:
            results['target_drift'] = self.generate_target_drift_report(reference_data, current_data)
        
        # 4. Model Performance (if predictions are available)
        if 'prediction' in current_data.columns and 'failure' in current_data.columns:
            results['model_performance'] = self.generate_model_performance_report(
                reference_data, current_data
            )
        
        logger.info("=" * 70)
        logger.info("MONITORING SUMMARY")
        logger.info("=" * 70)
        logger.info(f"Data Drift Detected: {results['data_drift']['dataset_drift_detected']}")
        logger.info(f"Drift Share: {results['data_drift']['drift_share']:.2%}")
        logger.info(f"Drifted Columns: {results['data_drift']['number_of_drifted_columns']}")
        logger.info(f"Reports saved to: {self.output_dir}")
        logger.info("=" * 70)
        
        # Save summary
        summary_path = self.output_dir / f"monitoring_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(summary_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"Summary saved: {summary_path}")
        
        return results


def main():
    """Main execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Model monitoring with Evidently AI")
    parser.add_argument("--reference", type=str,
                       default="data/train.csv",
                       help="Reference data path")
    parser.add_argument("--current", type=str,
                       default="data/test.csv",
                       help="Current data path")
    parser.add_argument("--output", type=str,
                       default="reports/evidently",
                       help="Output directory")
    
    args = parser.parse_args()
    
    # Load data
    logger.info(f"Loading reference data: {args.reference}")
    reference_df = pd.read_csv(args.reference)
    
    logger.info(f"Loading current data: {args.current}")
    current_df = pd.read_csv(args.current)
    
    # Initialize monitor
    monitor = ModelMonitor(args.output)
    
    # Run monitoring
    results = monitor.continuous_monitoring(reference_df, current_df)
    
    logger.info("\n✅ Monitoring complete!")
    logger.info(f"Reports saved to: {args.output}")
    
    return results


if __name__ == "__main__":
    main()
