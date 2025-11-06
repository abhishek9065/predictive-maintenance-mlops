"""
Comprehensive End-to-End Test for MLOps Predictive Maintenance Project
Tests all components: Data, Models, API, Monitoring, Edge Deployment
"""

import os
import sys
import json
import time
import requests
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

class MLOpsProjectTester:
    """Comprehensive tester for the entire MLOps project"""
    
    def __init__(self):
        self.api_url = "http://localhost:8000"
        self.test_results = {
            'timestamp': datetime.now().isoformat(),
            'tests_passed': 0,
            'tests_failed': 0,
            'tests_total': 0,
            'details': []
        }
        
    def print_header(self, text):
        """Print formatted header"""
        print("\n" + "="*80)
        print(f"  {text}")
        print("="*80 + "\n")
        
    def print_test(self, test_name, status, message=""):
        """Print test result"""
        symbol = "✅" if status else "❌"
        self.test_results['tests_total'] += 1
        if status:
            self.test_results['tests_passed'] += 1
        else:
            self.test_results['tests_failed'] += 1
        
        self.test_results['details'].append({
            'test': test_name,
            'status': 'PASS' if status else 'FAIL',
            'message': message
        })
        
        print(f"{symbol} {test_name}: {'PASS' if status else 'FAIL'}")
        if message:
            print(f"   → {message}")
    
    # ========================================================================
    # 1. DATA QUALITY TESTS
    # ========================================================================
    
    def test_data_files(self):
        """Test if all data files exist and are valid"""
        self.print_header("1. DATA QUALITY TESTS")
        
        required_files = {
            'data/full_dataset.csv': 20000,
            'data/train.csv': 15000,  # Augmented
            'data/test.csv': 4000,
            'data/validation.csv': 2000,
        }
        
        for filepath, min_samples in required_files.items():
            try:
                if not os.path.exists(filepath):
                    self.print_test(f"Data file exists: {filepath}", False, "File not found")
                    continue
                
                df = pd.read_csv(filepath)
                samples = len(df)
                
                if samples >= min_samples:
                    self.print_test(
                        f"Data file valid: {filepath}",
                        True,
                        f"{samples:,} samples (≥ {min_samples:,} required)"
                    )
                else:
                    self.print_test(
                        f"Data file valid: {filepath}",
                        False,
                        f"Only {samples} samples, need {min_samples}"
                    )
                
                # Check for required columns
                required_cols = ['temperature', 'vibration', 'pressure', 'rpm', 'current', 'failure']
                missing_cols = [col for col in required_cols if col not in df.columns]
                
                if not missing_cols:
                    self.print_test(
                        f"Required columns present: {filepath}",
                        True,
                        f"All {len(required_cols)} columns found"
                    )
                else:
                    self.print_test(
                        f"Required columns present: {filepath}",
                        False,
                        f"Missing: {missing_cols}"
                    )
                
                # Check data quality
                missing_values = df.isnull().sum().sum()
                duplicates = df.duplicated().sum()
                
                self.print_test(
                    f"Data quality: {filepath}",
                    missing_values == 0 and duplicates <= 1,
                    f"Missing: {missing_values}, Duplicates: {duplicates}"
                )
                
            except Exception as e:
                self.print_test(f"Data file valid: {filepath}", False, str(e))
    
    # ========================================================================
    # 2. MODEL TESTS
    # ========================================================================
    
    def test_models(self):
        """Test if trained models exist and are loadable"""
        self.print_header("2. MODEL TESTS")
        
        import pickle
        
        # Check for model files
        model_dir = Path("models/katib")
        if not model_dir.exists():
            self.print_test("Model directory exists", False, "models/katib not found")
            return
        
        model_files = list(model_dir.glob("*.pkl"))
        
        if len(model_files) > 0:
            self.print_test(
                "Model files exist",
                True,
                f"Found {len(model_files)} model(s)"
            )
        else:
            self.print_test("Model files exist", False, "No .pkl files found")
            return
        
        # Test loading the latest model
        latest_model = sorted(model_files)[-1]
        try:
            with open(latest_model, 'rb') as f:
                model = pickle.load(f)
            
            self.print_test(
                f"Model loadable: {latest_model.name}",
                True,
                f"Type: {type(model).__name__}"
            )
            
            # Test model metrics file
            metrics_file = latest_model.with_name(latest_model.stem + '_metrics.json')
            if metrics_file.exists():
                with open(metrics_file, 'r') as f:
                    metrics = json.load(f)
                
                accuracy = metrics.get('accuracy', 0)
                self.print_test(
                    f"Model accuracy check",
                    accuracy >= 0.90,
                    f"Accuracy: {accuracy:.4f} ({'✓' if accuracy >= 0.90 else 'Below 90%'})"
                )
                self.print_test(
                    f"Model metrics complete",
                    all(k in metrics for k in ['accuracy', 'precision', 'recall', 'f1']),
                    f"Precision: {metrics.get('precision', 0):.4f}, Recall: {metrics.get('recall', 0):.4f}, F1: {metrics.get('f1', 0):.4f}"
                )
            else:
                self.print_test("Model metrics file exists", False, f"{metrics_file.name} not found")
            
        except Exception as e:
            self.print_test(f"Model loadable: {latest_model.name}", False, str(e))
    
    # ========================================================================
    # 3. API TESTS
    # ========================================================================
    
    def test_api(self):
        """Test FastAPI endpoints"""
        self.print_header("3. API TESTS")
        
        # Test 1: Health endpoint
        try:
            response = requests.get(f"{self.api_url}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.print_test(
                    "API Health endpoint",
                    data.get('status') == 'healthy',
                    f"Status: {data.get('status')}, Model: {data.get('model_loaded', False)}"
                )
            else:
                self.print_test("API Health endpoint", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.print_test("API Health endpoint", False, str(e))
        
        # Test 2: Root endpoint
        try:
            response = requests.get(f"{self.api_url}/", timeout=5)
            self.print_test(
                "API Root endpoint",
                response.status_code == 200,
                f"HTTP {response.status_code}"
            )
        except Exception as e:
            self.print_test("API Root endpoint", False, str(e))
        
        # Test 3: Model info endpoint
        try:
            response = requests.get(f"{self.api_url}/model/info", timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.print_test(
                    "API Model info endpoint",
                    'accuracy' in data,
                    f"Accuracy: {data.get('accuracy', 'N/A')}"
                )
            else:
                self.print_test("API Model info endpoint", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.print_test("API Model info endpoint", False, str(e))
        
        # Test 4: Prediction endpoint
        try:
            test_data = {
                "temperature": 75.0,
                "vibration": 0.5,
                "pressure": 95.0,
                "rpm": 1450.0,
                "current": 9.0
            }
            
            response = requests.post(
                f"{self.api_url}/predict",
                json=test_data,
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                self.print_test(
                    "API Prediction endpoint",
                    'prediction' in data and 'probability' in data,
                    f"Prediction: {data.get('prediction')}, Probability: {data.get('probability', 0):.4f}"
                )
            else:
                self.print_test("API Prediction endpoint", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.print_test("API Prediction endpoint", False, str(e))
        
        # Test 5: Metrics endpoint
        try:
            response = requests.get(f"{self.api_url}/metrics", timeout=5)
            self.print_test(
                "API Metrics endpoint (Prometheus)",
                response.status_code == 200,
                f"HTTP {response.status_code}, Content-Type: {response.headers.get('content-type', 'N/A')}"
            )
        except Exception as e:
            self.print_test("API Metrics endpoint", False, str(e))
    
    # ========================================================================
    # 4. EDGE DEPLOYMENT TESTS
    # ========================================================================
    
    def test_edge_deployment(self):
        """Test TensorFlow Lite edge deployment"""
        self.print_header("4. EDGE DEPLOYMENT TESTS")
        
        # Check if TFLite model exists
        tflite_models = list(Path("models").glob("*.tflite"))
        
        if len(tflite_models) > 0:
            tflite_model = tflite_models[0]
            self.print_test(
                "TFLite model exists",
                True,
                f"Found: {tflite_model.name} ({tflite_model.stat().st_size / 1024:.2f} KB)"
            )
            
            # Test TFLite model loading
            try:
                import tensorflow as tf
                interpreter = tf.lite.Interpreter(model_path=str(tflite_model))
                interpreter.allocate_tensors()
                
                input_details = interpreter.get_input_details()
                output_details = interpreter.get_output_details()
                
                self.print_test(
                    "TFLite model loadable",
                    True,
                    f"Input shape: {input_details[0]['shape']}, Output shape: {output_details[0]['shape']}"
                )
            except Exception as e:
                self.print_test("TFLite model loadable", False, str(e))
        else:
            self.print_test("TFLite model exists", False, "No .tflite files found in models/")
    
    # ========================================================================
    # 5. MONITORING & OBSERVABILITY TESTS
    # ========================================================================
    
    def test_monitoring(self):
        """Test monitoring and observability components"""
        self.print_header("5. MONITORING & OBSERVABILITY TESTS")
        
        # Check if Evidently AI is installed
        try:
            import evidently
            self.print_test(
                "Evidently AI installed",
                True,
                f"Version: {evidently.__version__}"
            )
        except ImportError:
            self.print_test("Evidently AI installed", False, "Package not found")
        
        # Check monitoring scripts
        monitoring_files = [
            'src/monitoring/evidently_monitor.py',
            'src/monitoring/prometheus_metrics.py'
        ]
        
        for filepath in monitoring_files:
            exists = os.path.exists(filepath)
            self.print_test(
                f"Monitoring script: {Path(filepath).name}",
                exists,
                "Found" if exists else "Not found"
            )
    
    # ========================================================================
    # 6. CI/CD TESTS
    # ========================================================================
    
    def test_cicd(self):
        """Test CI/CD configuration"""
        self.print_header("6. CI/CD & DEPLOYMENT TESTS")
        
        # Check Jenkins pipeline
        jenkins_file = "Jenkinsfile"
        if os.path.exists(jenkins_file):
            with open(jenkins_file, 'r') as f:
                content = f.read()
            
            required_stages = ['Build', 'Test', 'Train', 'Deploy']
            stages_found = sum(1 for stage in required_stages if stage in content)
            
            self.print_test(
                "Jenkins pipeline configured",
                stages_found >= 3,
                f"{stages_found}/{len(required_stages)} required stages found"
            )
        else:
            self.print_test("Jenkins pipeline configured", False, "Jenkinsfile not found")
        
        # Check Docker files
        docker_files = ['Dockerfile', 'docker/Dockerfile.api', 'docker/Dockerfile.training']
        docker_count = sum(1 for f in docker_files if os.path.exists(f))
        
        self.print_test(
            "Docker configuration",
            docker_count > 0,
            f"{docker_count}/{len(docker_files)} Dockerfiles found"
        )
        
        # Check Kubernetes manifests
        k8s_dir = Path("k8s")
        if k8s_dir.exists():
            k8s_files = list(k8s_dir.glob("*.yaml"))
            self.print_test(
                "Kubernetes manifests",
                len(k8s_files) > 0,
                f"{len(k8s_files)} YAML files found"
            )
        else:
            self.print_test("Kubernetes manifests", False, "k8s/ directory not found")
    
    # ========================================================================
    # 7. SECURITY & GOVERNANCE TESTS
    # ========================================================================
    
    def test_security(self):
        """Test security and governance components"""
        self.print_header("7. SECURITY & GOVERNANCE TESTS")
        
        # Check OPA policies
        opa_dir = Path("opa")
        if opa_dir.exists():
            opa_files = list(opa_dir.glob("*.rego"))
            self.print_test(
                "OPA security policies",
                len(opa_files) >= 2,
                f"{len(opa_files)} policy files found"
            )
        else:
            self.print_test("OPA security policies", False, "opa/ directory not found")
        
        # Check RBAC configuration
        rbac_file = "k8s/rbac.yaml"
        self.print_test(
            "Kubernetes RBAC configured",
            os.path.exists(rbac_file),
            "rbac.yaml found" if os.path.exists(rbac_file) else "rbac.yaml not found"
        )
    
    # ========================================================================
    # 8. DOCUMENTATION TESTS
    # ========================================================================
    
    def test_documentation(self):
        """Test documentation completeness"""
        self.print_header("8. DOCUMENTATION TESTS")
        
        doc_files = {
            'README.md': 'Main documentation',
            'FIXED_README.md': 'Setup guide',
            'DATA_IMPROVEMENTS_SUMMARY.md': 'Data improvements',
            'WINDOWS_API_TESTING_GUIDE.md': 'Windows testing guide',
            'DATA_GENERATION_COMPLETE.md': 'Data generation guide'
        }
        
        for filepath, description in doc_files.items():
            exists = os.path.exists(filepath)
            if exists:
                size = os.path.getsize(filepath) / 1024
                self.print_test(
                    f"Documentation: {filepath}",
                    size > 1,
                    f"{size:.1f} KB - {description}"
                )
            else:
                self.print_test(f"Documentation: {filepath}", False, "Not found")
    
    # ========================================================================
    # 9. PERFORMANCE TESTS
    # ========================================================================
    
    def test_performance(self):
        """Test API performance"""
        self.print_header("9. PERFORMANCE TESTS")
        
        # Test API response time
        test_data = {
            "temperature": 75.0,
            "vibration": 0.5,
            "pressure": 95.0,
            "rpm": 1450.0,
            "current": 9.0
        }
        
        try:
            # Warmup request
            requests.post(f"{self.api_url}/predict", json=test_data, timeout=5)
            
            # Measure response time
            times = []
            for _ in range(10):
                start = time.time()
                response = requests.post(f"{self.api_url}/predict", json=test_data, timeout=5)
                elapsed = (time.time() - start) * 1000  # ms
                if response.status_code == 200:
                    times.append(elapsed)
            
            if times:
                avg_time = np.mean(times)
                max_time = np.max(times)
                
                self.print_test(
                    "API response time",
                    avg_time < 100,  # Should be under 100ms
                    f"Avg: {avg_time:.2f}ms, Max: {max_time:.2f}ms (10 requests)"
                )
        except Exception as e:
            self.print_test("API response time", False, str(e))
        
        # Test model inference time
        try:
            import pickle
            model_files = list(Path("models/katib").glob("*.pkl"))
            if model_files:
                latest_model = sorted(model_files)[-1]
                with open(latest_model, 'rb') as f:
                    model = pickle.load(f)
                
                # Test inference
                X_test = np.array([[75.0, 0.5, 95.0, 1450.0, 9.0]])
                
                times = []
                for _ in range(100):
                    start = time.time()
                    _ = model.predict(X_test)
                    elapsed = (time.time() - start) * 1000
                    times.append(elapsed)
                
                avg_time = np.mean(times)
                self.print_test(
                    "Model inference time",
                    avg_time < 10,  # Should be under 10ms
                    f"Avg: {avg_time:.3f}ms (100 predictions)"
                )
        except Exception as e:
            self.print_test("Model inference time", False, str(e))
    
    # ========================================================================
    # 10. INTEGRATION TESTS
    # ========================================================================
    
    def test_integration(self):
        """Test end-to-end integration"""
        self.print_header("10. INTEGRATION TESTS")
        
        # Test full prediction pipeline
        try:
            # Load test data
            if os.path.exists('data/test.csv'):
                df = pd.read_csv('data/test.csv')
                
                # Take 5 random samples
                samples = df.sample(5)
                
                correct_predictions = 0
                for idx, row in samples.iterrows():
                    test_data = {
                        "temperature": float(row['temperature']),
                        "vibration": float(row['vibration']),
                        "pressure": float(row['pressure']),
                        "rpm": float(row['rpm']),
                        "current": float(row['current'])
                    }
                    
                    response = requests.post(
                        f"{self.api_url}/predict",
                        json=test_data,
                        timeout=5
                    )
                    
                    if response.status_code == 200:
                        prediction = response.json()['prediction']
                        actual = int(row['failure'])
                        if prediction == actual:
                            correct_predictions += 1
                
                self.print_test(
                    "End-to-end prediction pipeline",
                    correct_predictions >= 3,
                    f"{correct_predictions}/5 predictions correct"
                )
            else:
                self.print_test("End-to-end prediction pipeline", False, "Test data not found")
        except Exception as e:
            self.print_test("End-to-end prediction pipeline", False, str(e))
    
    # ========================================================================
    # MAIN TEST RUNNER
    # ========================================================================
    
    def run_all_tests(self):
        """Run all tests"""
        self.print_header("MLOps PREDICTIVE MAINTENANCE - COMPREHENSIVE TEST SUITE")
        print(f"Timestamp: {self.test_results['timestamp']}")
        print(f"API URL: {self.api_url}")
        
        # Run all test suites
        self.test_data_files()
        self.test_models()
        self.test_api()
        self.test_edge_deployment()
        self.test_monitoring()
        self.test_cicd()
        self.test_security()
        self.test_documentation()
        self.test_performance()
        self.test_integration()
        
        # Print summary
        self.print_summary()
        
        # Save results
        self.save_results()
    
    def print_summary(self):
        """Print test summary"""
        self.print_header("TEST SUMMARY")
        
        total = self.test_results['tests_total']
        passed = self.test_results['tests_passed']
        failed = self.test_results['tests_failed']
        
        pass_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"Total Tests:  {total}")
        print(f"✅ Passed:    {passed}")
        print(f"❌ Failed:    {failed}")
        print(f"Pass Rate:    {pass_rate:.1f}%")
        
        if pass_rate >= 90:
            status = "🎉 EXCELLENT - Production Ready!"
            color = "green"
        elif pass_rate >= 75:
            status = "✅ GOOD - Minor improvements needed"
            color = "yellow"
        elif pass_rate >= 50:
            status = "⚠️  FAIR - Significant improvements needed"
            color = "orange"
        else:
            status = "❌ POOR - Major issues to resolve"
            color = "red"
        
        print(f"\nOverall Status: {status}")
        
        # List failed tests
        if failed > 0:
            print("\n" + "="*80)
            print("  FAILED TESTS")
            print("="*80)
            for detail in self.test_results['details']:
                if detail['status'] == 'FAIL':
                    print(f"❌ {detail['test']}")
                    if detail['message']:
                        print(f"   → {detail['message']}")
        
        print("\n" + "="*80)
    
    def save_results(self):
        """Save test results to JSON"""
        output_file = "test_results.json"
        with open(output_file, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        
        print(f"\n📄 Test results saved to: {output_file}")
        print("="*80 + "\n")


def main():
    """Main entry point"""
    tester = MLOpsProjectTester()
    tester.run_all_tests()


if __name__ == "__main__":
    main()
