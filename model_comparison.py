"""
MLflow Model Comparison Dashboard
Visualize and compare model performance across experiments
"""

import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from datetime import datetime


def load_experiment_report():
    """Load the MLflow experiment report"""
    report_path = Path("mlflow_experiment_report.json")
    
    if not report_path.exists():
        print("[ERROR] Experiment report not found. Run mlflow_advanced.py first.")
        return None
    
    with open(report_path, 'r') as f:
        return json.load(f)


def create_model_comparison_table(report):
    """Create a comparison table of all models"""
    
    print("\n" + "="*100)
    print("MODEL PERFORMANCE COMPARISON")
    print("="*100)
    
    # Extract data
    models_data = []
    for run in report['runs']:
        if run['status'] == 'FINISHED':
            metrics = run['metrics']
            params = run['params']
            tags = run['tags']
            
            models_data.append({
                'Model': tags.get('model_type', params.get('model_type', 'Unknown')),
                'Run ID': run['run_id'][:8],
                'Test Accuracy': metrics.get('test_accuracy', 0),
                'Test Precision': metrics.get('test_precision', 0),
                'Test Recall': metrics.get('test_recall', 0),
                'Test F1': metrics.get('test_f1_score', 0),
                'ROC AUC': metrics.get('test_roc_auc', 0),
                'Training Time (s)': metrics.get('training_time_seconds', 0),
                'Overfitting Gap': metrics.get('overfitting_gap', 0),
                'Date': tags.get('training_date', '')[:10]
            })
    
    df = pd.DataFrame(models_data)
    
    # Group by model type and get best of each
    unique_models = df.groupby('Model').agg({
        'Test Accuracy': 'max',
        'Test F1': 'max',
        'Training Time (s)': 'min',
        'Date': 'max'
    }).round(4)
    
    print("\n[1] Best Performance by Model Type:")
    print(unique_models.to_string())
    
    # Overall ranking
    print("\n[2] Top 10 Models Overall (by Test Accuracy):")
    top_models = df.nlargest(10, 'Test Accuracy')
    print(top_models.to_string(index=False))
    
    return df


def plot_model_comparison(df):
    """Create visualizations comparing models"""
    
    print("\n[*] Creating comparison visualizations...")
    
    # Set style
    sns.set_style("whitegrid")
    fig = plt.figure(figsize=(16, 12))
    
    # 1. Accuracy Comparison
    ax1 = plt.subplot(2, 3, 1)
    model_acc = df.groupby('Model')['Test Accuracy'].max().sort_values(ascending=False)
    model_acc.plot(kind='barh', ax=ax1, color='skyblue')
    ax1.set_title('Test Accuracy by Model Type', fontsize=12, fontweight='bold')
    ax1.set_xlabel('Accuracy')
    ax1.set_xlim(0, 1.1)
    
    # 2. F1 Score Comparison
    ax2 = plt.subplot(2, 3, 2)
    model_f1 = df.groupby('Model')['Test F1'].max().sort_values(ascending=False)
    model_f1.plot(kind='barh', ax=ax2, color='lightgreen')
    ax2.set_title('F1 Score by Model Type', fontsize=12, fontweight='bold')
    ax2.set_xlabel('F1 Score')
    ax2.set_xlim(0, 1.1)
    
    # 3. Training Time Comparison
    ax3 = plt.subplot(2, 3, 3)
    model_time = df.groupby('Model')['Training Time (s)'].min().sort_values()
    model_time.plot(kind='barh', ax=ax3, color='coral')
    ax3.set_title('Training Time by Model Type', fontsize=12, fontweight='bold')
    ax3.set_xlabel('Time (seconds)')
    
    # 4. Precision vs Recall
    ax4 = plt.subplot(2, 3, 4)
    for model_type in df['Model'].unique():
        model_df = df[df['Model'] == model_type]
        ax4.scatter(model_df['Test Recall'], model_df['Test Precision'], 
                   label=model_type, s=100, alpha=0.6)
    ax4.set_xlabel('Recall')
    ax4.set_ylabel('Precision')
    ax4.set_title('Precision vs Recall Trade-off', fontsize=12, fontweight='bold')
    ax4.legend(fontsize=8)
    ax4.plot([0, 1], [0, 1], 'k--', alpha=0.3)
    ax4.set_xlim(0, 1.1)
    ax4.set_ylim(0, 1.1)
    
    # 5. Accuracy vs Training Time
    ax5 = plt.subplot(2, 3, 5)
    for model_type in df['Model'].unique():
        model_df = df[df['Model'] == model_type]
        ax5.scatter(model_df['Training Time (s)'], model_df['Test Accuracy'],
                   label=model_type, s=100, alpha=0.6)
    ax5.set_xlabel('Training Time (seconds)')
    ax5.set_ylabel('Test Accuracy')
    ax5.set_title('Accuracy vs Training Time', fontsize=12, fontweight='bold')
    ax5.legend(fontsize=8)
    
    # 6. Overfitting Analysis
    ax6 = plt.subplot(2, 3, 6)
    model_overfit = df.groupby('Model')['Overfitting Gap'].mean().sort_values()
    colors = ['green' if x <= 0.05 else 'orange' if x <= 0.1 else 'red' for x in model_overfit.values]
    model_overfit.plot(kind='barh', ax=ax6, color=colors)
    ax6.set_title('Overfitting Gap (Train - Test Accuracy)', fontsize=12, fontweight='bold')
    ax6.set_xlabel('Gap (lower is better)')
    ax6.axvline(x=0.05, color='orange', linestyle='--', alpha=0.5, label='Warning threshold')
    ax6.axvline(x=0.1, color='red', linestyle='--', alpha=0.5, label='Critical threshold')
    ax6.legend(fontsize=8)
    
    plt.tight_layout()
    
    # Save
    output_path = Path("model_comparison_dashboard.png")
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"    [OK] Dashboard saved: {output_path}")
    
    plt.close()


