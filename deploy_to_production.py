"""
Production Deployment Script
Deploy the MLOps Predictive Maintenance system to production
"""

import os
import sys
import subprocess
import time
from pathlib import Path
import json

class ProductionDeployer:
    """Handle production deployment"""
    
    def __init__(self):
        self.deployment_status = {
            'model_ready': False,
            'api_running': False,
            'docker_ready': False,
            'health_check': False
        }
    
    def print_header(self, text):
        """Print formatted header"""
        print("\n" + "="*80)
        print(f"  {text}")
        print("="*80 + "\n")
    
    def check_prerequisites(self):
        """Check if all prerequisites are met"""
        self.print_header("1. CHECKING PREREQUISITES")
        
        # Check if model exists
        model_path = Path("models/best_model.pkl")
        if model_path.exists():
            print("✅ Production model found: models/best_model.pkl")
            self.deployment_status['model_ready'] = True
        else:
            print("❌ Production model not found!")
            print("   Run: python update_api_model.py")
            return False
        
        # Check if data exists
        if Path("data/full_dataset.csv").exists():
            print("✅ Training data available")
        else:
            print("⚠️  No training data found")
        
        # Check if Docker is available
        try:
            result = subprocess.run(
                ["docker", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                print(f"✅ Docker installed: {result.stdout.strip()}")
                self.deployment_status['docker_ready'] = True
            else:
                print("⚠️  Docker not found (optional for local deployment)")
        except Exception:
            print("⚠️  Docker not found (optional for local deployment)")
        
        return True
    
    def start_production_api(self):
        """Start the production API server"""
        self.print_header("2. STARTING PRODUCTION API SERVER")
        
        print("🚀 Starting FastAPI server on port 8000...")
        print("   URL: http://localhost:8000")
        print("   Docs: http://localhost:8000/docs")
        print("   Health: http://localhost:8000/health")
        
        # Kill any existing process on port 8000
        try:
            subprocess.run(
                'powershell -Command "$proc = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -First 1; if($proc) { Stop-Process -Id $proc -Force }"',
                shell=True,
                timeout=5
            )
            time.sleep(2)
        except Exception:
            pass
        
        # Start the server in background
        print("\n📋 Server will start in a new terminal window...")
        print("   To stop: Close the terminal or press Ctrl+C")
        
        # Create a startup script
        startup_script = """
@echo off
echo ============================================================
echo   PRODUCTION API SERVER - PREDICTIVE MAINTENANCE
echo ============================================================
echo.
echo Starting FastAPI server on http://localhost:8000
echo.
echo API Documentation: http://localhost:8000/docs
echo Health Check: http://localhost:8000/health
echo.
echo Press Ctrl+C to stop the server
echo ============================================================
echo.

cd /d "%~dp0"
uvicorn src.deployment.api_fastapi:app --host 0.0.0.0 --port 8000 --reload

pause
"""
        
        with open("start_production_server.bat", 'w') as f:
            f.write(startup_script)
        
        # Start server in new window
        subprocess.Popen(["start", "cmd", "/k", "start_production_server.bat"], shell=True)
        
        print("\n✅ Server startup initiated!")
        print("   Waiting 10 seconds for server to be ready...")
        time.sleep(10)
        
        return True
    
    def verify_api_health(self):
        """Verify API is running and healthy"""
        self.print_header("3. VERIFYING API HEALTH")
        
        import requests
        
        try:
            # Test health endpoint
            response = requests.get("http://localhost:8000/health", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                print("✅ API Health Check: PASSED")
                print(f"   Status: {data.get('status', 'unknown')}")
                print(f"   Model Loaded: {data.get('model_loaded', False)}")
                self.deployment_status['health_check'] = True
                self.deployment_status['api_running'] = True
                return True
            else:
                print(f"❌ Health check failed: HTTP {response.status_code}")
                return False
                
        except requests.exceptions.ConnectionError:
            print("❌ Cannot connect to API server")
            print("   Server may still be starting up...")
            return False
        except Exception as e:
            print(f"❌ Health check error: {str(e)}")
            return False
    
    def test_prediction_endpoint(self):
        """Test the prediction endpoint with real data"""
        self.print_header("4. TESTING PREDICTION ENDPOINT")
        
        import requests
        import pandas as pd
        
        # Load test data
        if Path("data/test.csv").exists():
            df = pd.read_csv("data/test.csv")
            sample = df.iloc[0]
            
            test_data = {
                "temperature": float(sample['temperature']),
                "vibration": float(sample['vibration']),
                "pressure": float(sample['pressure']),
                "rpm": float(sample['rpm']),
                "current": float(sample['current'])
            }
            
            print("📊 Test Data:")
            print(f"   Temperature: {test_data['temperature']:.2f}°C")
            print(f"   Vibration: {test_data['vibration']:.3f}")
            print(f"   Pressure: {test_data['pressure']:.2f} PSI")
            print(f"   RPM: {test_data['rpm']:.0f}")
            print(f"   Current: {test_data['current']:.2f}A")
            print(f"   Actual Failure: {'YES' if sample['failure'] == 1 else 'NO'}")
            
            try:
                response = requests.post(
                    "http://localhost:8000/predict",
                    json=test_data,
                    timeout=5
                )
                
                if response.status_code == 200:
                    result = response.json()
                    prediction = result.get('prediction', 'unknown')
                    probability = result.get('probability', 0.0)
                    
                    print(f"\n✅ Prediction Result:")
                    print(f"   Prediction: {prediction}")
                    print(f"   Probability: {probability:.4f}")
                    print(f"   Match: {'✅ CORRECT' if (prediction == 'FAILURE' and sample['failure'] == 1) or (prediction == 'NORMAL' and sample['failure'] == 0) else '❌ INCORRECT'}")
                    
                    return True
                else:
                    print(f"❌ Prediction failed: HTTP {response.status_code}")
                    return False
                    
            except Exception as e:
                print(f"❌ Prediction error: {str(e)}")
                return False
        else:
            print("⚠️  No test data available")
            return True
    
    def generate_deployment_docs(self):
        """Generate deployment documentation"""
        self.print_header("5. GENERATING DEPLOYMENT DOCUMENTATION")
        
        docs = f"""
# PRODUCTION DEPLOYMENT GUIDE

**Deployment Date:** {time.strftime('%Y-%m-%d %H:%M:%S')}
**Status:** {'✅ SUCCESSFUL' if all(self.deployment_status.values()) else '⚠️ PARTIAL'}

## Deployment Status

- Model Ready: {'✅' if self.deployment_status['model_ready'] else '❌'}
- API Running: {'✅' if self.deployment_status['api_running'] else '❌'}
- Docker Ready: {'✅' if self.deployment_status['docker_ready'] else '❌'}
- Health Check: {'✅' if self.deployment_status['health_check'] else '❌'}

## Production Endpoints

### Base URL
- **Local:** http://localhost:8000
- **Production:** Update with your production URL

### Available Endpoints

1. **Health Check**
   ```
   GET http://localhost:8000/health
   ```

2. **API Root**
   ```
   GET http://localhost:8000/
   ```

3. **Model Info**
   ```
   GET http://localhost:8000/model/info
   ```

4. **Predict (Single)**
   ```
   POST http://localhost:8000/predict
   
   Body:
   {{
     "temperature": 75.0,
     "vibration": 0.5,
     "pressure": 95.0,
     "rpm": 1450.0,
     "current": 9.0
   }}
   ```

5. **Prometheus Metrics**
   ```
   GET http://localhost:8000/metrics
   ```

6. **API Documentation**
   ```
   GET http://localhost:8000/docs
   ```

## Usage Examples

### Python
```python
import requests

# Make prediction
data = {{
    "temperature": 75.0,
    "vibration": 0.5,
    "pressure": 95.0,
    "rpm": 1450.0,
    "current": 9.0
}}

response = requests.post("http://localhost:8000/predict", json=data)
result = response.json()

print(f"Prediction: {{result['prediction']}}")
print(f"Probability: {{result['probability']:.4f}}")
```

### cURL (PowerShell)
```powershell
$body = @{{
    temperature = 75.0
    vibration = 0.5
    pressure = 95.0
    rpm = 1450.0
    current = 9.0
}} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/predict" -Method Post -Body $body -ContentType "application/json"
```

### JavaScript
```javascript
const response = await fetch('http://localhost:8000/predict', {{
  method: 'POST',
  headers: {{ 'Content-Type': 'application/json' }},
  body: JSON.stringify({{
    temperature: 75.0,
    vibration: 0.5,
    pressure: 95.0,
    rpm: 1450.0,
    current: 9.0
  }})
}});

const result = await response.json();
console.log(`Prediction: ${{result.prediction}}`);
```

## Docker Deployment

### Build Image
```bash
docker build -t predictive-maintenance:v2.0 .
```

### Run Container
```bash
docker run -d -p 8000:8000 --name pm-api predictive-maintenance:v2.0
```

### Docker Compose
```bash
docker-compose up -d
```

## Monitoring

### Health Checks
```bash
# Check if API is responding
curl http://localhost:8000/health

# Check model status
curl http://localhost:8000/model/info

# View metrics
curl http://localhost:8000/metrics
```

### Logs
Monitor the server terminal for request logs and errors.

## Troubleshooting

### API Not Responding
1. Check if server is running: `netstat -ano | findstr :8000`
2. Check logs in server terminal
3. Restart server: Run `start_production_server.bat`

### Model Not Loaded
1. Verify model exists: `models/best_model.pkl`
2. Check model metrics: `models/best_model_metrics.json`
3. Update model: `python update_api_model.py`

### Poor Performance
1. Check API response time in logs
2. Consider scaling with multiple workers
3. Enable caching if needed

## Production Checklist

- [ ] Model accuracy validated (>90%)
- [ ] API endpoints tested
- [ ] Health checks passing
- [ ] Error handling verified
- [ ] Monitoring configured
- [ ] Backup strategy in place
- [ ] Security reviewed
- [ ] Load testing completed
- [ ] Documentation updated

## Support

For issues or questions:
- Check logs in server terminal
- Review PROJECT_STATUS_REPORT.md
- Consult WINDOWS_API_TESTING_GUIDE.md

---
Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        with open("PRODUCTION_DEPLOYMENT.md", 'w') as f:
            f.write(docs)
        
        print("✅ Deployment documentation created: PRODUCTION_DEPLOYMENT.md")
        return True
    
    def create_monitoring_dashboard(self):
        """Create a simple monitoring dashboard script"""
        self.print_header("6. SETTING UP MONITORING")
        
        monitoring_script = '''"""
Production Monitoring Dashboard
Monitor API health, predictions, and performance
"""

import requests
import time
from datetime import datetime
import os

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def get_api_status():
    """Get API status"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=2)
        if response.status_code == 200:
            return "🟢 ONLINE", response.json()
        else:
            return "🟡 DEGRADED", {}
    except:
        return "🔴 OFFLINE", {}

def get_model_info():
    """Get model information"""
    try:
        response = requests.get("http://localhost:8000/model/info", timeout=2)
        if response.status_code == 200:
            return response.json()
        return {}
    except:
        return {}

def test_prediction():
    """Test a sample prediction"""
    test_data = {
        "temperature": 75.0,
        "vibration": 0.5,
        "pressure": 95.0,
        "rpm": 1450.0,
        "current": 9.0
    }
    
    try:
        start = time.time()
        response = requests.post("http://localhost:8000/predict", json=test_data, timeout=5)
        elapsed = (time.time() - start) * 1000
        
        if response.status_code == 200:
            result = response.json()
            return {
                'status': 'success',
                'prediction': result.get('prediction', 'unknown'),
                'probability': result.get('probability', 0.0),
                'response_time': elapsed
            }
        else:
            return {'status': 'error', 'response_time': elapsed}
    except Exception as e:
        return {'status': 'error', 'error': str(e)}

def main():
    """Main monitoring loop"""
    print("Starting Production Monitoring Dashboard...")
    print("Press Ctrl+C to exit\\n")
    time.sleep(2)
    
    try:
        while True:
            clear_screen()
            
            # Header
            print("="*80)
            print("  PRODUCTION MONITORING DASHBOARD - PREDICTIVE MAINTENANCE API")
            print("="*80)
            print(f"\\nLast Update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # API Status
            print("\\n" + "-"*80)
            print("API STATUS")
            print("-"*80)
            status, health = get_api_status()
            print(f"Status: {status}")
            if health:
                print(f"Model Loaded: {'✅' if health.get('model_loaded') else '❌'}")
            
            # Model Info
            print("\\n" + "-"*80)
            print("MODEL INFORMATION")
            print("-"*80)
            model_info = get_model_info()
            if model_info:
                info = model_info.get('info', {})
                print(f"Model Type: {info.get('model_type', 'Unknown')}")
                print(f"Training Samples: {info.get('training_samples', 'Unknown')}")
                print(f"Trained At: {info.get('trained_at', 'Unknown')}")
            else:
                print("⚠️ Model info not available")
            
            # Test Prediction
            print("\\n" + "-"*80)
            print("PREDICTION TEST")
            print("-"*80)
            test_result = test_prediction()
            if test_result['status'] == 'success':
                print(f"✅ Prediction: {test_result['prediction']}")
                print(f"   Probability: {test_result['probability']:.4f}")
                print(f"   Response Time: {test_result['response_time']:.2f}ms")
            else:
                print(f"❌ Prediction failed: {test_result.get('error', 'Unknown error')}")
            
            # Footer
            print("\\n" + "="*80)
            print("Auto-refresh in 5 seconds... (Ctrl+C to exit)")
            print("="*80)
            
            time.sleep(5)
            
    except KeyboardInterrupt:
        print("\\n\\nMonitoring stopped.")

if __name__ == "__main__":
    main()
'''
        
        with open("production_monitoring.py", 'w') as f:
            f.write(monitoring_script)
        
        print("✅ Monitoring dashboard created: production_monitoring.py")
        print("   Run: python production_monitoring.py")
        return True
    
    def print_deployment_summary(self):
        """Print deployment summary"""
        self.print_header("PRODUCTION DEPLOYMENT SUMMARY")
        
        all_ready = all(self.deployment_status.values())
        
        print(f"Overall Status: {'✅ READY FOR PRODUCTION' if all_ready else '⚠️ PARTIAL DEPLOYMENT'}")
        print(f"\\nComponent Status:")
        print(f"  - Model Ready: {'✅' if self.deployment_status['model_ready'] else '❌'}")
        print(f"  - API Running: {'✅' if self.deployment_status['api_running'] else '❌'}")
        print(f"  - Docker Ready: {'✅' if self.deployment_status['docker_ready'] else '⚠️ (Optional)'}")
        print(f"  - Health Check: {'✅' if self.deployment_status['health_check'] else '❌'}")
        
        print("\\n" + "="*80)
        print("  PRODUCTION API ENDPOINTS")
        print("="*80)
        print("\\n📍 Base URL: http://localhost:8000")
        print("\\n🔍 Key Endpoints:")
        print("   - Health Check:    GET  http://localhost:8000/health")
        print("   - Prediction:      POST http://localhost:8000/predict")
        print("   - Model Info:      GET  http://localhost:8000/model/info")
        print("   - API Docs:        GET  http://localhost:8000/docs")
        print("   - Metrics:         GET  http://localhost:8000/metrics")
        
        print("\\n" + "="*80)
        print("  NEXT STEPS")
        print("="*80)
        print("\\n1. 📊 Monitor API:")
        print("   python production_monitoring.py")
        print("\\n2. 🧪 Test endpoints:")
        print("   python test_api_simple.py")
        print("\\n3. 📖 View documentation:")
        print("   Open: PRODUCTION_DEPLOYMENT.md")
        print("\\n4. 🌐 Access API docs:")
        print("   Browser: http://localhost:8000/docs")
        print("\\n5. 🐳 Deploy with Docker (optional):")
        print("   docker build -t predictive-maintenance:v2.0 .")
        print("   docker run -p 8000:8000 predictive-maintenance:v2.0")
        
        print("\\n" + "="*80)
        print("  🎉 PRODUCTION DEPLOYMENT COMPLETE!")
        print("="*80 + "\\n")
    
    def deploy(self):
        """Run full deployment"""
        self.print_header("PRODUCTION DEPLOYMENT - PREDICTIVE MAINTENANCE")
        
        print("Starting production deployment process...")
        print("This will:")
        print("  1. Check prerequisites")
        print("  2. Start production API server")
        print("  3. Verify API health")
        print("  4. Test prediction endpoint")
        print("  5. Generate deployment docs")
        print("  6. Set up monitoring")
        print("\\nPress Enter to continue...")
        input()
        
        # Run deployment steps
        if not self.check_prerequisites():
            print("\\n❌ Prerequisites not met. Deployment aborted.")
            return False
        
        self.start_production_api()
        self.verify_api_health()
        self.test_prediction_endpoint()
        self.generate_deployment_docs()
        self.create_monitoring_dashboard()
        
        # Print summary
        self.print_deployment_summary()
        
        return True

def main():
    """Main entry point"""
    deployer = ProductionDeployer()
    deployer.deploy()

if __name__ == "__main__":
    main()
