"""
Data Quality Report Generator
Analyzes and reports on the quality of the generated datasets
"""

import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import json

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 8)


def generate_quality_report(data_dir: str = 'data'):
    """Generate comprehensive quality report for all datasets"""
    
    print("=" * 80)
    print("  DATA QUALITY REPORT - PREDICTIVE MAINTENANCE DATASET")
    print("=" * 80)
    print(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    data_path = Path(data_dir)
    
    # Load all datasets
    datasets = {}
    for file in ['full_dataset.csv', 'train.csv', 'test.csv', 'validation.csv', 'train_augmented.csv']:
        file_path = data_path / file
        if file_path.exists():
            datasets[file.replace('.csv', '')] = pd.read_csv(file_path)
            print(f"✅ Loaded: {file} ({len(datasets[file.replace('.csv', '')])} samples)")
    
    print(f"\n{'='*80}\n")
    
    # 1. DATASET OVERVIEW
    print("1. DATASET OVERVIEW")
    print("-" * 80)
    
    for name, df in datasets.items():
        print(f"\n{name.upper()}:")
        print(f"  • Total Samples: {len(df):,}")
        print(f"  • Features: {len(df.columns)}")
        print(f"  • Memory Usage: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
        
        if 'failure' in df.columns:
            normal = (df['failure'] == 0).sum()
            failure = (df['failure'] == 1).sum()
            print(f"  • Normal Samples: {normal:,} ({normal/len(df):.1%})")
            print(f"  • Failure Samples: {failure:,} ({failure/len(df):.1%})")
        
        if 'failure_mode' in df.columns:
            print(f"  • Failure Modes: {df['failure_mode'].nunique()}")
    
    # 2. DATA QUALITY METRICS
    print(f"\n{'='*80}\n")
    print("2. DATA QUALITY METRICS")
    print("-" * 80)
    
    for name, df in datasets.items():
        print(f"\n{name.upper()}:")
        
        # Missing values
        missing = df.isnull().sum()
        if missing.sum() > 0:
            print(f"  ⚠️  Missing Values:")
            for col, count in missing[missing > 0].items():
                print(f"     - {col}: {count} ({count/len(df):.1%})")
        else:
            print(f"  ✅ No missing values")
        
        # Duplicates
        duplicates = df.duplicated().sum()
        if duplicates > 0:
            print(f"  ⚠️  Duplicate Rows: {duplicates} ({duplicates/len(df):.1%})")
        else:
            print(f"  ✅ No duplicate rows")
        
        # Check for infinite values
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        inf_count = np.isinf(df[numeric_cols]).sum().sum()
        if inf_count > 0:
            print(f"  ⚠️  Infinite Values: {inf_count}")
        else:
            print(f"  ✅ No infinite values")
    
    # 3. SENSOR STATISTICS
    print(f"\n{'='*80}\n")
    print("3. SENSOR STATISTICS (Full Dataset)")
    print("-" * 80)
    
    if 'full_dataset' in datasets:
        df = datasets['full_dataset']
        sensor_cols = ['temperature', 'vibration', 'pressure', 'current', 'rpm']
        
        print("\nSensor Ranges:")
        for col in sensor_cols:
            if col in df.columns:
                print(f"\n{col.upper()}:")
                print(f"  Mean: {df[col].mean():.2f}")
                print(f"  Std:  {df[col].std():.2f}")
                print(f"  Min:  {df[col].min():.2f}")
                print(f"  Max:  {df[col].max():.2f}")
                print(f"  25%:  {df[col].quantile(0.25):.2f}")
                print(f"  50%:  {df[col].quantile(0.50):.2f}")
                print(f"  75%:  {df[col].quantile(0.75):.2f}")
    
    # 4. FAILURE MODE DISTRIBUTION
    print(f"\n{'='*80}\n")
    print("4. FAILURE MODE DISTRIBUTION")
    print("-" * 80)
    
    if 'full_dataset' in datasets and 'failure_mode' in datasets['full_dataset'].columns:
        df = datasets['full_dataset']
        print("\nFailure Mode Counts:")
        mode_counts = df['failure_mode'].value_counts()
        for mode, count in mode_counts.items():
            print(f"  • {mode:20s}: {count:6,} ({count/len(df):6.1%})")
    
    # 5. EQUIPMENT DISTRIBUTION
    print(f"\n{'='*80}\n")
    print("5. EQUIPMENT DISTRIBUTION")
    print("-" * 80)
    
    if 'full_dataset' in datasets and 'equipment_id' in datasets['full_dataset'].columns:
        df = datasets['full_dataset']
        print("\nEquipment Counts:")
        equip_counts = df['equipment_id'].value_counts()
        for equip, count in equip_counts.items():
            print(f"  • {equip:20s}: {count:6,} ({count/len(df):6.1%})")
    
    # 6. TEMPORAL COVERAGE
    print(f"\n{'='*80}\n")
    print("6. TEMPORAL COVERAGE")
    print("-" * 80)
    
    if 'full_dataset' in datasets and 'timestamp' in datasets['full_dataset'].columns:
        df = datasets['full_dataset']
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        print(f"\n  Start Date: {df['timestamp'].min()}")
        print(f"  End Date:   {df['timestamp'].max()}")
        print(f"  Duration:   {(df['timestamp'].max() - df['timestamp'].min()).days} days")
        
        if 'hour' in df.columns:
            print(f"\n  Operating Hours Distribution:")
            hour_dist = df['hour'].value_counts().sort_index()
            for hour in range(0, 24, 6):
                count = hour_dist[hour:hour+6].sum()
                print(f"    {hour:02d}:00 - {hour+5:02d}:59: {count:6,} samples")
    
    # 7. CORRELATION ANALYSIS
    print(f"\n{'='*80}\n")
    print("7. FEATURE CORRELATIONS (with failure)")
    print("-" * 80)
    
    if 'full_dataset' in datasets and 'failure' in datasets['full_dataset'].columns:
        df = datasets['full_dataset']
        sensor_cols = ['temperature', 'vibration', 'pressure', 'current', 'rpm']
        
        print("\nCorrelation with Failure:")
        for col in sensor_cols:
            if col in df.columns:
                corr = df[col].corr(df['failure'])
                print(f"  {col:15s}: {corr:+.3f}")
    
    # 8. DATA QUALITY SCORE
    print(f"\n{'='*80}\n")
    print("8. DATA QUALITY SCORE")
    print("-" * 80)
    
    for name, df in datasets.items():
        print(f"\n{name.upper()}:")
        
        # Calculate quality metrics
        completeness = (1 - df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100
        uniqueness = (1 - df.duplicated().sum() / len(df)) * 100
        
        # Check for realistic ranges
        validity = 100
        if 'temperature' in df.columns:
            if (df['temperature'] < -50).any() or (df['temperature'] > 200).any():
                validity -= 10
        if 'vibration' in df.columns:
            if (df['vibration'] < 0).any() or (df['vibration'] > 10).any():
                validity -= 10
        
        overall_quality = (completeness + uniqueness + validity) / 3
        
        print(f"  • Completeness: {completeness:.1f}%")
        print(f"  • Uniqueness:   {uniqueness:.1f}%")
        print(f"  • Validity:     {validity:.1f}%")
        print(f"  • Overall:      {overall_quality:.1f}%")
        
        if overall_quality >= 95:
            print(f"  ✅ EXCELLENT QUALITY")
        elif overall_quality >= 85:
            print(f"  ✅ GOOD QUALITY")
        elif overall_quality >= 75:
            print(f"  ⚠️  FAIR QUALITY")
        else:
            print(f"  ❌ POOR QUALITY")
    
    # 9. RECOMMENDATIONS
    print(f"\n{'='*80}\n")
    print("9. RECOMMENDATIONS")
    print("-" * 80)
    
    recommendations = []
    
    if 'full_dataset' in datasets:
        df = datasets['full_dataset']
        
        # Check class balance
        if 'failure' in df.columns:
            failure_ratio = (df['failure'] == 1).mean()
            if failure_ratio < 0.3:
                recommendations.append("⚠️  Consider collecting more failure samples (currently {:.1%})".format(failure_ratio))
            elif failure_ratio > 0.5:
                recommendations.append("⚠️  Dataset has high failure ratio ({:.1%}) - may not reflect real-world".format(failure_ratio))
            else:
                recommendations.append("✅ Good class balance ({:.1%} failures)".format(failure_ratio))
        
        # Check sample size
        if len(df) < 5000:
            recommendations.append("⚠️  Small dataset - consider generating more samples")
        elif len(df) < 10000:
            recommendations.append("ℹ️  Moderate dataset size - good for initial modeling")
        else:
            recommendations.append("✅ Large dataset - excellent for robust modeling")
        
        # Check temporal coverage
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            duration_days = (df['timestamp'].max() - df['timestamp'].min()).days
            if duration_days < 30:
                recommendations.append("⚠️  Limited temporal coverage - consider longer time period")
            else:
                recommendations.append("✅ Good temporal coverage ({} days)".format(duration_days))
    
    print()
    for rec in recommendations:
        print(f"  {rec}")
    
    # Save summary to JSON
    summary = {
        'generation_date': datetime.now().isoformat(),
        'datasets': {}
    }
    
    for name, df in datasets.items():
        summary['datasets'][name] = {
            'samples': len(df),
            'features': len(df.columns),
            'memory_mb': df.memory_usage(deep=True).sum() / 1024**2,
        }
        
        if 'failure' in df.columns:
            summary['datasets'][name]['normal_samples'] = int((df['failure'] == 0).sum())
            summary['datasets'][name]['failure_samples'] = int((df['failure'] == 1).sum())
    
    summary_path = Path(data_dir) / 'quality_report.json'
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n{'='*80}")
    print(f"✅ Quality report saved: {summary_path}")
    print("=" * 80)


if __name__ == "__main__":
    generate_quality_report()
