"""
Advanced High-Quality Data Generator for Predictive Maintenance
Generates realistic sensor data with multiple failure modes and patterns
"""

import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import argparse
import logging
from typing import Dict, List, Tuple

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class AdvancedDataGenerator:
    """Generate high-quality realistic sensor data with complex failure patterns"""
    
    def __init__(self, random_state: int = 42):
        np.random.seed(random_state)
        self.failure_modes = [
            'bearing_wear',
            'overheating',
            'vibration_anomaly',
            'electrical_fault',
            'pressure_leak',
            'normal_degradation'
        ]
    
    def generate_normal_operation(self, n_samples: int) -> pd.DataFrame:
        """Generate data for normal operation with natural variations"""
        logger.info(f"Generating {n_samples} normal operation samples...")
        
        # Time-based patterns (daily cycles, weekly patterns)
        time_cycle = np.linspace(0, 2*np.pi * (n_samples/1000), n_samples)
        
        data = {
            'temperature': 65 + 5*np.sin(time_cycle) + np.random.normal(0, 2, n_samples),
            'vibration': 0.3 + 0.1*np.sin(time_cycle*2) + np.random.normal(0, 0.05, n_samples),
            'pressure': 95 + 3*np.cos(time_cycle) + np.random.normal(0, 1.5, n_samples),
            'current': 8 + 1.5*np.sin(time_cycle) + np.random.normal(0, 0.5, n_samples),
            'rpm': 1450 + 30*np.cos(time_cycle*1.5) + np.random.normal(0, 10, n_samples),
            'failure': 0
        }
        
        df = pd.DataFrame(data)
        df['failure_mode'] = 'normal'
        df['operating_hours'] = np.cumsum(np.random.uniform(0.5, 2, n_samples))
        
        return df
    
    def generate_bearing_wear(self, n_samples: int) -> pd.DataFrame:
        """Simulate progressive bearing wear failure"""
        logger.info(f"Generating {n_samples} bearing wear failure samples...")
        
        progression = np.linspace(0, 1, n_samples)
        
        data = {
            'temperature': 65 + progression * 25 + np.random.normal(0, 3, n_samples),
            'vibration': 0.3 + progression * 1.5 + np.random.normal(0, 0.1, n_samples),
            'pressure': 95 - progression * 5 + np.random.normal(0, 2, n_samples),
            'current': 8 + progression * 4 + np.random.normal(0, 0.8, n_samples),
            'rpm': 1450 - progression * 100 + np.random.normal(0, 15, n_samples),
            'failure': 1
        }
        
        df = pd.DataFrame(data)
        df['failure_mode'] = 'bearing_wear'
        df['operating_hours'] = np.cumsum(np.random.uniform(1, 3, n_samples))
        
        return df
    
    def generate_overheating(self, n_samples: int) -> pd.DataFrame:
        """Simulate overheating failure pattern"""
        logger.info(f"Generating {n_samples} overheating failure samples...")
        
        progression = np.linspace(0, 1, n_samples)
        heat_spikes = np.random.choice([0, 1], n_samples, p=[0.7, 0.3]) * np.random.uniform(5, 15, n_samples)
        
        data = {
            'temperature': 70 + progression * 45 + heat_spikes + np.random.normal(0, 4, n_samples),
            'vibration': 0.4 + progression * 0.8 + np.random.normal(0, 0.12, n_samples),
            'pressure': 100 + progression * 15 + np.random.normal(0, 3, n_samples),
            'current': 9 + progression * 6 + np.random.normal(0, 1, n_samples),
            'rpm': 1500 + progression * 200 + np.random.normal(0, 25, n_samples),
            'failure': 1
        }
        
        df = pd.DataFrame(data)
        df['failure_mode'] = 'overheating'
        df['operating_hours'] = np.cumsum(np.random.uniform(0.5, 2, n_samples))
        
        return df
    
    def generate_vibration_anomaly(self, n_samples: int) -> pd.DataFrame:
        """Simulate vibration-related failures (imbalance, misalignment)"""
        logger.info(f"Generating {n_samples} vibration anomaly samples...")
        
        progression = np.linspace(0, 1, n_samples)
        # Oscillating vibration pattern
        vibration_pattern = np.sin(np.linspace(0, 10*np.pi, n_samples)) * progression
        
        data = {
            'temperature': 68 + progression * 15 + np.random.normal(0, 2.5, n_samples),
            'vibration': 0.5 + progression * 2.5 + vibration_pattern * 0.5 + np.random.normal(0, 0.15, n_samples),
            'pressure': 92 - progression * 8 + np.random.normal(0, 2, n_samples),
            'current': 8.5 + progression * 3 + np.random.normal(0, 0.7, n_samples),
            'rpm': 1460 + progression * 50 + vibration_pattern * 30 + np.random.normal(0, 20, n_samples),
            'failure': 1
        }
        
        df = pd.DataFrame(data)
        df['failure_mode'] = 'vibration_anomaly'
        df['operating_hours'] = np.cumsum(np.random.uniform(0.8, 2.5, n_samples))
        
        return df
    
    def generate_electrical_fault(self, n_samples: int) -> pd.DataFrame:
        """Simulate electrical system failures"""
        logger.info(f"Generating {n_samples} electrical fault samples...")
        
        progression = np.linspace(0, 1, n_samples)
        current_spikes = np.random.choice([0, 1], n_samples, p=[0.6, 0.4]) * np.random.uniform(3, 8, n_samples)
        
        data = {
            'temperature': 72 + progression * 20 + np.random.normal(0, 3.5, n_samples),
            'vibration': 0.35 + progression * 0.5 + np.random.normal(0, 0.08, n_samples),
            'pressure': 98 + np.random.normal(0, 2.5, n_samples),
            'current': 10 + progression * 8 + current_spikes + np.random.normal(0, 1.2, n_samples),
            'rpm': 1470 - progression * 150 + np.random.normal(0, 30, n_samples),
            'failure': 1
        }
        
        df = pd.DataFrame(data)
        df['failure_mode'] = 'electrical_fault'
        df['operating_hours'] = np.cumsum(np.random.uniform(0.5, 2, n_samples))
        
        return df
    
    def generate_pressure_leak(self, n_samples: int) -> pd.DataFrame:
        """Simulate pressure system leaks"""
        logger.info(f"Generating {n_samples} pressure leak samples...")
        
        progression = np.linspace(0, 1, n_samples)
        
        data = {
            'temperature': 66 + progression * 12 + np.random.normal(0, 2, n_samples),
            'vibration': 0.4 + progression * 0.7 + np.random.normal(0, 0.1, n_samples),
            'pressure': 95 - progression * 40 + np.random.normal(0, 3, n_samples),
            'current': 7.5 - progression * 2 + np.random.normal(0, 0.6, n_samples),
            'rpm': 1440 - progression * 80 + np.random.normal(0, 15, n_samples),
            'failure': 1
        }
        
        df = pd.DataFrame(data)
        df['failure_mode'] = 'pressure_leak'
        df['operating_hours'] = np.cumsum(np.random.uniform(1, 3, n_samples))
        
        return df
    
    def generate_degradation(self, n_samples: int) -> pd.DataFrame:
        """Simulate normal wear and tear over time"""
        logger.info(f"Generating {n_samples} normal degradation samples...")
        
        progression = np.linspace(0, 0.5, n_samples)  # Slower progression
        
        data = {
            'temperature': 67 + progression * 18 + np.random.normal(0, 2.5, n_samples),
            'vibration': 0.32 + progression * 0.8 + np.random.normal(0, 0.08, n_samples),
            'pressure': 96 - progression * 12 + np.random.normal(0, 2, n_samples),
            'current': 8.2 + progression * 3.5 + np.random.normal(0, 0.7, n_samples),
            'rpm': 1455 - progression * 60 + np.random.normal(0, 12, n_samples),
            'failure': 1
        }
        
        df = pd.DataFrame(data)
        df['failure_mode'] = 'normal_degradation'
        df['operating_hours'] = np.cumsum(np.random.uniform(2, 5, n_samples))
        
        return df
    
    def add_environmental_factors(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add realistic environmental variations"""
        logger.info("Adding environmental factors...")
        
        n_samples = len(df)
        
        # Ambient temperature effect
        df['ambient_temp'] = np.random.normal(22, 5, n_samples)
        df['temperature'] += df['ambient_temp'] * 0.15
        
        # Humidity effect on electrical systems
        df['humidity'] = np.random.normal(50, 15, n_samples).clip(20, 80)
        df['current'] += (df['humidity'] - 50) * 0.02
        
        # Load variations
        df['load_percent'] = np.random.normal(75, 15, n_samples).clip(40, 100)
        df['current'] *= df['load_percent'] / 75
        df['temperature'] += (df['load_percent'] - 75) * 0.2
        
        # Maintenance history (binary: 0=no recent maintenance, 1=recently maintained)
        df['recent_maintenance'] = np.random.choice([0, 1], n_samples, p=[0.85, 0.15])
        
        return df
    
    def add_time_features(self, df: pd.DataFrame, start_date: str = '2024-01-01') -> pd.DataFrame:
        """Add realistic timestamp and time-based features"""
        logger.info("Adding time features...")
        
        start = pd.to_datetime(start_date)
        n_samples = len(df)
        
        # Generate timestamps with realistic intervals
        time_intervals = pd.to_timedelta(np.cumsum(np.random.uniform(5, 15, n_samples)), unit='m')
        df['timestamp'] = start + time_intervals
        
        # Extract time features
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        df['month'] = df['timestamp'].dt.month
        
        # Working hours (8 AM - 6 PM weekdays have higher load)
        df['is_working_hours'] = ((df['hour'] >= 8) & (df['hour'] <= 18) & (df['day_of_week'] < 5)).astype(int)
        
        return df
    
    def add_sensor_noise(self, df: pd.DataFrame, noise_level: float = 0.02) -> pd.DataFrame:
        """Add realistic sensor noise and occasional measurement errors"""
        logger.info("Adding sensor noise and measurement errors...")
        
        n_samples = len(df)
        
        # Gaussian noise
        for col in ['temperature', 'vibration', 'pressure', 'current', 'rpm']:
            df[col] += np.random.normal(0, df[col].std() * noise_level, n_samples)
        
        # Occasional sensor spikes (1% of readings)
        spike_indices = np.random.choice(n_samples, size=int(n_samples * 0.01), replace=False)
        for idx in spike_indices:
            col = np.random.choice(['temperature', 'vibration', 'pressure', 'current', 'rpm'])
            df.loc[idx, col] *= np.random.uniform(1.1, 1.3)
        
        # Occasional sensor dropouts (0.5% of readings)
        dropout_indices = np.random.choice(n_samples, size=int(n_samples * 0.005), replace=False)
        # We'll mark these but not actually drop them for data integrity
        df['sensor_dropout'] = 0
        df.loc[dropout_indices, 'sensor_dropout'] = 1
        
        return df
    
    def generate_complete_dataset(self, 
                                 total_samples: int = 10000,
                                 failure_ratio: float = 0.3) -> pd.DataFrame:
        """
        Generate complete high-quality dataset with all failure modes
        
        Args:
            total_samples: Total number of samples to generate
            failure_ratio: Ratio of failure samples (0.3 = 30%)
        """
        logger.info("=" * 70)
        logger.info("GENERATING HIGH-QUALITY DATASET")
        logger.info("=" * 70)
        logger.info(f"Total samples: {total_samples}")
        logger.info(f"Failure ratio: {failure_ratio:.1%}")
        
        # Calculate samples per category
        n_failure = int(total_samples * failure_ratio)
        n_normal = total_samples - n_failure
        
        # Distribute failure samples across different modes
        n_per_failure_mode = n_failure // 6
        
        # Generate different datasets
        dfs = []
        
        # Normal operation
        dfs.append(self.generate_normal_operation(n_normal))
        
        # Different failure modes
        dfs.append(self.generate_bearing_wear(n_per_failure_mode))
        dfs.append(self.generate_overheating(n_per_failure_mode))
        dfs.append(self.generate_vibration_anomaly(n_per_failure_mode))
        dfs.append(self.generate_electrical_fault(n_per_failure_mode))
        dfs.append(self.generate_pressure_leak(n_per_failure_mode))
        dfs.append(self.generate_degradation(n_failure - 5*n_per_failure_mode))
        
        # Combine all datasets
        logger.info("\nCombining all failure modes...")
        df = pd.concat(dfs, ignore_index=True)
        
        # Add additional features
        df = self.add_environmental_factors(df)
        df = self.add_time_features(df)
        df = self.add_sensor_noise(df)
        
        # Shuffle the dataset
        df = df.sample(frac=1, random_state=42).reset_index(drop=True)
        
        # Add unique ID
        df['equipment_id'] = np.random.choice(['PUMP-001', 'PUMP-002', 'MOTOR-001', 'MOTOR-002', 'COMPRESSOR-001'], len(df))
        
        logger.info("\n" + "=" * 70)
        logger.info("DATASET STATISTICS")
        logger.info("=" * 70)
        logger.info(f"Total samples: {len(df)}")
        logger.info(f"Normal samples: {(df['failure'] == 0).sum()} ({(df['failure'] == 0).mean():.1%})")
        logger.info(f"Failure samples: {(df['failure'] == 1).sum()} ({(df['failure'] == 1).mean():.1%})")
        logger.info("\nFailure mode distribution:")
        logger.info(df['failure_mode'].value_counts())
        logger.info("\nSensor statistics:")
        logger.info(df[['temperature', 'vibration', 'pressure', 'current', 'rpm']].describe())
        
        return df


def main():
    parser = argparse.ArgumentParser(description="Generate high-quality sensor data")
    parser.add_argument('--samples', type=int, default=10000, help='Total samples to generate')
    parser.add_argument('--failure-ratio', type=float, default=0.3, help='Ratio of failure samples')
    parser.add_argument('--output-dir', type=str, default='data', help='Output directory')
    parser.add_argument('--train-split', type=float, default=0.8, help='Train/test split ratio')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    
    args = parser.parse_args()
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate data
    generator = AdvancedDataGenerator(random_state=args.seed)
    df = generator.generate_complete_dataset(
        total_samples=args.samples,
        failure_ratio=args.failure_ratio
    )
    
    # Split into train and test
    train_size = int(len(df) * args.train_split)
    train_df = df.iloc[:train_size].copy()
    test_df = df.iloc[train_size:].copy()
    
    # Save full dataset
    full_path = output_dir / 'full_dataset.csv'
    df.to_csv(full_path, index=False)
    logger.info(f"\n✅ Full dataset saved: {full_path} ({len(df)} samples)")
    
    # Save train/test split
    train_path = output_dir / 'train.csv'
    test_path = output_dir / 'test.csv'
    
    train_df.to_csv(train_path, index=False)
    test_df.to_csv(test_path, index=False)
    
    logger.info(f"✅ Train set saved: {train_path} ({len(train_df)} samples)")
    logger.info(f"✅ Test set saved: {test_path} ({len(test_df)} samples)")
    
    # Generate additional validation set
    val_df = test_df.sample(frac=0.5, random_state=args.seed)
    val_path = output_dir / 'validation.csv'
    val_df.to_csv(val_path, index=False)
    logger.info(f"✅ Validation set saved: {val_path} ({len(val_df)} samples)")
    
    # Save metadata
    metadata = {
        'generation_date': datetime.now().isoformat(),
        'total_samples': len(df),
        'train_samples': len(train_df),
        'test_samples': len(test_df),
        'validation_samples': len(val_df),
        'failure_ratio': args.failure_ratio,
        'features': list(df.columns),
        'failure_modes': df['failure_mode'].unique().tolist(),
        'equipment_types': df['equipment_id'].unique().tolist()
    }
    
    import json
    metadata_path = output_dir / 'dataset_metadata.json'
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"✅ Metadata saved: {metadata_path}")
    
    logger.info("\n" + "=" * 70)
    logger.info("✅ HIGH-QUALITY DATASET GENERATION COMPLETE!")
    logger.info("=" * 70)
    logger.info(f"\n📊 Summary:")
    logger.info(f"   - Total samples: {len(df):,}")
    logger.info(f"   - Features: {len(df.columns)}")
    logger.info(f"   - Failure modes: {len(df['failure_mode'].unique())}")
    logger.info(f"   - Time span: {df['timestamp'].min()} to {df['timestamp'].max()}")
    logger.info(f"   - Equipment: {', '.join(df['equipment_id'].unique())}")


if __name__ == "__main__":
    main()
