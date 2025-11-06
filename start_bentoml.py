"""
Simple BentoML Server Starter
Starts the BentoML service with proper error handling
"""

import subprocess
import sys
import time
import requests
from pathlib import Path

def check_model_exists():
    """Check if model is saved in BentoML"""
    try:
        result = subprocess.run(
            ["bentoml", "models", "list"],
            capture_output=True,
            text=True,
            check=False
        )
        return "predictive_maintenance_model" in result.stdout
    except Exception as e:
        print(f"⚠️  Error checking models: {e}")
        return False

def save_model():
    """Save model to BentoML if not exists"""
    print("\n📦 Saving model to BentoML...")
    try:
        result = subprocess.run(
            [sys.executable, "save_to_bentoml.py"],
            check=True
        )
        print("✅ Model saved successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to save model: {e}")
        return False

def start_bentoml_server(port=3000):
    """Start BentoML server"""
    print(f"\n🚀 Starting BentoML server on port {port}...")
    print("="*80)
    
    try:
        # Start the server
        process = subprocess.Popen(
            ["bentoml", "serve", "service:PredictiveMaintenanceService", "--port", str(port)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        # Wait a bit for server to start
        print("\n⏳ Waiting for server to start...")
        time.sleep(5)
        
        # Check if server is running
        max_attempts = 10
        for i in range(max_attempts):
            try:
                response = requests.get(f"http://localhost:{port}/health", timeout=2)
                if response.status_code == 200:
                    print(f"\n✅ BentoML server is running!")
                    print(f"   🌐 URL: http://localhost:{port}")
                    print(f"   📖 API Docs: http://localhost:{port}/docs")
                    print(f"   🏥 Health: http://localhost:{port}/health")
                    print("\n" + "="*80)
                    print("  Server is ready to accept requests!")
                    print("  Press Ctrl+C to stop")
                    print("="*80 + "\n")
                    
                    # Keep server running
                    try:
                        process.wait()
                    except KeyboardInterrupt:
                        print("\n\n👋 Stopping server...")
                        process.terminate()
                        process.wait(timeout=5)
                        print("✅ Server stopped")
                    
                    return True
            except requests.exceptions.RequestException:
                print(f"   Attempt {i+1}/{max_attempts}...")
                time.sleep(2)
        
        print("\n❌ Server failed to start properly")
        process.terminate()
        return False
        
    except FileNotFoundError:
        print("\n❌ BentoML not found!")
        print("   Please activate the virtual environment:")
        print("   .\\venv\\Scripts\\Activate.ps1")
        return False
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        return False

def main():
    """Main function"""
    print("\n" + "="*80)
    print("  🚀 BENTOML SERVER STARTER")
    print("="*80)
    
    # Check if model exists
    print("\n📋 Checking model status...")
    if not check_model_exists():
        print("   Model not found in BentoML store")
        if not save_model():
            print("\n❌ Failed to save model. Please run: python save_to_bentoml.py")
            return
    else:
        print("   ✅ Model found in BentoML store")
    
    # Start server
    if not start_bentoml_server(port=3000):
        print("\n❌ Failed to start BentoML server")
        print("\n📚 Manual start:")
        print("   bentoml serve service:PredictiveMaintenanceService --port 3000")

if __name__ == "__main__":
    main()
