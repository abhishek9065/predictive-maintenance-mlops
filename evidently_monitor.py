"""
Evidently AI Monitoring & Explainability (v0.7.15)
Model monitoring, data drift detection, and prediction analysis
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import json
import joblib

from evidently.pipeline.column_mapping import ColumnMapping
from evidently.dashboard import Dashboard
from evidently.dashboard.tabs import (
    DataDriftTab,
    CatTargetDriftTab,
    ClassificationPerformanceTab,
    ProbClassificationPerformanceTab
)

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
        self.column_mapping = ColumnMapping()
        self.column_mapping.target = 'target'
        self.column_mapping.prediction = 'prediction'
        self.column_mapping.numerical_features = ['temperature', 'vibration', 'pressure', 'rpm', 'current']
        
        print(f"   📊 Features: {self.column_mapping.numerical_features}")
    
    def generate_data_drift_dashboard(self, current_data, save_html=True):
        """
        Generate data drift dashboard
        
        Args:
            current_data: Current production data
            save_html: Save HTML dashboard
        
        Returns:
            Dashboard object
        """
        print("\n" + "="*80)
        print("  📊 GENERATING DATA DRIFT DASHBOARD")
        print("="*80)
        
        # Create dashboard
        dashboard = Dashboard(tabs=[DataDriftTab()])
        
        # Run dashboard
        dashboard.calculate(
            reference_data=self.reference_data,
            current_data=current_data,
            column_mapping=self.column_mapping
        )
        
        # Save HTML dashboard
        if save_html:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            dashboard_path = self.output_dir / f"data_drift_dashboard_{timestamp}.html"
            dashboard.save(str(dashboard_path))
            print(f"\n✅ Dashboard saved: {dashboard_path}")
        
        print(f"\n📈 Data Drift Dashboard Generated")
        print(f"   Reference samples: {len(self.reference_data)}")
        print(f"   Current samples: {len(current_data)}")
        
        return dashboard
    
    def generate_classification_performance_dashboard(self, current_data_with_predictions, save_html=True):
        """
        Generate classification performance dashboard
        
        Args:
            current_data_with_predictions: Current data with predictions
            save_html: Save HTML dashboard
        
        Returns:
            Dashboard object
        """
        print("\n" + "="*80)
        print("  📈 GENERATING CLASSIFICATION PERFORMANCE DASHBOARD")
        print("="*80)
        
        # Add predictions to reference data (using actual targets as predictions for baseline)
        ref_data_with_pred = self.reference_data.copy()
        if 'prediction' not in ref_data_with_pred.columns:
            ref_data_with_pred['prediction'] = ref_data_with_pred['target']
        
        # Create dashboard
        dashboard = Dashboard(tabs=[ClassificationPerformanceTab()])
        
        # Run dashboard
        dashboard.calculate(
            reference_data=ref_data_with_pred,
            current_data=current_data_with_predictions,
            column_mapping=self.column_mapping
        )
        
        # Save HTML dashboard
        if save_html:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            dashboard_path = self.output_dir / f"classification_performance_{timestamp}.html"
            dashboard.save(str(dashboard_path))
            print(f"\n✅ Dashboard saved: {dashboard_path}")
        
        print(f"\n📊 Classification Performance Dashboard Generated")
        
        return dashboard
    
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
                print(f"         Temp: {sample['features']['temperature']:.1f}°C, "
                      f"Vib: {sample['features']['vibration']:.2f}")
        
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
        
        # Add predictions to current data
        current_data_with_pred = current_data.copy()
        current_data_with_pred['prediction'] = predictions
        
        # Generate reports
        reports = {}
        
        # 1. Data Drift Dashboard
        reports['data_drift'] = self.generate_data_drift_dashboard(current_data)
        
        # 2. Classification Performance Dashboard
        if 'target' in current_data.columns:
            reports['classification_performance'] = self.generate_classification_performance_dashboard(
                current_data_with_pred
            )
        
        # 3. Prediction Analysis
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
                'failure': int(np.sum(predictions == 1)),
                'failure_rate': float(np.mean(predictions))
            },
            'performance': {
                'avg_confidence': float(np.mean(np.max(probabilities, axis=1))),
                'low_confidence_count': int(np.sum(np.max(probabilities, axis=1) < 0.7))
            },
            'reports_generated': ['data_drift', 'classification_performance', 'prediction_analysis']
        }
        
        summary_path = self.output_dir / f"monitoring_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print("\n" + "="*100)
        print("  ✅ COMPREHENSIVE MONITORING COMPLETE")
        print("="*100)
        print(f"\n📁 All reports saved to: {self.output_dir}")
        print(f"   📊 HTML Dashboards: Open in browser for interactive analysis")
        print(f"   📄 Summary: {summary_path.name}")
        print(f"\n💡 Tip: Open the HTML files in your browser to explore interactive visualizations!")
        
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
    print("     1. Open HTML dashboards in browser for interactive analysis")
    print("     2. Review data drift patterns")
    print("     3. Check model performance trends")
    print("     4. Investigate high-risk predictions")
    print("     5. Set up automated monitoring in production")
    print("\n" + "="*100)

if __name__ == "__main__":
    main()
