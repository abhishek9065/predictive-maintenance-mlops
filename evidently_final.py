"""
Evidently AI - Final Working Monitoring Script
Uses Evidently 0.7.15 with correct API
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
import logging

try:
    from evidently import Report
    from evidently.metrics import (
        ColumnCount,
        DuplicatedRowCount,
        DatasetMissingValueCount,
        DatasetCorrelations,
        DriftedColumnsCount,
        ValueDrift,
    )
    EVIDENTLY_OK = True
except ImportError as e:
    EVIDENTLY_OK = False
    print(f"Evidently not available: {e}")

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def run_monitoring(reference_path: str, current_path: str, output_dir: str = "reports/evidently"):
    """Run Evidently AI monitoring and drift detection"""
    
    print("=" * 70)
    print("EVIDENTLY AI - MODEL MONITORING & DRIFT DETECTION")
    print("=" * 70)
    
    if not EVIDENTLY_OK:
        print("❌ Evidently AI not available. Skipping...")
        return {"status": "skipped"}
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Load data
    print(f"\nLoading reference data: {reference_path}")
    reference_data = pd.read_csv(reference_path)
    
    print(f"Loading current data: {current_path}")
    current_data = pd.read_csv(current_path)
    
    print(f"Reference shape: {reference_data.shape}")
    print(f"Current shape: {current_data.shape}")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    reports_count = 0
    
    # 1. Data Quality Report
    print("\n1. Generating Data Quality Report...")
    try:
        report = Report(metrics=[
            ColumnCount(),
            DuplicatedRowCount(),
            DatasetMissingValueCount(),
        ])
        
        report.run(reference_data=reference_data, current_data=current_data)
        
        html_path = output_path / f"data_quality_{timestamp}.html"
        json_path = output_path / f"data_quality_{timestamp}.json"
        
        report.save_html(str(html_path))
        report.save_json(str(json_path))
        
        print(f"✅ Data Quality Report saved: {html_path}")
        reports_count += 1
        
    except Exception as e:
        print(f"❌ Data Quality Report failed: {e}")
    
    # 2. Data Correlations
    print("\n2. Generating Correlation Analysis...")
    try:
        report = Report(metrics=[
            DatasetCorrelations(),
        ])
        
        report.run(reference_data=reference_data, current_data=current_data)
        
        html_path = output_path / f"correlations_{timestamp}.html"
        json_path = output_path / f"correlations_{timestamp}.json"
        
        report.save_html(str(html_path))
        report.save_json(str(json_path))
        
        print(f"✅ Correlation Report saved: {html_path}")
        reports_count += 1
        
    except Exception as e:
        print(f"❌ Correlation Report failed: {e}")
    
    # 3. Drift Detection
    print("\n3. Generating Drift Detection Report...")
    try:
        # Create drift reports for each feature
        feature_columns = ['temperature', 'vibration', 'pressure', 'humidity', 'rpm']
        
        drift_metrics = [DriftedColumnsCount()]
        for col in feature_columns:
            drift_metrics.append(ValueDrift(column_name=col))
        
        report = Report(metrics=drift_metrics)
        
        report.run(reference_data=reference_data, current_data=current_data)
        
        html_path = output_path / f"drift_detection_{timestamp}.html"
        json_path = output_path / f"drift_detection_{timestamp}.json"
        
        report.save_html(str(html_path))
        report.save_json(str(json_path))
        
        print(f"✅ Drift Detection Report saved: {html_path}")
        reports_count += 1
        
    except Exception as e:
        print(f"❌ Drift Detection Report failed: {e}")
    
    # Summary
    print("\n" + "=" * 70)
    print("MONITORING SUMMARY")
    print("=" * 70)
    print(f"✅ Reports generated: {reports_count}")
    print(f"📁 Output directory: {output_path}")
    print(f"📄 HTML files: {len(list(output_path.glob('*.html')))}")
    print(f"📄 JSON files: {len(list(output_path.glob('*.json')))}")
    print("=" * 70)
    
    return {
        "status": "success",
        "output_dir": str(output_path),
        "reports_count": reports_count
    }


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Evidently AI Monitoring")
    parser.add_argument("--reference", default="data/train.csv")
    parser.add_argument("--current", default="data/test.csv")
    parser.add_argument("--output", default="reports/evidently")
    
    args = parser.parse_args()
    
    result = run_monitoring(args.reference, args.current, args.output)
    
    if result['status'] == 'success':
        print(f"\n🎉 Monitoring complete! Check {result['output_dir']} for reports.")
    else:
        print(f"\n⚠️  Monitoring status: {result['status']}")
