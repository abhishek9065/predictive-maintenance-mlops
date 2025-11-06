"""
Feature Engineering Module
Creates meaningful features from raw sensor data for machine learning.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FeatureEngineer:
    """Engineer features from sensor data for predictive maintenance."""
    
    def __init__(self, config: Dict):
        """
        Initialize feature engineer with configuration.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.feature_config = config.get('features', {})
        self.window_sizes = self.feature_config.get('window_sizes', [5, 10, 30, 60])
        self.sensor_columns = self._get_sensor_columns()
    
    def _get_sensor_columns(self) -> List[str]:
        """Get list of sensor column names from configuration."""
        sensors = self.config.get('data', {}).get('sensors', [])
        return [s['name'] for s in sensors]
    
    def create_statistical_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create statistical features for each sensor.
        
        Args:
            df: Input DataFrame
            
        Returns:
            DataFrame with statistical features
        """
        logger.info("Creating statistical features...")
        df_features = df.copy()
        
        stat_features = self.feature_config.get('statistical_features', 
                                                ['mean', 'std', 'min', 'max', 'median'])
        
        for sensor in self.sensor_columns:
            if sensor not in df.columns:
                continue
            
            # Basic statistics
            if 'mean' in stat_features:
                df_features[f'{sensor}_mean'] = df[sensor].mean()
            if 'std' in stat_features:
                df_features[f'{sensor}_std'] = df[sensor].std()
            if 'min' in stat_features:
                df_features[f'{sensor}_min'] = df[sensor].min()
            if 'max' in stat_features:
                df_features[f'{sensor}_max'] = df[sensor].max()
            if 'median' in stat_features:
                df_features[f'{sensor}_median'] = df[sensor].median()
            if 'skew' in stat_features:
                df_features[f'{sensor}_skew'] = df[sensor].skew()
            if 'kurtosis' in stat_features:
                df_features[f'{sensor}_kurtosis'] = df[sensor].kurtosis()
        
        logger.info(f"Created {len(df_features.columns) - len(df.columns)} statistical features")
        return df_features
    
    def create_rolling_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create rolling window features.
        
        Args:
            df: Input DataFrame (must be sorted by timestamp)
            
        Returns:
            DataFrame with rolling features
        """
        logger.info("Creating rolling window features...")
        df_features = df.copy()
        
        for window_size in self.window_sizes:
            for sensor in self.sensor_columns:
                if sensor not in df.columns:
                    continue
                
                # Rolling mean
                df_features[f'{sensor}_rolling_mean_{window_size}'] = (
                    df[sensor].rolling(window=window_size, min_periods=1).mean()
                )
                
                # Rolling standard deviation
                df_features[f'{sensor}_rolling_std_{window_size}'] = (
                    df[sensor].rolling(window=window_size, min_periods=1).std()
                )
                
                # Rolling min/max
                df_features[f'{sensor}_rolling_min_{window_size}'] = (
                    df[sensor].rolling(window=window_size, min_periods=1).min()
                )
                df_features[f'{sensor}_rolling_max_{window_size}'] = (
                    df[sensor].rolling(window=window_size, min_periods=1).max()
                )
        
        logger.info(f"Created rolling features for {len(self.window_sizes)} window sizes")
        return df_features
    
    def create_lag_features(self, df: pd.DataFrame, 
                           lags: List[int] = [1, 2, 3, 5, 10]) -> pd.DataFrame:
        """
        Create lag features.
        
        Args:
            df: Input DataFrame
            lags: List of lag values
            
        Returns:
            DataFrame with lag features
        """
        logger.info("Creating lag features...")
        df_features = df.copy()
        
        for sensor in self.sensor_columns:
            if sensor not in df.columns:
                continue
            
            for lag in lags:
                df_features[f'{sensor}_lag_{lag}'] = df[sensor].shift(lag)
        
        logger.info(f"Created lag features for {len(lags)} lag values")
        return df_features
    
    def create_rate_of_change_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create rate of change features.
        
        Args:
            df: Input DataFrame
            
        Returns:
            DataFrame with rate of change features
        """
        logger.info("Creating rate of change features...")
        df_features = df.copy()
        
        for sensor in self.sensor_columns:
            if sensor not in df.columns:
                continue
            
            # First difference
            df_features[f'{sensor}_diff'] = df[sensor].diff()
            
            # Percentage change
            df_features[f'{sensor}_pct_change'] = df[sensor].pct_change()
            
            # Second difference (acceleration)
            df_features[f'{sensor}_diff2'] = df[sensor].diff().diff()
        
        logger.info("Rate of change features created")
        return df_features
    
    def create_interaction_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create interaction features between sensors.
        
        Args:
            df: Input DataFrame
            
        Returns:
            DataFrame with interaction features
        """
        logger.info("Creating interaction features...")
        df_features = df.copy()
        
        # Temperature-Vibration interaction
        if 'temperature' in df.columns and 'vibration' in df.columns:
            df_features['temp_vibration_ratio'] = (
                df['temperature'] / (df['vibration'] + 1e-6)
            )
            df_features['temp_vibration_product'] = (
                df['temperature'] * df['vibration']
            )
        
        # Pressure-RPM interaction
        if 'pressure' in df.columns and 'rpm' in df.columns:
            df_features['pressure_rpm_ratio'] = (
                df['pressure'] / (df['rpm'] + 1e-6)
            )
        
        # Current-Temperature interaction
        if 'current' in df.columns and 'temperature' in df.columns:
            df_features['current_temp_ratio'] = (
                df['current'] / (df['temperature'] + 1e-6)
            )
        
        logger.info("Interaction features created")
        return df_features
    
    def create_time_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create time-based features.
        
        Args:
            df: Input DataFrame with timestamp column
            
        Returns:
            DataFrame with time features
        """
        logger.info("Creating time-based features...")
        df_features = df.copy()
        
        if 'timestamp' in df.columns:
            df_features['timestamp'] = pd.to_datetime(df_features['timestamp'])
            
            # Cyclical time features
            df_features['hour_sin'] = np.sin(2 * np.pi * df_features['timestamp'].dt.hour / 24)
            df_features['hour_cos'] = np.cos(2 * np.pi * df_features['timestamp'].dt.hour / 24)
            
            df_features['day_of_week_sin'] = np.sin(2 * np.pi * df_features['timestamp'].dt.dayofweek / 7)
            df_features['day_of_week_cos'] = np.cos(2 * np.pi * df_features['timestamp'].dt.dayofweek / 7)
            
            df_features['month_sin'] = np.sin(2 * np.pi * df_features['timestamp'].dt.month / 12)
            df_features['month_cos'] = np.cos(2 * np.pi * df_features['timestamp'].dt.month / 12)
            
            # Is weekend
            df_features['is_weekend'] = (df_features['timestamp'].dt.dayofweek >= 5).astype(int)
            
            # Is business hours (8 AM - 6 PM)
            df_features['is_business_hours'] = (
                (df_features['timestamp'].dt.hour >= 8) & 
                (df_features['timestamp'].dt.hour < 18)
            ).astype(int)
        
        logger.info("Time-based features created")
        return df_features
    
    def create_operational_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create operational features related to equipment lifecycle.
        
        Args:
            df: Input DataFrame
            
        Returns:
            DataFrame with operational features
        """
        logger.info("Creating operational features...")
        df_features = df.copy()
        
        # Operating hours features (if available)
        if 'operating_hours' in df.columns:
            df_features['operating_hours_squared'] = df['operating_hours'] ** 2
            df_features['operating_hours_log'] = np.log1p(df['operating_hours'])
        
        # Time since maintenance features (if available)
        if 'time_since_maintenance' in df.columns:
            df_features['maintenance_overdue'] = (
                (df['time_since_maintenance'] > 720).astype(int)  # 30 days
            )
            df_features['time_since_maintenance_log'] = np.log1p(df['time_since_maintenance'])
        
        logger.info("Operational features created")
        return df_features
    
    def create_threshold_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create features based on threshold crossings.
        
        Args:
            df: Input DataFrame
            
        Returns:
            DataFrame with threshold features
        """
        logger.info("Creating threshold-based features...")
        df_features = df.copy()
        
        sensor_configs = {
            s['name']: s for s in self.config.get('data', {}).get('sensors', [])
        }
        
        for sensor, config in sensor_configs.items():
            if sensor not in df.columns:
                continue
            
            normal_min, normal_max = config['normal_range']
            critical_threshold = config['critical_threshold']
            
            # Above normal range
            df_features[f'{sensor}_above_normal'] = (
                (df[sensor] > normal_max).astype(int)
            )
            
            # Below normal range
            df_features[f'{sensor}_below_normal'] = (
                (df[sensor] < normal_min).astype(int)
            )
            
            # Near critical
            df_features[f'{sensor}_near_critical'] = (
                (df[sensor] > critical_threshold * 0.8).astype(int)
            )
            
            # Distance from normal range
            df_features[f'{sensor}_distance_from_normal'] = np.where(
                df[sensor] > normal_max,
                df[sensor] - normal_max,
                np.where(df[sensor] < normal_min, normal_min - df[sensor], 0)
            )
        
        logger.info("Threshold-based features created")
        return df_features
    
    def engineer_features_pipeline(self, df: pd.DataFrame, 
                                   include_all: bool = True) -> pd.DataFrame:
        """
        Run complete feature engineering pipeline.
        
        Args:
            df: Input DataFrame
            include_all: Whether to include all feature types
            
        Returns:
            DataFrame with engineered features
        """
        logger.info("Starting feature engineering pipeline...")
        
        # Ensure data is sorted by timestamp
        if 'timestamp' in df.columns:
            df = df.sort_values('timestamp').reset_index(drop=True)
        
        df_features = df.copy()
        
        # Create different feature types
        if include_all:
            df_features = self.create_rolling_features(df_features)
            df_features = self.create_lag_features(df_features)
            df_features = self.create_rate_of_change_features(df_features)
            df_features = self.create_interaction_features(df_features)
            df_features = self.create_time_features(df_features)
            df_features = self.create_operational_features(df_features)
            df_features = self.create_threshold_features(df_features)
        
        # Drop NaN values created by lag/rolling operations
        initial_count = len(df_features)
        df_features = df_features.dropna()
        dropped_count = initial_count - len(df_features)
        
        logger.info(f"Feature engineering completed:")
        logger.info(f"  - Initial features: {len(df.columns)}")
        logger.info(f"  - Final features: {len(df_features.columns)}")
        logger.info(f"  - Rows dropped (NaN): {dropped_count}")
        
        return df_features
    
    def save_features(self, df: pd.DataFrame, output_path: str):
        """
        Save engineered features to file.
        
        Args:
            df: DataFrame with features
            output_path: Output file path
        """
        from pathlib import Path
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)
        logger.info(f"Features saved to {output_path}")
    
    def get_feature_importance_ready_data(self, df: pd.DataFrame, 
                                         target_column: str = 'is_failing') -> tuple:
        """
        Prepare data for model training.
        
        Args:
            df: DataFrame with features
            target_column: Name of target column
            
        Returns:
            Tuple of (X, y, feature_names)
        """
        # Separate features and target
        feature_columns = [col for col in df.columns if col not in 
                          [target_column, 'timestamp', 'equipment_id', 'status']]
        
        X = df[feature_columns]
        y = df[target_column] if target_column in df.columns else None
        
        logger.info(f"Prepared data: {X.shape[0]} samples, {X.shape[1]} features")
        
        return X, y, feature_columns


def main():
    """Main function for testing feature engineering."""
    config = {
        'features': {
            'window_sizes': [5, 10, 30],
            'statistical_features': ['mean', 'std', 'min', 'max', 'median']
        },
        'data': {
            'sensors': [
                {'name': 'temperature', 'unit': 'celsius', 'normal_range': [20, 80], 'critical_threshold': 90},
                {'name': 'vibration', 'unit': 'mm/s', 'normal_range': [0, 10], 'critical_threshold': 15}
            ]
        }
    }
    
    engineer = FeatureEngineer(config)
    logger.info("Feature engineer module ready")


if __name__ == "__main__":
    main()
