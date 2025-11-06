"""
Data Drift Detector
Detects distribution changes in incoming data.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from scipy import stats
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DriftDetector:
    """Detect data drift in production data."""
    
    def __init__(self, reference_data: pd.DataFrame, config: Dict):
        """
        Initialize drift detector.
        
        Args:
            reference_data: Reference (training) data distribution
            config: Configuration dictionary
        """
        self.reference_data = reference_data
        self.config = config
        self.drift_config = config.get('monitoring', {}).get('drift_detection', {})
        self.threshold = self.drift_config.get('threshold', 0.05)
        self.statistical_test = self.drift_config.get('statistical_test', 'ks')
    
    def kolmogorov_smirnov_test(self, 
                                reference: np.ndarray,
                                current: np.ndarray) -> Tuple[float, float]:
        """
        Perform Kolmogorov-Smirnov test.
        
        Args:
            reference: Reference distribution
            current: Current distribution
            
        Returns:
            Tuple of (statistic, p-value)
        """
        statistic, p_value = stats.ks_2samp(reference, current)
        return statistic, p_value
    
    def chi_square_test(self,
                       reference: np.ndarray,
                       current: np.ndarray,
                       bins: int = 10) -> Tuple[float, float]:
        """
        Perform Chi-Square test.
        
        Args:
            reference: Reference distribution
            current: Current distribution
            bins: Number of bins for discretization
            
        Returns:
            Tuple of (statistic, p-value)
        """
        # Create bins
        bin_edges = np.histogram_bin_edges(
            np.concatenate([reference, current]),
            bins=bins
        )
        
        # Get counts for each distribution
        ref_counts, _ = np.histogram(reference, bins=bin_edges)
        curr_counts, _ = np.histogram(current, bins=bin_edges)
        
        # Avoid division by zero
        ref_counts = ref_counts + 1
        curr_counts = curr_counts + 1
        
        # Perform chi-square test
        statistic, p_value = stats.chisquare(curr_counts, ref_counts)
        return statistic, p_value
    
    def detect_drift(self, current_data: pd.DataFrame) -> Dict:
        """
        Detect drift in current data compared to reference.
        
        Args:
            current_data: Current production data
            
        Returns:
            Dictionary with drift detection results
        """
        drift_results = {
            'timestamp': pd.Timestamp.now().isoformat(),
            'features': {},
            'drift_detected': False,
            'drifted_features': []
        }
        
        # Get common columns
        common_columns = set(self.reference_data.columns) & set(current_data.columns)
        numeric_columns = [
            col for col in common_columns
            if pd.api.types.is_numeric_dtype(self.reference_data[col])
        ]
        
        logger.info(f"Checking drift for {len(numeric_columns)} features...")
        
        for feature in numeric_columns:
            ref_values = self.reference_data[feature].dropna().values
            curr_values = current_data[feature].dropna().values
            
            if len(ref_values) == 0 or len(curr_values) == 0:
                continue
            
            # Perform statistical test
            if self.statistical_test == 'ks':
                statistic, p_value = self.kolmogorov_smirnov_test(ref_values, curr_values)
            elif self.statistical_test == 'chi_square':
                statistic, p_value = self.chi_square_test(ref_values, curr_values)
            else:
                logger.warning(f"Unknown test: {self.statistical_test}, using KS test")
                statistic, p_value = self.kolmogorov_smirnov_test(ref_values, curr_values)
            
            # Check for drift
            is_drifted = p_value < self.threshold
            
            drift_results['features'][feature] = {
                'statistic': float(statistic),
                'p_value': float(p_value),
                'is_drifted': is_drifted,
                'test': self.statistical_test
            }
            
            if is_drifted:
                drift_results['drift_detected'] = True
                drift_results['drifted_features'].append(feature)
                logger.warning(
                    f"Drift detected in '{feature}': "
                    f"p-value={p_value:.4f} < threshold={self.threshold}"
                )
        
        if drift_results['drift_detected']:
            logger.warning(
                f"Data drift detected in {len(drift_results['drifted_features'])} features: "
                f"{drift_results['drifted_features']}"
            )
        else:
            logger.info("No significant drift detected")
        
        return drift_results
    
    def calculate_feature_statistics(self, data: pd.DataFrame) -> Dict:
        """
        Calculate statistical properties of features.
        
        Args:
            data: Input data
            
        Returns:
            Dictionary of statistics
        """
        stats_dict = {}
        
        for column in data.select_dtypes(include=[np.number]).columns:
            stats_dict[column] = {
                'mean': float(data[column].mean()),
                'std': float(data[column].std()),
                'min': float(data[column].min()),
                'max': float(data[column].max()),
                'median': float(data[column].median()),
                'q25': float(data[column].quantile(0.25)),
                'q75': float(data[column].quantile(0.75))
            }
        
        return stats_dict


def main():
    """Main function for testing drift detector."""
    # Create sample reference data
    np.random.seed(42)
    reference_data = pd.DataFrame({
        'temperature': np.random.normal(60, 10, 1000),
        'vibration': np.random.normal(5, 2, 1000),
        'pressure': np.random.normal(100, 15, 1000)
    })
    
    # Create current data with drift
    current_data = pd.DataFrame({
        'temperature': np.random.normal(70, 10, 100),  # Mean shift
        'vibration': np.random.normal(5, 2, 100),
        'pressure': np.random.normal(100, 15, 100)
    })
    
    config = {
        'monitoring': {
            'drift_detection': {
                'threshold': 0.05,
                'statistical_test': 'ks'
            }
        }
    }
    
    detector = DriftDetector(reference_data, config)
    results = detector.detect_drift(current_data)
    
    logger.info(f"Drift detection results: {results}")


if __name__ == "__main__":
    main()
