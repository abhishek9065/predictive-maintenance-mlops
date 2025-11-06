"""
Simplified Deployment Manager (No Docker Required)
Deploys ML components locally without Docker Desktop
"""

import os
import sys
import subprocess
import json
from pathlib import Path
import time

class SimpleDeploymentManager:
    """Deploy ML components locally"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        
    def check_environment(self):
        """Check if environment is set up correctly"""
        print("🔍 Checking environment...")
        
        # Check Python
        python_version = sys.version.split()[0]
        print(f"✅ Python: {python_version}")
        
        # Check required packages
        required_packages = [
            'fastapi', 'uvicorn', 'flask', 'bentoml', 
            'mlflow', 'joblib', 'prometheus_client'
        ]
        
        missing = []
        for package in required_packages:
            try:
                __import__(package)
                print(f"✅ {package}")
            except ImportError:
                print(f"❌ {package} - MISSING")
                missing.append(package)
        
        if missing:
            print(f"\n⚠️ Missing packages: {', '.join(missing)}")
            print(f"Install with: pip install {' '.join(missing)}")
            return False
        
        return True
    
    def generate_data(self):
        """Generate sample data for training"""
        print("\n📊 Generating sample data...")
        
        try:
            subprocess.run([
                sys.executable, "generate_sample_data.py",
                "--samples", "2000",
                "--output", "data"
            ], check=True)
            print("✅ Sample data generated")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to generate data: {e}")
            return False
    
    def train_model(self):
        """Train a quick model using Katib script"""
        print("\n🎯 Training model with Katib hyperparameter tuning...")
        
        # Check if data exists
        if not Path("data/train.csv").exists():
            print("⚠️ No training data found. Generating...")
            if not self.generate_data():
                return False
        
        try:
            # Train with different models
            models = ['random_forest', 'gradient_boosting', 'logistic_regression']
            
            for model_type in models:
                print(f"\n🔧 Training {model_type}...")
                result = subprocess.run([
                    sys.executable, "katib_tuning.py",
                    f"--model={model_type}",
                    "--n_estimators=100",
                    "--max_depth=10",
                    "--learning_rate=0.1"
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    print(f"✅ {model_type} trained successfully")
                    # Parse metrics from output
                    for line in result.stdout.split('\n'):
                        if 'accuracy' in line.lower():
                            print(f"   {line}")
                else:
                    print(f"⚠️ {model_type} training had issues")
            
            return True
        except Exception as e:
            print(f"❌ Training failed: {e}")
            return False
    
    def start_fastapi(self, port=8000):
        """Start FastAPI server"""
        print(f"\n🚀 Starting FastAPI server on port {port}...")
        print(f"   Docs: http://localhost:{port}/docs")
        print(f"   Health: http://localhost:{port}/health")
        print(f"   Press Ctrl+C to stop")
        
        try:
            subprocess.run([
                sys.executable, "-m", "uvicorn",
                "src.deployment.api_fastapi:app",
                "--reload",
                "--host", "0.0.0.0",
                "--port", str(port)
            ])
        except KeyboardInterrupt:
            print("\n✅ Server stopped")
    
    def start_flask(self, port=5000):
        """Start Flask server"""
        print(f"\n🚀 Starting Flask server on port {port}...")
        print(f"   Health: http://localhost:{port}/health")
        print(f"   Press Ctrl+C to stop")
        
        try:
            subprocess.run([
                sys.executable, "src/deployment/api_flask.py"
            ])
        except KeyboardInterrupt:
            print("\n✅ Server stopped")
    
    def test_api(self, port=8000):
        """Test API endpoints"""
        print(f"\n🧪 Testing API on port {port}...")
        
        import requests
        
        base_url = f"http://localhost:{port}"
        
        try:
            # Test health
            response = requests.get(f"{base_url}/health", timeout=5)
            if response.status_code == 200:
                print(f"✅ Health check: {response.json()}")
            else:
                print(f"❌ Health check failed: {response.status_code}")
                return False
            
            # Test prediction
            payload = {
                "data": [{
                    "temperature": 75.0,
                    "vibration": 3.5,
                    "pressure": 100.0,
                    "rpm": 1500.0,
                    "power_consumption": 250.0
                }],
                "return_probability": True
            }
            
            response = requests.post(f"{base_url}/predict", json=payload, timeout=5)
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Prediction: {result['predictions']}")
                if result.get('probabilities'):
                    print(f"   Probabilities: {result['probabilities'][0]}")
            else:
                print(f"⚠️ Prediction returned {response.status_code}")
            
            return True
            
        except requests.exceptions.ConnectionError:
            print(f"❌ Could not connect to API at {base_url}")
            print("   Make sure the server is running in another terminal")
            return False
        except Exception as e:
            print(f"❌ Test failed: {e}")
            return False
    
    def save_to_bentoml(self):
        """Save model to BentoML"""
        print("\n📦 Saving model to BentoML...")
        
        try:
            subprocess.run([
                sys.executable, "src/deployment/bentoml_save.py",
                "--model-path", "models/production_model.pkl"
            ], check=True)
            print("✅ Model saved to BentoML")
            return True
        except subprocess.CalledProcessError:
            print("❌ Failed to save to BentoML")
            return False
    
    def list_bentoml_models(self):
        """List BentoML models"""
        print("\n📋 BentoML Models:")
        try:
            result = subprocess.run([
                "bentoml", "models", "list"
            ], capture_output=True, text=True, check=True)
            print(result.stdout)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("⚠️ BentoML CLI not available or no models saved")
    
    def full_pipeline(self):
        """Run the complete pipeline"""
        print("=" * 60)
        print("🚀 Complete MLOps Pipeline")
        print("=" * 60)
        
        # Step 1: Check environment
        if not self.check_environment():
            print("\n❌ Environment check failed. Please install missing packages.")
            return
        
        # Step 2: Generate data
        if not self.generate_data():
            print("\n❌ Data generation failed")
            return
        
        # Step 3: Train models
        if not self.train_model():
            print("\n⚠️ Training completed with warnings")
        
        # Step 4: Save to BentoML
        self.save_to_bentoml()
        
        print("\n" + "=" * 60)
        print("✅ Pipeline Complete!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Start API: python deploy_simple.py api")
        print("2. Test API: python deploy_simple.py test")
        print("3. View docs: http://localhost:8000/docs")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Simple ML Deployment Manager")
    parser.add_argument("command", 
                       choices=['check', 'data', 'train', 'api', 'flask', 'test', 'bento', 'list', 'full'],
                       help="Command to execute")
    parser.add_argument("--port", type=int, default=8000, help="API port")
    
    args = parser.parse_args()
    
    manager = SimpleDeploymentManager()
    
    commands = {
        'check': manager.check_environment,
        'data': manager.generate_data,
        'train': manager.train_model,
        'api': lambda: manager.start_fastapi(args.port),
        'flask': lambda: manager.start_flask(),
        'test': lambda: manager.test_api(args.port),
        'bento': manager.save_to_bentoml,
        'list': manager.list_bentoml_models,
        'full': manager.full_pipeline
    }
    
    commands[args.command]()


if __name__ == "__main__":
    main()