def generate_model_selection_report(df):
    """Generate recommendations for model selection"""
    
    print("\n" + "="*100)
    print("MODEL SELECTION RECOMMENDATIONS")
    print("="*100)
    
    # Best overall model
    best_overall = df.loc[df['Test Accuracy'].idxmax()]
    print(f"\n[1] BEST OVERALL MODEL:")
    print(f"    Model: {best_overall['Model']}")
    print(f"    Run ID: {best_overall['Run ID']}")
    print(f"    Test Accuracy: {best_overall['Test Accuracy']:.4f}")
    print(f"    Test F1: {best_overall['Test F1']:.4f}")
    print(f"    Training Time: {best_overall['Training Time (s)']:.3f}s")
    
    # Fastest model with good performance
    fast_models = df[df['Test Accuracy'] >= 0.95]
    if not fast_models.empty:
        fastest = fast_models.loc[fast_models['Training Time (s)'].idxmin()]
        print(f"\n[2] FASTEST MODEL (Accuracy >= 95%):")
        print(f"    Model: {fastest['Model']}")
        print(f"    Run ID: {fastest['Run ID']}")
        print(f"    Test Accuracy: {fastest['Test Accuracy']:.4f}")
        print(f"    Training Time: {fastest['Training Time (s)']:.3f}s")
        print(f"    Speed Advantage: {(best_overall['Training Time (s)'] / fastest['Training Time (s)']):.1f}x faster")
    
    # Best for production (balanced)
    df['production_score'] = (
        df['Test Accuracy'] * 0.4 +
        df['Test F1'] * 0.3 +
        df['Test Precision'] * 0.15 +
        df['Test Recall'] * 0.15
    )
    best_production = df.loc[df['production_score'].idxmax()]
    print(f"\n[3] RECOMMENDED FOR PRODUCTION (Balanced):")
    print(f"    Model: {best_production['Model']}")
    print(f"    Run ID: {best_production['Run ID']}")
    print(f"    Production Score: {best_production['production_score']:.4f}")
    print(f"    Test Accuracy: {best_production['Test Accuracy']:.4f}")
    print(f"    Test F1: {best_production['Test F1']:.4f}")
    
    # Model insights
    print(f"\n[4] MODEL INSIGHTS:")
    
    # Group statistics
    model_stats = df.groupby('Model').agg({
        'Test Accuracy': ['mean', 'std', 'count'],
        'Training Time (s)': ['mean', 'std']
    }).round(4)
    
    print("\n    Performance Statistics by Model Type:")
    print(model_stats.to_string())
    
    # Recommendations
    print(f"\n[5] RECOMMENDATIONS:")
    
    if df['Overfitting Gap'].max() > 0.1:
        print("    [WARNING] Some models show overfitting (gap > 10%)")
        print("    Recommendation: Use regularization or collect more data")
    else:
        print("    [OK] No significant overfitting detected")
    
    if df['Test Accuracy'].std() < 0.05:
        print("    [INFO] All models perform similarly well")
        print("    Recommendation: Choose fastest model for production")
    else:
        print("    [INFO] Performance varies across models")
        print("    Recommendation: Prioritize accuracy for critical applications")
    
    if fastest['Training Time (s)'] < 0.1:
        print(f"    [OK] Fast training time enables real-time retraining")
    
    return {
        'best_overall': best_overall.to_dict(),
        'fastest': fastest.to_dict() if not fast_models.empty else None,
        'production': best_production.to_dict()
    }


def main():
    """Main execution"""
    
    print("="*100)
    print("MLFLOW MODEL COMPARISON DASHBOARD")
    print("="*100)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Load report
    report = load_experiment_report()
    if not report:
        return
    
    print(f"\nExperiment: {report['experiment_name']}")
    print(f"Total Runs: {report['total_runs']}")
    print(f"Report Date: {report['generated_at'][:10]}")
    
    # Create comparison table
    df = create_model_comparison_table(report)
    
    # Create visualizations
    plot_model_comparison(df)
    
    # Generate recommendations
    recommendations = generate_model_selection_report(df)
    
    # Save recommendations
    rec_path = Path("model_selection_recommendations.json")
    with open(rec_path, 'w') as f:
        json.dump(recommendations, f, indent=2)
    
    print(f"\n[OK] Recommendations saved: {rec_path}")
    
    print("\n" + "="*100)
    print("DASHBOARD COMPLETE!")
    print("="*100)
    print("\nFiles Generated:")
    print("  1. model_comparison_dashboard.png - Visual comparison of all models")
    print("  2. model_selection_recommendations.json - Model selection guide")
    print("\nNext Steps:")
    print("  1. Review dashboard: model_comparison_dashboard.png")
    print("  2. Check MLflow UI: http://localhost:5000")
    print("  3. Deploy recommended model to production")


if __name__ == "__main__":
    main()
