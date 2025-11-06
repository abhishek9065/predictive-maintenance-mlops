"""
Custom ML Monitoring & Explainability
Production-ready monitoring without complex dependencies
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import json
import joblib
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    classification_report, confusion_matrix, 
    accuracy_score, precision_recall_fscore_support
)

class ProductionMonitor:
    """Production ML model monitoring and explainability"""
    
    def __init__(self, reference_data_path="data/train.csv", output_dir="reports/monitoring"):
        """
        Initialize monitor
        
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
        
        self.feature_cols = ['temperature', 'vibration', 'pressure', 'rpm', 'current']
        self.target_col = 'target'
        
        # Calculate reference statistics
        self.ref_stats = self.calculate_statistics(self.reference_data)
        
    def calculate_statistics(self, data):
        """Calculate statistics for data"""
        stats = {}
        for col in self.feature_cols:
            stats[col] = {
                'mean': float(data[col].mean()),
                'std': float(data[col].std()),
                'min': float(data[col].min()),
                'max': float(data[col].max()),
                'q25': float(data[col].quantile(0.25)),
                'q50': float(data[col].quantile(0.50)),
                'q75': float(data[col].quantile(0.75))
            }
        
        if self.target_col in data.columns:
            stats['target_distribution'] = {
                'normal': int((data[self.target_col] == 0).sum()),
                'failure': int((data[self.target_col] == 1).sum()),
                'failure_rate': float(data[self.target_col].mean())
            }
        
        return stats
    
    def detect_data_drift(self, current_data):
        """
        Detect data drift using statistical methods
        
        Args:
            current_data: Current production data
        
        Returns:
            Drift detection results
        """
        print("\n" + "="*80)
        print("  📊 DETECTING DATA DRIFT")
        print("="*80)
        
        current_stats = self.calculate_statistics(current_data)
        drift_results = {}
        
        for col in self.feature_cols:
            ref_mean = self.ref_stats[col]['mean']
            ref_std = self.ref_stats[col]['std']
            curr_mean = current_stats[col]['mean']
            curr_std = current_stats[col]['std']
            
            # Calculate drift metrics
            mean_diff_pct = abs((curr_mean - ref_mean) / ref_mean * 100) if ref_mean != 0 else 0
            std_diff_pct = abs((curr_std - ref_std) / ref_std * 100) if ref_std != 0 else 0
            
            # Drift detected if mean shifts > 20% or std changes > 50%
            drift_detected = mean_diff_pct > 20 or std_diff_pct > 50
            
            drift_results[col] = {
                'reference_mean': ref_mean,
                'current_mean': curr_mean,
                'mean_diff_pct': mean_diff_pct,
                'reference_std': ref_std,
                'current_std': curr_std,
                'std_diff_pct': std_diff_pct,
                'drift_detected': drift_detected
            }
        
        # Summary
        drifted_features = [col for col, res in drift_results.items() if res['drift_detected']]
        
        print(f"\n📈 Data Drift Analysis:")
        print(f"   Total Features: {len(self.feature_cols)}")
        print(f"   Drifted Features: {len(drifted_features)}")
        print(f"   Drift Status: {'🔴 DRIFT DETECTED' if drifted_features else '🟢 NO DRIFT'}")
        
        if drifted_features:
            print(f"\n   🔴 Features with Drift:")
            for col in drifted_features:
                print(f"      {col}: Mean shift {drift_results[col]['mean_diff_pct']:.1f}%")
        else:
            print(f"\n   🟢 All features within expected range")
        
        return drift_results
    
    def evaluate_model_performance(self, current_data, predictions):
        """
        Evaluate model performance
        
        Args:
            current_data: Current data with true labels
            predictions: Model predictions
        
        Returns:
            Performance metrics
        """
        print("\n" + "="*80)
        print("  📈 EVALUATING MODEL PERFORMANCE")
        print("="*80)
        
        if self.target_col not in current_data.columns:
            print("   ⚠️  No target column found, skipping performance evaluation")
            return None
        
        y_true = current_data[self.target_col].values
        y_pred = predictions
        
        # Calculate metrics
        accuracy = accuracy_score(y_true, y_pred)
        precision, recall, f1, _ = precision_recall_fscore_support(y_true, y_pred, average='binary')
        
        # Confusion matrix
        cm = confusion_matrix(y_true, y_pred)
        
        metrics = {
            'accuracy': float(accuracy),
            'precision': float(precision),
            'recall': float(recall),
            'f1_score': float(f1),
            'confusion_matrix': cm.tolist(),
            'classification_report': classification_report(y_true, y_pred, output_dict=True)
        }
        
        print(f"\n📊 Model Performance:")
        print(f"   Accuracy:  {accuracy*100:.2f}%")
        print(f"   Precision: {precision*100:.2f}%")
        print(f"   Recall:    {recall*100:.2f}%")
        print(f"   F1 Score:  {f1*100:.2f}%")
        
        print(f"\n📋 Confusion Matrix:")
        print(f"              Predicted")
        print(f"              Normal  Failure")
        print(f"   Actual Normal   {cm[0][0]:4d}    {cm[0][1]:4d}")
        print(f"          Failure  {cm[1][0]:4d}    {cm[1][1]:4d}")
        
        return metrics
    
    def analyze_predictions(self, features, predictions, probabilities):
        """Analyze predictions in detail"""
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
        
        # Find high-risk predictions
        for i, (pred, prob) in enumerate(zip(predictions, probabilities)):
            if pred == 1 and prob[1] > 0.8:
                results['high_risk_samples'].append({
                    'index': int(i),
                    'confidence': float(prob[1]),
                    'temperature': float(features.iloc[i]['temperature']),
                    'vibration': float(features.iloc[i]['vibration']),
                    'pressure': float(features.iloc[i]['pressure']),
                    'rpm': float(features.iloc[i]['rpm']),
                    'current': float(features.iloc[i]['current'])
                })
        
        print(f"\n📊 Prediction Summary:")
        print(f"   Total: {results['total_predictions']}")
        print(f"   🟢 Normal: {results['normal_count']} ({results['normal_count']/results['total_predictions']*100:.1f}%)")
        print(f"   🔴 Failure: {results['failure_count']} ({results['failure_count']/results['total_predictions']*100:.1f}%)")
        print(f"   📈 Avg Confidence: {results['avg_confidence']*100:.1f}%")
        print(f"   ⚠️  Low Confidence (<70%): {results['low_confidence_count']}")
        print(f"   🚨 High Risk (Failure >80%): {len(results['high_risk_samples'])}")
        
        return results
    
    def generate_visualizations(self, current_data, predictions, probabilities, timestamp):
        """Generate monitoring visualizations"""
        print("\n📊 Generating visualizations...")
        
        fig, axes = plt.subplots(2, 3, figsize=(15, 10))
        fig.suptitle('Production Model Monitoring Dashboard', fontsize=16, fontweight='bold')
        
        # 1. Feature distributions comparison
        for idx, col in enumerate(self.feature_cols):
            if idx < 5:
                ax = axes[idx // 3, idx % 3]
                
                # Plot reference and current distributions
                ax.hist(self.reference_data[col], bins=30, alpha=0.5, label='Reference', color='blue')
                ax.hist(current_data[col], bins=30, alpha=0.5, label='Current', color='orange')
                ax.set_xlabel(col.capitalize())
                ax.set_ylabel('Frequency')
                ax.legend()
                ax.grid(True, alpha=0.3)
        
        # 6. Prediction confidence distribution
        ax = axes[1, 2]
        confidences = np.max(probabilities, axis=1)
        ax.hist(confidences, bins=20, color='green', alpha=0.7)
        ax.axvline(x=0.7, color='red', linestyle='--', label='Low Confidence Threshold')
        ax.set_xlabel('Prediction Confidence')
        ax.set_ylabel('Count')
        ax.set_title('Confidence Distribution')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # Save plot
        plot_path = self.output_dir / f"monitoring_dashboard_{timestamp}.png"
        plt.savefig(plot_path, dpi=100, bbox_inches='tight')
        plt.close()
        
        print(f"   ✅ Dashboard saved: {plot_path.name}")
        
        return str(plot_path)
    
    def generate_html_report(self, summary, timestamp):
        """Generate HTML monitoring report"""
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>ML Monitoring Report - {timestamp}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: auto; background: white; padding: 30px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
        h2 {{ color: #34495e; margin-top: 30px; border-bottom: 2px solid #ecf0f1; padding-bottom: 5px; }}
        .metric {{ background: #ecf0f1; padding: 15px; margin: 10px 0; border-radius: 5px; }}
        .metric strong {{ color: #2c3e50; }}
        .success {{ color: #27ae60; }}
        .warning {{ color: #f39c12; }}
        .error {{ color: #e74c3c; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border: 1px solid #ddd; }}
        th {{ background: #3498db; color: white; }}
        tr:nth-child(even) {{ background: #f9f9f9; }}
        .dashboard-image {{ width: 100%; max-width: 1000px; margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 ML Model Monitoring Report</h1>
        <p><strong>Generated:</strong> {summary['timestamp']}</p>
        
        <h2>📊 Data Overview</h2>
        <div class="metric">
            <strong>Reference Data:</strong> {summary['reference_data_samples']} samples<br>
            <strong>Current Data:</strong> {summary['current_data_samples']} samples
        </div>
        
        <h2>🎯 Prediction Summary</h2>
        <div class="metric">
            <strong>Total Predictions:</strong> {summary['predictions']['total']}<br>
            <strong class="success">Normal Operations:</strong> {summary['predictions']['normal']} ({summary['predictions']['normal']/summary['predictions']['total']*100:.1f}%)<br>
            <strong class="error">Failures Detected:</strong> {summary['predictions']['failure']} ({summary['predictions']['failure']/summary['predictions']['total']*100:.1f}%)<br>
            <strong>Failure Rate:</strong> {summary['predictions']['failure_rate']*100:.1f}%
        </div>
        
        <h2>📈 Model Performance</h2>
        """
        
        if summary.get('performance'):
            perf = summary['performance']
            html_content += f"""
        <div class="metric">
            <strong>Accuracy:</strong> {perf['accuracy']*100:.2f}%<br>
            <strong>Precision:</strong> {perf['precision']*100:.2f}%<br>
            <strong>Recall:</strong> {perf['recall']*100:.2f}%<br>
            <strong>F1 Score:</strong> {perf['f1_score']*100:.2f}%
        </div>
            """
        
        html_content += f"""
        <h2>🔍 Prediction Quality</h2>
        <div class="metric">
            <strong>Average Confidence:</strong> {summary['quality']['avg_confidence']*100:.1f}%<br>
            <strong class="warning">Low Confidence Predictions:</strong> {summary['quality']['low_confidence_count']}<br>
            <strong class="error">High Risk Samples:</strong> {summary['quality']['high_risk_count']}
        </div>
        
        <h2>📊 Data Drift Analysis</h2>
        <table>
            <tr>
                <th>Feature</th>
                <th>Reference Mean</th>
                <th>Current Mean</th>
                <th>Mean Shift %</th>
                <th>Status</th>
            </tr>
        """
        
        for feature, drift in summary['drift'].items():
            status = '<span class="error">⚠️ DRIFT</span>' if drift['drift_detected'] else '<span class="success">✅ OK</span>'
            html_content += f"""
            <tr>
                <td>{feature}</td>
                <td>{drift['reference_mean']:.2f}</td>
                <td>{drift['current_mean']:.2f}</td>
                <td>{drift['mean_diff_pct']:.1f}%</td>
                <td>{status}</td>
            </tr>
            """
        
        html_content += """
        </table>
        
        <h2>📊 Monitoring Dashboard</h2>
        <img src="{dashboard_image}" class="dashboard-image" alt="Monitoring Dashboard">
        
    </div>
</body>
</html>
        """
        
        report_path = self.output_dir / f"monitoring_report_{timestamp}.html"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"   ✅ HTML report saved: {report_path.name}")
        return str(report_path)
    
    def generate_comprehensive_report(self, current_data_path="data/test.csv", 
                                     model_path="models/production_model.pkl"):
        """Generate comprehensive monitoring report"""
        print("\n" + "="*100)
        print("  🎯 COMPREHENSIVE MODEL MONITORING & EXPLAINABILITY")
        print("="*100)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Load data and model
        print(f"\n📂 Loading current data from: {current_data_path}")
        current_data = pd.read_csv(current_data_path)
        print(f"   ✅ Loaded {len(current_data)} samples")
        
        print(f"\n🤖 Loading model from: {model_path}")
        model = joblib.load(model_path)
        print(f"   ✅ Model loaded")
        
        # Make predictions
        X_current = current_data[self.feature_cols]
        print(f"\n🔮 Making predictions...")
        predictions = model.predict(X_current)
        probabilities = model.predict_proba(X_current)
        print(f"   ✅ {len(predictions)} predictions complete")
        
        # Run analyses
        drift_results = self.detect_data_drift(current_data)
        performance_metrics = self.evaluate_model_performance(current_data, predictions)
        prediction_analysis = self.analyze_predictions(X_current, predictions, probabilities)
        dashboard_path = self.generate_visualizations(current_data, predictions, probabilities, timestamp)
        
        # Create summary
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
            'performance': performance_metrics,
            'drift': drift_results,
            'quality': {
                'avg_confidence': prediction_analysis['avg_confidence'],
                'low_confidence_count': prediction_analysis['low_confidence_count'],
                'high_risk_count': len(prediction_analysis['high_risk_samples'])
            },
            'dashboard_path': dashboard_path
        }
        
        # Save JSON summary
        json_path = self.output_dir / f"monitoring_summary_{timestamp}.json"
        with open(json_path, 'w') as f:
            json.dump(summary, f, indent=2)
        print(f"\n📄 Summary saved: {json_path.name}")
        
        # Generate HTML report
        html_path = self.generate_html_report(summary, timestamp)
        
        print("\n" + "="*100)
        print("  ✅ COMPREHENSIVE MONITORING COMPLETE")
        print("="*100)
        print(f"\n📁 All reports saved to: {self.output_dir}")
        print(f"   📊 HTML Report: {Path(html_path).name}")
        print(f"   📈 Dashboard: {Path(dashboard_path).name}")
        print(f"   📄 JSON Summary: {json_path.name}")
        
        return summary

def main():
    """Main function"""
    monitor = ProductionMonitor(
        reference_data_path="data/train.csv",
        output_dir="reports/monitoring"
    )
    
    summary = monitor.generate_comprehensive_report(
        current_data_path="data/test.csv",
        model_path="models/production_model.pkl"
    )
    
    print("\n" + "="*100)
    print("  🎉 MONITORING & EXPLAINABILITY COMPLETE!")
    print("="*100)
    print("\n  💡 Next Steps:")
    print("     1. Open HTML report for detailed analysis")
    print("     2. Review data drift metrics")
    print("     3. Check model performance trends")
    print("     4. Investigate high-risk predictions")
    print("     5. Set up automated monitoring")
    print("\n" + "="*100)

if __name__ == "__main__":
    main()
