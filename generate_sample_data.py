"""
Generate Sample Data for Katib Hyperparameter Tuning
Creates synthetic sensor data for training ML models
"""

import numpy as np
import pandas as pd
from pathlib import Path
import os

def generate_sample_data(n_samples=1000, output_dir="data"):
    """
    Generate synthetic sensor data for predictive maintenance
    
    Args:
        n_samples: Number of samples to generate
        output_dir: Directory to save the data
    """
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Set random seed for reproducibility
    np.random.seed(42)
    
    # Generate features
    temperature = np.random.normal(75, 15, n_samples)
    vibration = np.random.exponential(3.5, n_samples)
    pressure = np.random.normal(100, 20, n_samples)
    rpm = np.random.normal(1500, 300, n_samples)
    power_consumption = np.random.normal(250, 50, n_samples)
    
    # Generate target (failure) based on rules
    # Higher temperature, vibration, and lower pressure increase failure probability
    failure_score = (
        (temperature - 75) / 15 * 0.3 +
        (vibration - 3.5) / 2 * 0.3 +
        (100 - pressure) / 20 * 0.2 +
        (rpm - 1500) / 300 * 0.1 +
        (power_consumption - 250) / 50 * 0.1
    )
    
    # Add some randomness
    failure_score += np.random.normal(0, 0.5, n_samples)
    
    # Convert to binary (0 = no failure, 1 = failure)
    failure = (failure_score > 0.5).astype(int)
    
    # Create DataFrame
    df = pd.DataFrame({
        'temperature': temperature,
        'vibration': vibration,
        'pressure': pressure,
        'rpm': rpm,
        'power_consumption': power_consumption,
        'failure': failure
    })
    
    # Ensure reasonable ranges
    df['temperature'] = df['temperature'].clip(0, 150)
    df['vibration'] = df['vibration'].clip(0, 20)
    df['pressure'] = df['pressure'].clip(50, 150)
    df['rpm'] = df['rpm'].clip(500, 3000)
    df['power_consumption'] = df['power_consumption'].clip(100, 500)
    
    # Split into train and test
    train_size = int(0.8 * n_samples)
    train_df = df[:train_size]
    test_df = df[train_size:]
    
    # Save to CSV
    train_file = output_path / "train.csv"
    test_file = output_path / "test.csv"
    
    train_df.to_csv(train_file, index=False)
    test_df.to_csv(test_file, index=False)
    
    print(f"✅ Generated {n_samples} samples")
    print(f"   - Training samples: {len(train_df)} ({len(train_df[train_df['failure']==1])} failures)")
    print(f"   - Test samples: {len(test_df)} ({len(test_df[test_df['failure']==1])} failures)")
    print(f"   - Train file: {train_file.absolute()}")
    print(f"   - Test file: {test_file.absolute()}")
    
    # Print statistics
    print("\n📊 Feature Statistics:")
    print(df.describe())
    
    print(f"\n⚠️ Failure Rate: {df['failure'].mean()*100:.2f}%")
    
    return train_df, test_df


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate sample data for ML training")
    parser.add_argument("--samples", type=int, default=1000, help="Number of samples to generate")
    parser.add_argument("--output", type=str, default="data", help="Output directory")
    
    args = parser.parse_args()
    
    generate_sample_data(n_samples=args.samples, output_dir=args.output)
