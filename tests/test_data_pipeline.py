"""
Unit Tests for Data Processing Pipeline
"""

import pytest
import numpy as np
import json
from pathlib import Path


class TestDataCollection:
    """Test data collection and loading"""
    
    def test_historical_data_exists(self):
        """Verify historical data files exist"""
        data_dir = Path("data/raw")
        files = list(data_dir.glob("historical_*.json"))
        assert len(files) > 0, "No historical data files found"
    
    def test_data_file_readable(self):
        """Verify data files can be read"""
        data_dir = Path("data/raw")
        files = list(data_dir.glob("historical_*.json"))
        
        if files:
            with open(files[0], 'r') as f:
                data = json.load(f)
            assert isinstance(data, list), "Data should be a list"
            assert len(data) > 0, "Data file is empty"
    
    def test_data_schema(self):
        """Verify data has correct schema"""
        data_dir = Path("data/raw")
        files = list(data_dir.glob("historical_*.json"))
        
        if files:
            with open(files[0], 'r') as f:
                data = json.load(f)
            
            sample = data[0]
            required_fields = ['equipment_id', 'timestamp', 'sensors', 'is_failing']
            
            for field in required_fields:
                assert field in sample, f"Missing field: {field}"
    
    def test_sensor_data_structure(self):
        """Verify sensor data has correct structure"""
        data_dir = Path("data/raw")
        files = list(data_dir.glob("historical_*.json"))
        
        if files:
            with open(files[0], 'r') as f:
                data = json.load(f)
            
            sensors = data[0]['sensors']
            required_sensors = ['temperature', 'vibration', 'pressure', 'current', 'rpm']
            
            for sensor in required_sensors:
                assert sensor in sensors, f"Missing sensor: {sensor}"
                assert 'value' in sensors[sensor], f"Sensor {sensor} missing value"
                assert 'unit' in sensors[sensor], f"Sensor {sensor} missing unit"


class TestFeatureExtraction:
    """Test feature engineering pipeline"""
    
    @pytest.fixture
    def sample_data(self):
        """Create sample sensor data for testing"""
        return {
            'equipment_id': 'TEST_001',
            'timestamp': '2025-11-05T10:00:00',
            'sensors': {
                'temperature': {'value': 60.0, 'unit': 'celsius'},
                'vibration': {'value': 5.0, 'unit': 'mm/s'},
                'pressure': {'value': 100.0, 'unit': 'psi'},
                'current': {'value': 20.0, 'unit': 'ampere'},
                'rpm': {'value': 1500.0, 'unit': 'rpm'}
            },
            'is_failing': False
        }
    
    def test_feature_extraction(self, sample_data):
        """Test extracting features from sensor data"""
        sensors = sample_data['sensors']
        features = [
            sensors['temperature']['value'],
            sensors['vibration']['value'],
            sensors['pressure']['value'],
            sensors['current']['value'],
            sensors['rpm']['value']
        ]
        
        assert len(features) == 5, "Should extract 5 features"
        assert all(isinstance(f, (int, float)) for f in features), "All features should be numeric"
    
    def test_feature_ranges(self, sample_data):
        """Test features are within expected ranges"""
        sensors = sample_data['sensors']
        
        # Test reasonable ranges
        assert 0 <= sensors['temperature']['value'] <= 150, "Temperature out of range"
        assert 0 <= sensors['vibration']['value'] <= 20, "Vibration out of range"
        assert 0 <= sensors['pressure']['value'] <= 200, "Pressure out of range"
        assert 0 <= sensors['current']['value'] <= 100, "Current out of range"
        assert 0 <= sensors['rpm']['value'] <= 3000, "RPM out of range"


class TestDataQuality:
    """Test data quality checks"""
    
    def test_no_missing_values(self):
        """Verify no missing values in data"""
        data_dir = Path("data/raw")
        files = list(data_dir.glob("historical_*.json"))
        
        if files:
            with open(files[0], 'r') as f:
                data = json.load(f)
            
            # Extract features
            features = []
            for record in data[:100]:
                sensors = record['sensors']
                features.append([
                    sensors['temperature']['value'],
                    sensors['vibration']['value'],
                    sensors['pressure']['value'],
                    sensors['current']['value'],
                    sensors['rpm']['value']
                ])
            
            X = np.array(features)
            assert not np.isnan(X).any(), "Found NaN values in features"
    
    def test_class_balance(self):
        """Check class distribution"""
        data_dir = Path("data/raw")
        files = list(data_dir.glob("historical_*.json"))
        
        if files:
            with open(files[0], 'r') as f:
                data = json.load(f)
            
            failures = sum(1 for r in data if r['is_failing'])
            total = len(data)
            failure_rate = failures / total
            
            assert 0.05 <= failure_rate <= 0.30, \
                f"Unusual class distribution: {failure_rate:.2%} failures"


class TestDataSplitting:
    """Test train/test splitting"""
    
    def test_split_preserves_size(self):
        """Verify splitting preserves total samples"""
        from sklearn.model_selection import train_test_split
        
        X = np.random.rand(100, 5)
        y = np.random.randint(0, 2, 100)
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        assert len(X_train) + len(X_test) == len(X), "Split size mismatch"
        assert len(y_train) + len(y_test) == len(y), "Label split size mismatch"
    
    def test_split_ratio(self):
        """Verify correct split ratio"""
        from sklearn.model_selection import train_test_split
        
        X = np.random.rand(100, 5)
        y = np.random.randint(0, 2, 100)
        
        X_train, X_test, _, _ = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        assert len(X_test) == 20, "Test set should be 20% of data"
        assert len(X_train) == 80, "Train set should be 80% of data"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
