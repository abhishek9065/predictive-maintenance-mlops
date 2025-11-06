"""
Simplified Evidently AI Monitoring Script
Compatible with Evidently 0.7.15+
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
import logging

from evidently import Report
from evidently import metric_preset

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_monitoring(reference_path: str, current_path: str, output_dir: str = "reports/evidently"):
    """
    Run Evidently AI monitoring
    
    Args:
        reference_path: Path to reference/training data
        current_path: Path to current/test data
        output_dir: Output directory for reports
    """
    logger.info("="* 70)
    logger.info("EVIDENTLY AI - MODEL MONITORING")
    logger.info("=" * 70)
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Load data
    logger.info(f"Loading reference data: {reference_path}")
    reference_data = pd.read_csv(reference_path)
    
    logger.info(f"Loading current data: {current_path}")
    current_data = pd.read_csv(current_path)
    
    logger.info(f"Reference data shape: {reference_data.shape}")
    logger.info(f"Current data shape: {current_data.shape}")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 1. Data Drift Report
    logger.info("\n1. Generating Data Drift Report...")
    try:
        drift_report = Report(metrics=[
            DataDriftPreset(),
        ])
        drift_report.run(reference_data=reference_data, current_data=current_data)
        
        # Save HTML
        drift_html = output_path / f"data_drift_{timestamp}.html"
        drift_report.save_html(str(drift_html))
        logger.info(f"✅ Data Drift Report: {drift_html}")
        
        # Save JSON
        drift_json = output_path / f"data_drift_{timestamp}.json"
        drift_report.save_json(str(drift_json))
        logger.info(f"✅ Data Drift JSON: {drift_json}")
        
    except Exception as e:
        logger.error(f"❌ Data Drift Report failed: {e}")
    
    # 2. Data Quality Report
    logger.info("\n2. Generating Data Quality Report...")
    try:
        quality_report = Report(metrics=[
            DataQualityPreset(),
        ])
        quality_report.run(reference_data=reference_data, current_data=current_data)
        
        # Save HTML
        quality_html = output_path / f"data_quality_{timestamp}.html"
        quality_report.save_html(str(quality_html))
        logger.info(f"✅ Data Quality Report: {quality_html}")
        
        # Save JSON
        quality_json = output_path / f"data_quality_{timestamp}.json"
        quality_report.save_json(str(quality_json))
        logger.info(f"✅ Data Quality JSON: {quality_json}")
        
    except Exception as e:
        logger.error(f"❌ Data Quality Report failed: {e}")
    
    # 3. Dataset-level Metrics
    logger.info("\n3. Generating Dataset Metrics...")
    try:
        metrics_report = Report(metrics=[
            DatasetDriftMetric(),
            DatasetMissingValuesMetric(),
        ])
        metrics_report.run(reference_data=reference_data, current_data=current_data)
        
        # Save HTML
        metrics_html = output_path / f"dataset_metrics_{timestamp}.html"
        metrics_report.save_html(str(metrics_html))
        logger.info(f"✅ Dataset Metrics Report: {metrics_html}")
        
        # Save JSON
        metrics_json = output_path / f"dataset_metrics_{timestamp}.json"
        metrics_report.save_json(str(metrics_json))
        logger.info(f"✅ Dataset Metrics JSON: {metrics_json}")
        
    except Exception as e:
        logger.error(f"❌ Dataset Metrics Report failed: {e}")
    
    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("MONITORING SUMMARY")
    logger.info("=" * 70)
    logger.info(f"📊 Reports generated in: {output_path}")
    logger.info(f"📁 HTML Reports: {len(list(output_path.glob('*.html')))} files")
    logger.info(f"📄 JSON Reports: {len(list(output_path.glob('*.json')))} files")
    logger.info("=" * 70)
    
    return {
        "status": "success",
        "output_dir": str(output_path),
        "reports_count": len(list(output_path.glob('*.html')))
    }


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Evidently AI Monitoring")
    parser.add_argument("--reference", default="data/train.csv", help="Reference data path")
    parser.add_argument("--current", default="data/test.csv", help="Current data path")
    parser.add_argument("--output", default="reports/evidently", help="Output directory")
    
    args = parser.parse_args()
    
    result = run_monitoring(args.reference, args.current, args.output)
    print(f"\n✅ Monitoring complete: {result}")
