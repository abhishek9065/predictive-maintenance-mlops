"""
Evidently AI Monitoring - Working Version
Uses Evidently 0.7.15+ API
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
import logging

try:
    from evidently import Report
    from evidently.metrics import (
        DatasetDriftMetric,
        DatasetMissingValuesMetric,
        DatasetCorrelationsMetric,
        DatasetSummaryMetric,
    )
    EVIDENTLY_AVAILABLE = True
except ImportError as e:
    EVIDENTLY_AVAILABLE = False
    logging.error(f"Evidently not available: {e}")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_monitoring(reference_path: str, current_path: str, output_dir: str = "reports/evidently"):
    """Run Evidently AI monitoring"""
    
    logger.info("="* 70)
    logger.info("EVIDENTLY AI - MODEL MONITORING")
    logger.info("=" * 70)
    
    if not EVIDENTLY_AVAILABLE:
        logger.error("Evidently not available")
        return {"status": "error", "message": "Evidently not installed"}
    
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
    reports_generated = 0
    
    # 1. Dataset Drift
    logger.info("\n1. Generating Dataset Drift Report...")
    try:
        report = Report(metrics=[
            DatasetDriftMetric(),
            DatasetMissingValuesMetric(),
            DatasetCorrelationsMetric(),
        ])
        report.run(reference_data=reference_data, current_data=current_data)
        
        # Save
        html_path = output_path / f"dataset_drift_{timestamp}.html"
        json_path = output_path / f"dataset_drift_{timestamp}.json"
        
        report.save_html(str(html_path))
        report.save_json(str(json_path))
        
        logger.info(f"✅ Dataset Drift Report: {html_path}")
        reports_generated += 1
        
    except Exception as e:
        logger.error(f"❌ Dataset Drift failed: {e}")
    
    # 2. Column Summary
    logger.info("\n2. Generating Column Summary Report...")
    try:
        report = Report(metrics=[
            DatasetSummaryMetric(),
        ])
        report.run(reference_data=reference_data, current_data=current_data)
        
        html_path = output_path / f"column_summary_{timestamp}.html"
        json_path = output_path / f"column_summary_{timestamp}.json"
        
        report.save_html(str(html_path))
        report.save_json(str(json_path))
        
        logger.info(f"✅ Column Summary Report: {html_path}")
        reports_generated += 1
        
    except Exception as e:
        logger.error(f"❌ Column Summary failed: {e}")
    
    # 3. Data Quality
    logger.info("\n3. Generating Data Quality Report...")
    try:
        report = Report(metrics=[
            DataQualityMetricsCalculatorMetric(),
        ])
        report.run(reference_data=reference_data, current_data=current_data)
        
        html_path = output_path / f"data_quality_{timestamp}.html"
        json_path = output_path / f"data_quality_{timestamp}.json"
        
        report.save_html(str(html_path))
        report.save_json(str(json_path))
        
        logger.info(f"✅ Data Quality Report: {html_path}")
        reports_generated += 1
        
    except Exception as e:
        logger.error(f"❌ Data Quality failed: {e}")
    
    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("MONITORING SUMMARY")
    logger.info("=" * 70)
    logger.info(f"📊 Reports generated: {reports_generated}")
    logger.info(f"📁 Output directory: {output_path}")
    logger.info(f"📄 Total files: {len(list(output_path.glob('*')))} ")
    logger.info("=" * 70)
    
    return {
        "status": "success",
        "output_dir": str(output_path),
        "reports_count": reports_generated
    }


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Evidently AI Monitoring")
    parser.add_argument("--reference", default="data/train.csv", help="Reference data")
    parser.add_argument("--current", default="data/test.csv", help="Current data")
    parser.add_argument("--output", default="reports/evidently", help="Output directory")
    
    args = parser.parse_args()
    
    result = run_monitoring(args.reference, args.current, args.output)
    print(f"\n✅ Monitoring complete!")
