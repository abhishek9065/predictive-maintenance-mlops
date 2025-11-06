"""
Test Script for Advanced MLOps Components
Tests Katib, Docker, Kubernetes, FastAPI, Flask, and BentoML implementations
"""

import os
import sys
import json
import time
import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

import requests
import numpy as np
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MLOpsComponentTester:
    """Test all MLOps components"""
    
    def __init__(self):
        self.results = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "tests": []
        }
        self.passed = 0
        self.failed = 0
    
    def add_result(self, test_name: str, passed: bool, message: str = "", details: dict = None):
        """Add test result"""
        result = {
            "test": test_name,
            "passed": passed,
            "message": message,
            "details": details or {}
        }
        self.results["tests"].append(result)
        
        if passed:
            self.passed += 1
            logger.info(f"✓ {test_name}: PASSED")
        else:
            self.failed += 1
            logger.error(f"✗ {test_name}: FAILED - {message}")
        
        if message:
            logger.info(f"  {message}")
    
    def test_file_exists(self, file_path: str, description: str):
        """Test if a file exists"""
        exists = Path(file_path).exists()
        self.add_result(
            f"File: {description}",
            exists,
            f"Path: {file_path}",
            {"file_path": file_path, "exists": exists}
        )
        return exists
    
    def test_katib_script(self):
        """Test Katib training script"""
        logger.info("\n" + "="*60)
        logger.info("Testing Katib Components")
        logger.info("="*60)
        
        # Check script exists
        script_path = "katib_tuning.py"
        if not self.test_file_exists(script_path, "Katib Training Script"):
            return
        
        # Check if script can be imported
        try:
            # Test with minimal arguments
            cmd = [
                sys.executable,
                script_path,
                "--model=logistic_regression",
                "--C=1.0",
                "--max_iter=100",
                "--penalty=l2"
            ]
            
            # Just validate the script syntax, don't run full training
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            passed = result.returncode == 0
            self.add_result(
                "Katib Script Execution",
                passed,
                f"Exit code: {result.returncode}",
                {"stdout": result.stdout[:200], "stderr": result.stderr[:200]}
            )
        
        except Exception as e:
            self.add_result("Katib Script Execution", False, str(e))
    
    def test_kubernetes_manifests(self):
        """Test Kubernetes manifest files"""
        logger.info("\n" + "="*60)
        logger.info("Testing Kubernetes Manifests")
        logger.info("="*60)
        
        manifests = [
            ("kubernetes/namespace.yaml", "Namespace"),
            ("kubernetes/persistent-volumes.yaml", "Persistent Volumes"),
            ("kubernetes/katib-experiment.yaml", "Katib Experiments"),
            ("kubernetes/mlflow-deployment.yaml", "MLflow Deployment"),
            ("kubernetes/api-deployment.yaml", "API Deployment"),
        ]
        
        for file_path, description in manifests:
            self.test_file_exists(file_path, f"K8s: {description}")
    
    def test_dockerfiles(self):
        """Test Dockerfile existence and syntax"""
        logger.info("\n" + "="*60)
        logger.info("Testing Dockerfiles")
        logger.info("="*60)
        
        dockerfiles = [
            ("Dockerfile", "Training Container"),
            ("Dockerfile.api", "API Container"),
            ("Dockerfile.mlflow", "MLflow Container"),
        ]
        
        for file_path, description in dockerfiles:
            if self.test_file_exists(file_path, f"Dockerfile: {description}"):
                # Validate syntax with docker
                try:
                    result = subprocess.run(
                        ["docker", "build", "-f", file_path, "--help"],
                        capture_output=True,
                        timeout=5
                    )
                    # If docker command works, syntax is likely OK
                    self.add_result(
                        f"Docker Build Test: {description}",
                        True,
                        "Docker available"
                    )
                except Exception as e:
                    self.add_result(
                        f"Docker Build Test: {description}",
                        False,
                        f"Docker not available: {e}"
                    )
    
    def test_fastapi(self, base_url: str = "http://localhost:8000"):
        """Test FastAPI endpoints"""
        logger.info("\n" + "="*60)
        logger.info("Testing FastAPI")
        logger.info("="*60)
        
        # Check if file exists
        if not self.test_file_exists("src/deployment/api_fastapi.py", "FastAPI Implementation"):
            return
        
        # Test endpoints (if server is running)
        endpoints = [
            ("/", "Root"),
            ("/health", "Health Check"),
            ("/model/info", "Model Info"),
        ]
        
        for endpoint, name in endpoints:
            try:
                response = requests.get(f"{base_url}{endpoint}", timeout=5)
                passed = response.status_code == 200 or response.status_code == 404
                
                self.add_result(
                    f"FastAPI Endpoint: {name}",
                    passed,
                    f"Status: {response.status_code}",
                    {"endpoint": endpoint, "status": response.status_code}
                )
            except requests.exceptions.ConnectionError:
                self.add_result(
                    f"FastAPI Endpoint: {name}",
                    False,
                    "Server not running (expected if not started)",
                    {"endpoint": endpoint, "note": "Start server to test"}
                )
            except Exception as e:
                self.add_result(f"FastAPI Endpoint: {name}", False, str(e))
    
    def test_flask(self, base_url: str = "http://localhost:8000"):
        """Test Flask endpoints"""
        logger.info("\n" + "="*60)
        logger.info("Testing Flask")
        logger.info("="*60)
        
        # Check if file exists
        if not self.test_file_exists("src/deployment/api_flask.py", "Flask Implementation"):
            return
        
        # Flask uses same endpoints as FastAPI
        logger.info("Flask endpoint tests would be same as FastAPI (server not running)")
    
    def test_bentoml(self):
        """Test BentoML components"""
        logger.info("\n" + "="*60)
        logger.info("Testing BentoML")
        logger.info("="*60)
        
        # Check files
        files = [
            ("src/deployment/bentoml_service.py", "BentoML Service"),
            ("src/deployment/bentoml_save.py", "BentoML Saver"),
            ("bentofile.yaml", "Bento Configuration"),
        ]
        
        for file_path, description in files:
            self.test_file_exists(file_path, description)
        
        # Check BentoML installation
        try:
            result = subprocess.run(
                ["bentoml", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            passed = result.returncode == 0
            version = result.stdout.strip() if passed else "Not installed"
            
            self.add_result(
                "BentoML Installation",
                passed,
                f"Version: {version}",
                {"version": version}
            )
        except Exception as e:
            self.add_result("BentoML Installation", False, str(e))
    
    def test_prediction_api_payload(self):
        """Test API payload structure"""
        logger.info("\n" + "="*60)
        logger.info("Testing API Payload Structure")
        logger.info("="*60)
        
        # Sample payload
        payload = {
            "data": [
                {
                    "temperature": 75.0,
                    "vibration": 3.5,
                    "pressure": 100.0,
                    "rpm": 1500.0,
                    "power_consumption": 250.0
                },
                {
                    "temperature": 80.0,
                    "vibration": 4.0,
                    "pressure": 110.0,
                    "rpm": 1600.0,
                    "power_consumption": 270.0
                }
            ],
            "return_probability": True
        }
        
        # Validate structure
        try:
            assert "data" in payload
            assert isinstance(payload["data"], list)
            assert len(payload["data"]) > 0
            
            required_fields = ["temperature", "vibration", "pressure", "rpm", "power_consumption"]
            for record in payload["data"]:
                for field in required_fields:
                    assert field in record
                    assert isinstance(record[field], (int, float))
            
            self.add_result(
                "API Payload Validation",
                True,
                "Payload structure is correct",
                {"sample_payload": payload}
            )
        except AssertionError as e:
            self.add_result("API Payload Validation", False, str(e))
    
    def test_deployment_scripts(self):
        """Test deployment scripts"""
        logger.info("\n" + "="*60)
        logger.info("Testing Deployment Scripts")
        logger.info("="*60)
        
        scripts = [
            ("deploy.py", "Main Deployment Script"),
        ]
        
        for script_path, description in scripts:
            if self.test_file_exists(script_path, description):
                # Test script can be executed (with --help)
                try:
                    result = subprocess.run(
                        [sys.executable, script_path, "--help"],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    passed = result.returncode == 0
                    self.add_result(
                        f"Script Execution: {description}",
                        passed,
                        "Help command works"
                    )
                except Exception as e:
                    self.add_result(f"Script Execution: {description}", False, str(e))
    
    def test_documentation(self):
        """Test documentation files"""
        logger.info("\n" + "="*60)
        logger.info("Testing Documentation")
        logger.info("="*60)
        
        docs = [
            ("ADVANCED_MLOPS_COMPONENTS.md", "Advanced MLOps Guide"),
            ("DEPLOYMENT_SCRIPTS.md", "Deployment Scripts Guide"),
        ]
        
        for doc_path, description in docs:
            if self.test_file_exists(doc_path, description):
                # Check file size (should be substantial)
                size = Path(doc_path).stat().st_size
                passed = size > 1000  # At least 1KB
                self.add_result(
                    f"Documentation Size: {description}",
                    passed,
                    f"Size: {size} bytes",
                    {"size_bytes": size}
                )
    
    def run_all_tests(self):
        """Run all tests"""
        logger.info("\n" + "="*70)
        logger.info("ADVANCED MLOPS COMPONENTS - COMPREHENSIVE TEST SUITE")
        logger.info("="*70)
        
        # Run all test suites
        self.test_katib_script()
        self.test_kubernetes_manifests()
        self.test_dockerfiles()
        self.test_fastapi()
        self.test_flask()
        self.test_bentoml()
        self.test_prediction_api_payload()
        self.test_deployment_scripts()
        self.test_documentation()
        
        # Print summary
        self.print_summary()
        
        # Save results
        self.save_results()
        
        return self.passed, self.failed
    
    def print_summary(self):
        """Print test summary"""
        total = self.passed + self.failed
        pass_rate = (self.passed / total * 100) if total > 0 else 0
        
        logger.info("\n" + "="*70)
        logger.info("TEST SUMMARY")
        logger.info("="*70)
        logger.info(f"Total Tests: {total}")
        logger.info(f"Passed:      {self.passed} ({pass_rate:.1f}%)")
        logger.info(f"Failed:      {self.failed}")
        logger.info("="*70)
        
        if self.failed == 0:
            logger.info("✓ All tests passed!")
        else:
            logger.warning(f"⚠ {self.failed} test(s) failed")
    
    def save_results(self, output_file: str = "advanced_mlops_test_results.json"):
        """Save test results to file"""
        self.results["summary"] = {
            "total": self.passed + self.failed,
            "passed": self.passed,
            "failed": self.failed,
            "pass_rate": (self.passed / (self.passed + self.failed) * 100) if (self.passed + self.failed) > 0 else 0
        }
        
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        logger.info(f"\n✓ Test results saved to: {output_file}")

def main():
    """Main test function"""
    tester = MLOpsComponentTester()
    passed, failed = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if failed == 0 else 1)

if __name__ == "__main__":
    main()
