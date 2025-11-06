"""
Unit Tests for Model Training and Evaluation
"""

import pytest
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score


class TestModelTraining:
    """Test model training pipeline"""
    
    @pytest.fixture
    def sample_dataset(self):
        """Create sample dataset for testing"""
        np.random.seed(42)
        n_samples = 200
        
        # Create synthetic data
        X = np.random.rand(n_samples, 5)
        y = (X[:, 0] + X[:, 1] > 1.0).astype(int)  # Simple decision rule
        
        return X, y
    
    def test_model_initialization(self):
        """Test model can be initialized"""
        model = RandomForestClassifier(n_estimators=10, random_state=42)
        assert model is not None
        assert model.n_estimators == 10
    
    def test_model_training(self, sample_dataset):
        """Test model can be trained"""
        X, y = sample_dataset
        model = RandomForestClassifier(n_estimators=10, random_state=42)
        
        model.fit(X, y)
        assert hasattr(model, 'estimators_'), "Model should have trained estimators"
    
    def test_model_prediction(self, sample_dataset):
        """Test model can make predictions"""
        X, y = sample_dataset
        model = RandomForestClassifier(n_estimators=10, random_state=42)
        model.fit(X, y)
        
        predictions = model.predict(X)
        assert len(predictions) == len(y), "Should predict for all samples"
        assert all(p in [0, 1] for p in predictions), "Predictions should be binary"
    
    def test_model_probability(self, sample_dataset):
        """Test model can output probabilities"""
        X, y = sample_dataset
        model = RandomForestClassifier(n_estimators=10, random_state=42)
        model.fit(X, y)
        
        probabilities = model.predict_proba(X)
        assert probabilities.shape == (len(X), 2), "Should have 2 class probabilities"
        assert np.allclose(probabilities.sum(axis=1), 1.0), "Probabilities should sum to 1"


class TestModelEvaluation:
    """Test model evaluation metrics"""
    
    @pytest.fixture
    def predictions(self):
        """Create sample predictions for testing"""
        y_true = np.array([0, 0, 1, 1, 0, 1, 0, 1])
        y_pred = np.array([0, 0, 1, 0, 0, 1, 0, 1])
        return y_true, y_pred
    
    def test_accuracy_calculation(self, predictions):
        """Test accuracy metric"""
        y_true, y_pred = predictions
        accuracy = accuracy_score(y_true, y_pred)
        
        assert 0 <= accuracy <= 1, "Accuracy should be between 0 and 1"
        assert accuracy == 0.875, "Accuracy calculation incorrect"
    
    def test_precision_calculation(self, predictions):
        """Test precision metric"""
        y_true, y_pred = predictions
        precision = precision_score(y_true, y_pred)
        
        assert 0 <= precision <= 1, "Precision should be between 0 and 1"
    
    def test_recall_calculation(self, predictions):
        """Test recall metric"""
        y_true, y_pred = predictions
        recall = recall_score(y_true, y_pred)
        
        assert 0 <= recall <= 1, "Recall should be between 0 and 1"
    
    def test_f1_calculation(self, predictions):
        """Test F1 score metric"""
        y_true, y_pred = predictions
        f1 = f1_score(y_true, y_pred)
        
        assert 0 <= f1 <= 1, "F1 score should be between 0 and 1"


class TestModelPerformance:
    """Test model performance requirements"""
    
    def test_model_meets_accuracy_threshold(self):
        """Test model achieves minimum accuracy"""
        np.random.seed(42)
        
        # Create linearly separable data
        X = np.random.rand(1000, 5)
        y = (X[:, 0] + X[:, 1] > 1.0).astype(int)
        
        from sklearn.model_selection import train_test_split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        model = RandomForestClassifier(n_estimators=50, random_state=42)
        model.fit(X_train, y_train)
        
        y_pred = model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        assert accuracy >= 0.7, f"Model accuracy {accuracy:.2%} below 70% threshold"
    
    def test_model_training_speed(self):
        """Test model trains in reasonable time"""
        import time
        
        X = np.random.rand(1000, 5)
        y = np.random.randint(0, 2, 1000)
        
        model = RandomForestClassifier(n_estimators=10, random_state=42, n_jobs=-1)
        
        start_time = time.time()
        model.fit(X, y)
        training_time = time.time() - start_time
        
        assert training_time < 5.0, f"Training took {training_time:.2f}s, should be < 5s"


class TestFeatureImportance:
    """Test feature importance extraction"""
    
    def test_feature_importance_exists(self):
        """Test model provides feature importance"""
        X = np.random.rand(100, 5)
        y = np.random.randint(0, 2, 100)
        
        model = RandomForestClassifier(n_estimators=10, random_state=42)
        model.fit(X, y)
        
        assert hasattr(model, 'feature_importances_'), "Model should have feature importances"
        assert len(model.feature_importances_) == 5, "Should have importance for each feature"
    
    def test_feature_importance_sums_to_one(self):
        """Test feature importances sum to 1"""
        X = np.random.rand(100, 5)
        y = np.random.randint(0, 2, 100)
        
        model = RandomForestClassifier(n_estimators=10, random_state=42)
        model.fit(X, y)
        
        importance_sum = model.feature_importances_.sum()
        assert np.isclose(importance_sum, 1.0), "Feature importances should sum to 1"


class TestModelPersistence:
    """Test model saving and loading"""
    
    def test_model_can_be_saved(self, tmp_path):
        """Test model can be saved to file"""
        import joblib
        
        X = np.random.rand(100, 5)
        y = np.random.randint(0, 2, 100)
        
        model = RandomForestClassifier(n_estimators=10, random_state=42)
        model.fit(X, y)
        
        model_path = tmp_path / "test_model.pkl"
        joblib.dump(model, model_path)
        
        assert model_path.exists(), "Model file should be created"
    
    def test_model_can_be_loaded(self, tmp_path):
        """Test saved model can be loaded"""
        import joblib
        
        X = np.random.rand(100, 5)
        y = np.random.randint(0, 2, 100)
        
        # Train and save model
        model = RandomForestClassifier(n_estimators=10, random_state=42)
        model.fit(X, y)
        
        model_path = tmp_path / "test_model.pkl"
        joblib.dump(model, model_path)
        
        # Load model
        loaded_model = joblib.load(model_path)
        
        # Test predictions match
        original_pred = model.predict(X[:5])
        loaded_pred = loaded_model.predict(X[:5])
        
        assert np.array_equal(original_pred, loaded_pred), \
            "Loaded model predictions should match original"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
