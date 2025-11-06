"""
Data Cleaning and Validation Module
Handles data quality checks, cleaning, and validation.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataCleaner:
    """Clean and validate sensor data."""
    
    def __init__(self, config: Dict):
        """
        Initialize data cleaner with configuration.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.sensor_configs = {
            s['name']: s for s in config.get('data', {}).get('sensors', [])
        }
    
    def load_data(self, file_path: str) -> pd.DataFrame:
        """
        Load sensor data from JSON file.
        
        Args:
            file_path: Path to data file
            
        Returns:
            DataFrame with sensor data
        """
        logger.info(f"Loading data from {file_path}")
        
        import json
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Flatten the nested structure
        records = []
        for record in data:
            flat_record = {
                'equipment_id': record.get('equipment_id'),
                'timestamp': record.get('timestamp'),
                'operating_hours': record.get('operating_hours'),
                'time_since_maintenance': record.get('time_since_maintenance'),
                'status': record.get('status'),
                'is_failing': record.get('is_failing', False)
            }
            
            # Add sensor values
            for sensor_name, sensor_data in record.get('sensors', {}).items():
                flat_record[sensor_name] = sensor_data.get('value')
            
            records.append(flat_record)
        
        df = pd.DataFrame(records)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        logger.info(f"Loaded {len(df)} records")
        return df
    
    def check_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Check and report missing values.
        
        Args:
            df: Input DataFrame
            
        Returns:
            DataFrame with missing value statistics
        """
        missing_stats = pd.DataFrame({
            'column': df.columns,
            'missing_count': df.isnull().sum().values,
            'missing_percentage': (df.isnull().sum() / len(df) * 100).values
        })
        
        missing_stats = missing_stats[missing_stats['missing_count'] > 0]
        
        if len(missing_stats) > 0:
            logger.warning(f"Found missing values:\n{missing_stats}")
        else:
            logger.info("No missing values found")
        
        return missing_stats
    
    def handle_missing_values(self, df: pd.DataFrame, 
                             strategy: str = 'interpolate') -> pd.DataFrame:
        """
        Handle missing values in the dataset.
        
        Args:
            df: Input DataFrame
            strategy: Strategy for handling missing values 
                     ('interpolate', 'forward_fill', 'drop', 'mean')
            
        Returns:
            DataFrame with missing values handled
        """
        logger.info(f"Handling missing values using strategy: {strategy}")
        
        df_clean = df.copy()
        numeric_columns = df_clean.select_dtypes(include=[np.number]).columns
        
        if strategy == 'interpolate':
            df_clean[numeric_columns] = df_clean[numeric_columns].interpolate(
                method='linear', limit_direction='both'
            )
        elif strategy == 'forward_fill':
            df_clean[numeric_columns] = df_clean[numeric_columns].ffill()
            df_clean[numeric_columns] = df_clean[numeric_columns].bfill()
        elif strategy == 'drop':
            df_clean = df_clean.dropna()
        elif strategy == 'mean':
            df_clean[numeric_columns] = df_clean[numeric_columns].fillna(
                df_clean[numeric_columns].mean()
            )
        
        logger.info(f"Missing values handled. Remaining: {df_clean.isnull().sum().sum()}")
        return df_clean
    
    def detect_outliers(self, df: pd.DataFrame, 
                       columns: Optional[List[str]] = None,
                       method: str = 'iqr') -> pd.DataFrame:
        """
        Detect outliers in sensor data.
        
        Args:
            df: Input DataFrame
            columns: Columns to check for outliers
            method: Outlier detection method ('iqr', 'zscore', 'threshold')
            
        Returns:
            DataFrame with outlier flags
        """
        if columns is None:
            columns = df.select_dtypes(include=[np.number]).columns.tolist()
        
        df_outliers = df.copy()
        
        for col in columns:
            if col not in df.columns:
                continue
            
            if method == 'iqr':
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                
                df_outliers[f'{col}_outlier'] = (
                    (df[col] < lower_bound) | (df[col] > upper_bound)
                )
            
            elif method == 'zscore':
                z_scores = np.abs((df[col] - df[col].mean()) / df[col].std())
                df_outliers[f'{col}_outlier'] = z_scores > 3
            
            elif method == 'threshold':
                if col in self.sensor_configs:
                    critical_threshold = self.sensor_configs[col]['critical_threshold']
                    df_outliers[f'{col}_outlier'] = df[col] > critical_threshold
        
        outlier_columns = [c for c in df_outliers.columns if c.endswith('_outlier')]
        total_outliers = df_outliers[outlier_columns].sum().sum()
        
        logger.info(f"Detected {total_outliers} outliers using {method} method")
        return df_outliers
    
    def remove_outliers(self, df: pd.DataFrame, 
                       outlier_columns: List[str]) -> pd.DataFrame:
        """
        Remove rows with outliers.
        
        Args:
            df: Input DataFrame with outlier flags
            outlier_columns: Columns with outlier flags
            
        Returns:
            DataFrame with outliers removed
        """
        initial_count = len(df)
        
        # Create mask for rows without any outliers
        mask = ~df[outlier_columns].any(axis=1)
        df_clean = df[mask].copy()
        
        # Remove outlier flag columns
        df_clean = df_clean.drop(columns=outlier_columns)
        
        removed_count = initial_count - len(df_clean)
        logger.info(f"Removed {removed_count} rows with outliers ({removed_count/initial_count*100:.2f}%)")
        
        return df_clean
    
    def validate_data_ranges(self, df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """
        Validate that sensor values are within expected ranges.
        
        Args:
            df: Input DataFrame
            
        Returns:
            Tuple of (is_valid, list of validation errors)
        """
        errors = []
        
        for sensor_name, sensor_config in self.sensor_configs.items():
            if sensor_name not in df.columns:
                continue
            
            min_range, max_range = sensor_config['normal_range']
            critical_threshold = sensor_config['critical_threshold']
            
            # Check for values below minimum
            below_min = df[df[sensor_name] < 0]
            if len(below_min) > 0:
                errors.append(f"{sensor_name}: {len(below_min)} values below 0")
            
            # Check for extremely high values (beyond critical)
            beyond_critical = df[df[sensor_name] > critical_threshold * 1.5]
            if len(beyond_critical) > 0:
                errors.append(
                    f"{sensor_name}: {len(beyond_critical)} values beyond 1.5x critical threshold"
                )
        
        is_valid = len(errors) == 0
        
        if is_valid:
            logger.info("Data validation passed")
        else:
            logger.warning(f"Data validation failed:\n" + "\n".join(errors))
        
        return is_valid, errors
    
    def normalize_timestamps(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize and validate timestamps.
        
        Args:
            df: Input DataFrame
            
        Returns:
            DataFrame with normalized timestamps
        """
        df_norm = df.copy()
        
        # Ensure timestamp is datetime
        if not pd.api.types.is_datetime64_any_dtype(df_norm['timestamp']):
            df_norm['timestamp'] = pd.to_datetime(df_norm['timestamp'])
        
        # Sort by timestamp
        df_norm = df_norm.sort_values('timestamp').reset_index(drop=True)
        
        # Add time-based features
        df_norm['hour'] = df_norm['timestamp'].dt.hour
        df_norm['day_of_week'] = df_norm['timestamp'].dt.dayofweek
        df_norm['day_of_year'] = df_norm['timestamp'].dt.dayofyear
        
        logger.info("Timestamps normalized")
        return df_norm
    
    def clean_pipeline(self, df: pd.DataFrame, 
                      remove_outliers: bool = True) -> pd.DataFrame:
        """
        Run complete data cleaning pipeline.
        
        Args:
            df: Input DataFrame
            remove_outliers: Whether to remove outlier rows
            
        Returns:
            Cleaned DataFrame
        """
        logger.info("Starting data cleaning pipeline")
        
        # Check missing values
        self.check_missing_values(df)
        
        # Handle missing values
        df = self.handle_missing_values(df, strategy='interpolate')
        
        # Normalize timestamps
        df = self.normalize_timestamps(df)
        
        # Detect outliers
        sensor_columns = [col for col in df.columns 
                         if col in self.sensor_configs.keys()]
        df = self.detect_outliers(df, columns=sensor_columns, method='iqr')
        
        # Optionally remove outliers
        if remove_outliers:
            outlier_columns = [c for c in df.columns if c.endswith('_outlier')]
            df = self.remove_outliers(df, outlier_columns)
        
        # Validate data ranges
        self.validate_data_ranges(df)
        
        logger.info(f"Data cleaning pipeline completed. Final dataset size: {len(df)}")
        return df
    
    def save_cleaned_data(self, df: pd.DataFrame, output_path: str):
        """
        Save cleaned data to file.
        
        Args:
            df: Cleaned DataFrame
            output_path: Output file path
        """
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)
        logger.info(f"Cleaned data saved to {output_path}")


def main():
    """Main function for testing data cleaning."""
    # Sample configuration
    config = {
        'data': {
            'sensors': [
                {'name': 'temperature', 'unit': 'celsius', 'normal_range': [20, 80], 'critical_threshold': 90},
                {'name': 'vibration', 'unit': 'mm/s', 'normal_range': [0, 10], 'critical_threshold': 15},
                {'name': 'pressure', 'unit': 'psi', 'normal_range': [80, 120], 'critical_threshold': 140}
            ]
        }
    }
    
    cleaner = DataCleaner(config)
    
    # This would normally load from a file
    # df = cleaner.load_data('data/raw/sensor_data.json')
    # df_clean = cleaner.clean_pipeline(df)
    # cleaner.save_cleaned_data(df_clean, 'data/processed/cleaned_data.csv')
    
    logger.info("Data cleaner module ready")


if __name__ == "__main__":
    main()
