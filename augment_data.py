"""
Data Augmentation for Predictive Maintenance
Creates synthetic variations of existing data to increase dataset size and diversity
"""

import numpy as np
import pandas as pd
from pathlib import Path
import argparse
import logging
from typing import List, Tuple

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DataAugmenter:
    """Advanced data augmentation techniques for sensor time-series data"""
    
    def __init__(self, random_state: int = 42):
        np.random.seed(random_state)
    
    def add_gaussian_noise(self, df: pd.DataFrame, noise_factor: float = 0.05) -> pd.DataFrame:
        """Add Gaussian noise to sensor readings"""
        augmented = df.copy()
        sensor_cols = ['temperature', 'vibration', 'pressure', 'current', 'rpm']
        
        for col in sensor_cols:
            if col in augmented.columns:
                noise = np.random.normal(0, augmented[col].std() * noise_factor, len(augmented))
                augmented[col] += noise
        
        return augmented
    
    def time_shift(self, df: pd.DataFrame, shift_range: Tuple[float, float] = (-0.1, 0.1)) -> pd.DataFrame:
        """Apply random time shifts to create temporal variations"""
        augmented = df.copy()
        sensor_cols = ['temperature', 'vibration', 'pressure', 'current', 'rpm']
        
        for col in sensor_cols:
            if col in augmented.columns:
                shift = np.random.uniform(*shift_range)
                augmented[col] = augmented[col] * (1 + shift)
        
        return augmented
    
    def magnitude_scaling(self, df: pd.DataFrame, scale_range: Tuple[float, float] = (0.9, 1.1)) -> pd.DataFrame:
        """Scale sensor magnitudes within realistic range"""
        augmented = df.copy()
        sensor_cols = ['temperature', 'vibration', 'pressure', 'current', 'rpm']
        
        for col in sensor_cols:
            if col in augmented.columns:
                scale = np.random.uniform(*scale_range)
                augmented[col] = augmented[col] * scale
        
        return augmented
    
    def add_drift(self, df: pd.DataFrame, drift_factor: float = 0.02) -> pd.DataFrame:
        """Add gradual drift to simulate sensor calibration issues"""
        augmented = df.copy()
        sensor_cols = ['temperature', 'vibration', 'pressure', 'current', 'rpm']
        
        n = len(augmented)
        drift = np.linspace(0, drift_factor, n)
        
        for col in sensor_cols:
            if col in augmented.columns:
                direction = np.random.choice([-1, 1])
                augmented[col] += augmented[col] * drift * direction
        
        return augmented
    
    def add_spikes(self, df: pd.DataFrame, spike_prob: float = 0.02, spike_magnitude: float = 0.3) -> pd.DataFrame:
        """Add occasional spikes to simulate transient events"""
        augmented = df.copy()
        sensor_cols = ['temperature', 'vibration', 'pressure', 'current', 'rpm']
        
        n = len(augmented)
        
        for col in sensor_cols:
            if col in augmented.columns:
                spike_mask = np.random.random(n) < spike_prob
                spike_values = np.random.uniform(1, 1 + spike_magnitude, n)
                augmented.loc[spike_mask, col] *= spike_values[spike_mask]
        
        return augmented
    
    def seasonal_variation(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add seasonal temperature variations"""
        augmented = df.copy()
        n = len(augmented)
        
        # Simulate seasonal cycle
        season_cycle = np.sin(np.linspace(0, 2*np.pi, n))
        
        if 'temperature' in augmented.columns:
            augmented['temperature'] += season_cycle * 5
        
        if 'ambient_temp' in augmented.columns:
            augmented['ambient_temp'] += season_cycle * 10
        
        return augmented
    
    def load_variation(self, df: pd.DataFrame) -> pd.DataFrame:
        """Simulate different load conditions"""
        augmented = df.copy()
        
        # Random load variation
        load_multiplier = np.random.uniform(0.7, 1.3)
        
        if 'current' in augmented.columns:
            augmented['current'] *= load_multiplier
        
        if 'temperature' in augmented.columns:
            augmented['temperature'] += (load_multiplier - 1) * 10
        
        if 'load_percent' in augmented.columns:
            augmented['load_percent'] *= load_multiplier
            augmented['load_percent'] = augmented['load_percent'].clip(40, 100)
        
        return augmented
    
    def combine_augmentations(self, df: pd.DataFrame, n_augmentations: int = 5) -> List[pd.DataFrame]:
        """Apply multiple random augmentations"""
        logger.info(f"Applying {n_augmentations} augmentation combinations...")
        
        augmented_dfs = [df.copy()]  # Original data
        
        augmentation_methods = [
            lambda x: self.add_gaussian_noise(x, np.random.uniform(0.02, 0.08)),
            lambda x: self.time_shift(x, (-0.05, 0.05)),
            lambda x: self.magnitude_scaling(x, (0.95, 1.05)),
            lambda x: self.add_drift(x, np.random.uniform(0.01, 0.03)),
            lambda x: self.add_spikes(x, 0.02, 0.2),
            self.seasonal_variation,
            self.load_variation
        ]
        
        for i in range(n_augmentations):
            # Apply 2-3 random augmentations
            n_methods = np.random.randint(2, 4)
            selected_methods = np.random.choice(len(augmentation_methods), n_methods, replace=False)
            
            augmented = df.copy()
            for method_idx in selected_methods:
                augmented = augmentation_methods[method_idx](augmented)
            
            augmented_dfs.append(augmented)
        
        return augmented_dfs
    
    def augment_minority_class(self, df: pd.DataFrame, target_col: str = 'failure', 
                               balance_ratio: float = 0.5) -> pd.DataFrame:
        """
        Augment minority class to balance dataset
        
        Args:
            df: Input dataframe
            target_col: Target column name
            balance_ratio: Target ratio for minority class
        """
        logger.info("Balancing dataset using augmentation...")
        
        # Separate classes
        majority = df[df[target_col] == 0]
        minority = df[df[target_col] == 1]
        
        logger.info(f"Original - Majority: {len(majority)}, Minority: {len(minority)}")
        
        # Calculate how many samples needed
        target_minority = int(len(majority) * balance_ratio / (1 - balance_ratio))
        n_to_generate = target_minority - len(minority)
        
        if n_to_generate <= 0:
            logger.info("Dataset already balanced or minority is majority")
            return df
        
        logger.info(f"Generating {n_to_generate} synthetic minority samples...")
        
        # Generate synthetic samples
        augmented_samples = []
        n_per_augmentation = n_to_generate // 5 + 1
        
        for _ in range(5):
            sample = minority.sample(n=min(n_per_augmentation, len(minority)), replace=True)
            augmented = self.combine_augmentations(sample, n_augmentations=1)[1]
            augmented_samples.append(augmented)
        
        # Combine all
        all_minority = pd.concat([minority] + augmented_samples[:n_to_generate], ignore_index=True)
        balanced_df = pd.concat([majority, all_minority], ignore_index=True)
        balanced_df = balanced_df.sample(frac=1).reset_index(drop=True)
        
        logger.info(f"Balanced - Majority: {len(majority)}, Minority: {len(all_minority)}")
        
        return balanced_df


def main():
    parser = argparse.ArgumentParser(description="Augment sensor data")
    parser.add_argument('--input', type=str, default='data/train.csv', help='Input data file')
    parser.add_argument('--output', type=str, default='data/train_augmented.csv', help='Output file')
    parser.add_argument('--augmentations', type=int, default=3, help='Number of augmentation variations')
    parser.add_argument('--balance', action='store_true', help='Balance classes using augmentation')
    parser.add_argument('--balance-ratio', type=float, default=0.45, help='Target minority class ratio')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    
    args = parser.parse_args()
    
    logger.info("=" * 70)
    logger.info("DATA AUGMENTATION")
    logger.info("=" * 70)
    
    # Load data
    logger.info(f"Loading data from {args.input}...")
    df = pd.read_csv(args.input)
    logger.info(f"Original dataset: {len(df)} samples")
    
    # Initialize augmenter
    augmenter = DataAugmenter(random_state=args.seed)
    
    if args.balance:
        # Balance classes
        df = augmenter.augment_minority_class(df, balance_ratio=args.balance_ratio)
    else:
        # Apply general augmentation
        augmented_dfs = augmenter.combine_augmentations(df, n_augmentations=args.augmentations)
        df = pd.concat(augmented_dfs, ignore_index=True)
        df = df.sample(frac=1).reset_index(drop=True)
    
    # Save
    logger.info(f"\nSaving augmented data to {args.output}...")
    df.to_csv(args.output, index=False)
    
    logger.info("\n" + "=" * 70)
    logger.info("AUGMENTATION COMPLETE")
    logger.info("=" * 70)
    logger.info(f"Final dataset: {len(df)} samples")
    if 'failure' in df.columns:
        logger.info(f"Normal: {(df['failure'] == 0).sum()} ({(df['failure'] == 0).mean():.1%})")
        logger.info(f"Failure: {(df['failure'] == 1).sum()} ({(df['failure'] == 1).mean():.1%})")
    logger.info(f"✅ Saved: {args.output}")


if __name__ == "__main__":
    main()
