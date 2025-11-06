"""
Evidently AI Monitoring & Explainability
Model monitoring, data drift detection, and prediction analysis
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import json

from evidently.pipeline.column_mapping import ColumnMapping
from evidently.dashboard import Dashboard
from evidently.dashboard.tabs import DataDriftTab, CatTargetDriftTab, ClassificationPerformanceTab
from evidently.model_profile import Profile
from evidently.model_profile.sections import DataDriftProfileSection, ClassificationPerformanceProfileSection

class EvidentlyMonitor:
    """Evidently AI monitoring for predictive maintenance"""
    
    def __init__(self, reference_data_path="data/train.csv", output_dir="reports/evidently"):
        """
        Initialize Evidently monitor
        
        Args:
            reference_data_path: Path to reference (training) data
            output_dir: Directory to save reports
        """
        self.reference_data_path = Path(reference_data_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load reference data
        print("📂 Loading reference data...")
        self.reference_data = pd.read_csv(self.reference_data_path)
        print(f"   ✅ Loaded {len(self.reference_data)} samples")
        
        # Define column mapping
        self.column_mapping = ColumnMapping(
            target='target',
            prediction=None,
            numerical_features=['temperature', 'vibration', 'pressure', 'rpm', 'current'],
            categorical_features=[]
        )
        
        print(f"   📊 Features: {self.column_mapping.numerical_features}")
    
    def generate_data_drift_report(self, current_data, save_html=True):
        """
        Generate data drift report
        
        Args:
            current_data: Current production data
            save_html: Save HTML report
        
        Returns:
            Report object
        """
        print("\n" + "="*80)
        print("  📊 GENERATING DATA DRIFT REPORT")
        print("="*80)
        
        # Create report
        report = Report(metrics=[
            DataDriftPreset(),
        ])
        
        # Run report
        report.run(
            reference_data=self.reference_data,
            current_data=current_data,
            column_mapping=self.column_mapping
        )
        
        # Save HTML report
        if save_html:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_path = self.output_dir / f"data_drift_report_{timestamp}.html"
            report.save_html(str(report_path))
            print(f"\n✅ Report saved: {report_path}")
        
        # Get drift metrics
        report_dict = report.as_dict()
        drift_detected = report_dict['metrics'][0]['result']['dataset_drift']
        
        print(f"\n📈 Data Drift Analysis:")
        print(f"   Dataset Drift Detected: {'🔴 YES' if drift_detected else '🟢 NO'}")
        
        # Feature-level drift
        feature_drift = report_dict['metrics'][0]['result'].get('drift_by_columns', {})
        print(f"\n   Feature-level Drift:")
        for feature, drift_info in feature_drift.items():
            if feature in self.column_mapping.numerical_features:
                drifted = drift_info.get('drift_detected', False)
                status = "🔴 DRIFT" if drifted else "🟢 OK"
                print(f"      {feature}: {status}")
        
        return report
    
    def generate_data_quality_report(self, current_data, save_html=True):
        """
        Generate data quality report
        
        Args:
            current_data: Current production data
            save_html: Save HTML report
        
        Returns:
            Report object
        """
        print("\n" + "="*80)
        print("  🔍 GENERATING DATA QUALITY REPORT")
        print("="*80)
        
        # Create report
        report = Report(metrics=[
            DataQualityPreset(),
        ])
        
        # Run report
        report.run(
            reference_data=self.reference_data,
            current_data=current_data,
            column_mapping=self.column_mapping
        )
        
        # Save HTML report
        if save_html:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_path = self.output_dir / f"data_quality_report_{timestamp}.html"
            report.save_html(str(report_path))
            print(f"\n✅ Report saved: {report_path}")
        
        # Get quality metrics
        report_dict = report.as_dict()
        
        print(f"\n📊 Data Quality Summary:")
        print(f"   Current Data Samples: {len(current_data)}")
        print(f"   Reference Data Samples: {len(self.reference_data)}")
        
        return report
    
    def generate_model_performance_report(self, current_data, predictions, save_html=True):
        """
        Generate model performance report with predictions
        
        Args:
            current_data: Current production data
            predictions: Model predictions
            save_html: Save HTML report
        
        Returns:
            Report object
        """
        print("\n" + "="*80)
        print("  📈 GENERATING MODEL PERFORMANCE REPORT")
        print("="*80)
        
        # Add predictions to data
        current_with_pred = current_data.copy()
        current_with_pred['prediction'] = predictions
        
        ref_data_with_pred = self.reference_data.copy()
        
        # Update column mapping
        column_mapping = ColumnMapping(
            target='target',
            prediction='prediction',
            numerical_features=['temperature', 'vibration', 'pressure', 'rpm', 'current'],
            categorical_features=[]
        )
        
        # Create report
        report = Report(metrics=[
            ClassificationQualityMetric(),
            ClassificationConfusionMatrix(),
            ClassificationQualityByClass(),
        ])
        
        # Run report
        report.run(
            reference_data=ref_data_with_pred,
            current_data=current_with_pred,
            column_mapping=column_mapping
        )
        
        # Save HTML report
        if save_html:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_path = self.output_dir / f"model_performance_report_{timestamp}.html"
            report.save_html(str(report_path))
            print(f"\n✅ Report saved: {report_path}")
        
        # Get performance metrics
        report_dict = report.as_dict()
        
        print(f"\n📊 Model Performance:")
        metrics = report_dict['metrics'][0]['result']['current']
        print(f"   Accuracy: {metrics.get('accuracy', 0)*100:.2f}%")
        print(f"   Precision: {metrics.get('precision', 0)*100:.2f}%")
        print(f"   Recall: {metrics.get('recall', 0)*100:.2f}%")
        print(f"   F1 Score: {metrics.get('f1', 0)*100:.2f}%")
        
        return report
    
    def run_data_tests(self, current_data):
        """
        Run automated data quality tests
        
        Args:
            current_data: Current production data
        
        Returns:
            TestSuite object
        """
        print("\n" + "="*80)
        print("  🧪 RUNNING DATA QUALITY TESTS")
        print("="*80)
        
        # Create test suite
        tests = TestSuite(tests=[
            TestNumberOfColumns(),
            TestNumberOfRows(gt=10),
            TestColumnsType(),
            TestNumberOfMissingValues(),
            TestNumberOfDuplicatedRows(),
            TestNumberOfDuplicatedColumns(),
            TestShareOfDriftedColumns(lt=0.5),
        ])
        
        # Run tests
        tests.run(
            reference_data=self.reference_data,
            current_data=current_data,
            column_mapping=self.column_mapping
        )
        
        # Save HTML report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = self.output_dir / f"data_tests_{timestamp}.html"
        tests.save_html(str(report_path))
        print(f"\n✅ Test report saved: {report_path}")
        
        # Get test results
        test_results = tests.as_dict()
        total_tests = test_results['summary']['total_tests']
        passed_tests = test_results['summary']['success_tests']
        failed_tests = test_results['summary']['failed_tests']
        
        print(f"\n📋 Test Results:")
        print(f"   Total Tests: {total_tests}")
        print(f"   ✅ Passed: {passed_tests}")
        print(f"   ❌ Failed: {failed_tests}")
        print(f"   Success Rate: {passed_tests/total_tests*100:.1f}%")
        
        return tests
    
    def analyze_predictions(self, features, predictions, probabilities):
        """
        Analyze individual predictions
        
        Args:
            features: Input features DataFrame
            predictions: Model predictions
            probabilities: Prediction probabilities
        
        Returns:
            Analysis results
        """
        print("\n" + "="*80)
        print("  🔍 ANALYZING PREDICTIONS")
        print("="*80)
        
        results = {
            'total_predictions': len(predictions),
            'normal_count': int(np.sum(predictions == 0)),
            'failure_count': int(np.sum(predictions == 1)),
            'avg_confidence': float(np.mean(np.max(probabilities, axis=1))),
            'low_confidence_count': int(np.sum(np.max(probabilities, axis=1) < 0.7)),
            'high_risk_samples': []
        }
        
        # Find high-risk predictions (failure with high confidence)
        for i, (pred, prob) in enumerate(zip(predictions, probabilities)):
            if pred == 1 and prob[1] > 0.8:  # Failure with >80% confidence
                results['high_risk_samples'].append({
                    'index': int(i),
                    'confidence': float(prob[1]),
                    'features': features.iloc[i].to_dict()
                })
        
        print(f"\n📊 Prediction Analysis:")
        print(f"   Total Predictions: {results['total_predictions']}")
        print(f"   🟢 Normal: {results['normal_count']} ({results['normal_count']/results['total_predictions']*100:.1f}%)")
        print(f"   🔴 Failure: {results['failure_count']} ({results['failure_count']/results['total_predictions']*100:.1f}%)")
        print(f"   📈 Avg Confidence: {results['avg_confidence']*100:.1f}%")
        print(f"   ⚠️  Low Confidence (<70%): {results['low_confidence_count']}")
        print(f"   🚨 High Risk Samples: {len(results['high_risk_samples'])}")
        
        if results['high_risk_samples']:
            print(f"\n   🔴 High Risk Alerts:")
            for sample in results['high_risk_samples'][:5]:  # Show top 5
                print(f"      Sample {sample['index']}: {sample['confidence']*100:.1f}% failure risk")
        
        return results
    
    def generate_comprehensive_report(self, current_data_path="data/test.csv", 
                                     model_path="models/production_model.pkl"):
        """
        Generate comprehensive monitoring report
        
        Args:
            current_data_path: Path to current/test data
            model_path: Path to model
        
        Returns:
            Dictionary with all reports
        """
        print("\n" + "="*100)
        print("  🎯 COMPREHENSIVE EVIDENTLY AI MONITORING & EXPLAINABILITY")
        print("="*100)
        
        # Load current data
        print(f"\n📂 Loading current data from: {current_data_path}")
        current_data = pd.read_csv(current_data_path)
        print(f"   ✅ Loaded {len(current_data)} samples")
        
        # Load model and make predictions
        print(f"\n🤖 Loading model from: {model_path}")
        import joblib
        model = joblib.load(model_path)
        print(f"   ✅ Model loaded")
        
        # Prepare features
        feature_cols = ['temperature', 'vibration', 'pressure', 'rpm', 'current']
        X_current = current_data[feature_cols]
        
        # Make predictions
        print(f"\n🔮 Making predictions on {len(X_current)} samples...")
        predictions = model.predict(X_current)
        probabilities = model.predict_proba(X_current)
        print(f"   ✅ Predictions complete")
        
        # Generate reports
        reports = {}
        
        # 1. Data Drift Report
        reports['data_drift'] = self.generate_data_drift_report(current_data)
        
        # 2. Data Quality Report
        reports['data_quality'] = self.generate_data_quality_report(current_data)
        
        # 3. Model Performance Report
        if 'target' in current_data.columns:
            reports['model_performance'] = self.generate_model_performance_report(
                current_data, predictions
            )
        
        # 4. Data Quality Tests
        reports['tests'] = self.run_data_tests(current_data)
        
        # 5. Prediction Analysis
        reports['prediction_analysis'] = self.analyze_predictions(
            X_current, predictions, probabilities
        )
        
        # Save summary
        summary = {
            'timestamp': datetime.now().isoformat(),
            'reference_data_samples': len(self.reference_data),
            'current_data_samples': len(current_data),
            'predictions': {
                'total': int(len(predictions)),
                'normal': int(np.sum(predictions == 0)),
                'failure': int(np.sum(predictions == 1))
            },
            'reports_generated': list(reports.keys())
        }
        
        summary_path = self.output_dir / f"monitoring_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print("\n" + "="*100)
        print("  ✅ COMPREHENSIVE MONITORING COMPLETE")
        print("="*100)
        print(f"\n📁 All reports saved to: {self.output_dir}")
        print(f"   📊 HTML Reports: Open in browser for interactive analysis")
        print(f"   📄 Summary: {summary_path}")
        
        return reports

def main():
    """Main function to demonstrate Evidently AI monitoring"""
    
    # Create monitor
    monitor = EvidentlyMonitor(
        reference_data_path="data/train.csv",
        output_dir="reports/evidently"
    )
    
    # Generate comprehensive report
    reports = monitor.generate_comprehensive_report(
        current_data_path="data/test.csv",
        model_path="models/production_model.pkl"
    )
    
    print("\n" + "="*100)
    print("  🎉 EVIDENTLY AI MONITORING COMPLETE!")
    print("="*100)
    print("\n  📊 Next Steps:")
    print("     1. Open HTML reports in browser for interactive analysis")
    print("     2. Review data drift and quality metrics")
    print("     3. Check model performance trends")
    print("     4. Investigate high-risk predictions")
    print("     5. Set up automated monitoring in production")
    print("\n" + "="*100)

if __name__ == "__main__":
    main()
