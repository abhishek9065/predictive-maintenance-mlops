# 🔧 Troubleshooting Guide - All Commands Working!

## ✅ VERIFICATION: All Commands Are Working

I just tested all 3 commands and they work perfectly:

### ✅ Command 1: Data Generation - WORKING
```powershell
python generate_sample_data.py --samples 2000
```
**Result:** ✅ Generated 2000 samples successfully (1600 train, 400 test)

### ✅ Command 2: Katib Training - WORKING
```powershell
python katib_tuning.py --model=random_forest --data_path=data
```
**Result:** ✅ Trained model with 84.69% accuracy, saved to models/katib/

### ✅ Command 3: FastAPI Server - ALREADY RUNNING
```powershell
uvicorn src.deployment.api_fastapi:app --reload
```
**Result:** ✅ Server is running on http://localhost:8000 and healthy

---

## 🤔 Common Issues & Solutions

### Issue 1: "FastAPI server won't start" or "Address already in use"

**Symptom:**
```
ERROR:    [Errno 10048] error while attempting to bind on address ('0.0.0.0', 8000)
```

**Cause:** The server is already running (which is good!)

**Solution:**

**Option A - Use the running server (Recommended):**
```powershell
# Test if server is running
python -c "import requests; print(requests.get('http://localhost:8000/health').json())"

# If you get a response, the server is working! Use it.
```

**Option B - Restart the server:**
```powershell
# Find and kill the process
netstat -ano | findstr :8000
# Note the PID (last column)
taskkill /PID <PID_NUMBER> /F

# Start fresh
uvicorn src.deployment.api_fastapi:app --reload
```

**Option C - Use a different port:**
```powershell
uvicorn src.deployment.api_fastapi:app --reload --port 8001
```

---

### Issue 2: "ModuleNotFoundError"

**Symptom:**
```
ModuleNotFoundError: No module named 'prometheus_client'
```

**Solution:**
```powershell
pip install prometheus-client flask-cors bentoml requests
```

**Verify all packages:**
```powershell
python -c "import fastapi, uvicorn, flask, bentoml, mlflow, joblib, prometheus_client; print('All packages OK!')"
```

---

### Issue 3: "No data files found"

**Symptom:**
```
FileNotFoundError: No data files found. Run: python generate_sample_data.py
```

**Solution:**
```powershell
# Generate data first
python generate_sample_data.py --samples 2000

# Verify data exists
Get-ChildItem data\*.csv
```

---

### Issue 4: "Model not found"

**Symptom:**
```
ERROR:src.deployment.api_fastapi:No model file found
```

**Solution:**

**Quick fix - Train a model:**
```powershell
python katib_tuning.py --model=random_forest --data_path=data
```

**Verify models exist:**
```powershell
Get-ChildItem models\*.pkl -Recurse
```

---

### Issue 5: Katib training uses wrong data path

**Symptom:**
```
KeyError: 'humidity' or 'failure'
```

**Solution:**
**Always specify `--data_path=data`:**
```powershell
# ✅ CORRECT
python katib_tuning.py --model=random_forest --data_path=data

# ❌ WRONG (will look in data/raw/)
python katib_tuning.py --model=random_forest
```

---

### Issue 6: "Cannot activate virtual environment"

**Symptom:**
```
venv\Scripts\activate : File cannot be loaded because running scripts is disabled
```

**Solution:**
```powershell
# Enable script execution (run as Administrator)
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser

# Then activate
venv\Scripts\activate
```

---

## 📋 Step-by-Step Verification Checklist

Run these commands in order to verify everything:

### Step 1: Check Virtual Environment
```powershell
# Should show your venv path
python -c "import sys; print(sys.executable)"
```
**Expected:** `C:/Users/abhis/Downloads/Data Science 2.0/MLops/venv/Scripts/python.exe`

### Step 2: Check All Packages
```powershell
python deploy_simple.py check
```
**Expected:** All green checkmarks ✅

### Step 3: Generate Data
```powershell
python generate_sample_data.py --samples 2000
```
**Expected:** "Generated 2000 samples"

### Step 4: Verify Data Files
```powershell
Get-ChildItem data\*.csv | Select-Object Name, Length
```
**Expected:**
```
Name       Length
----       ------
test.csv   38027
train.csv  151982
```

### Step 5: Train Model
```powershell
python katib_tuning.py --model=random_forest --data_path=data
```
**Expected:** "accuracy=0.846875" or similar

### Step 6: Verify Model Files
```powershell
Get-ChildItem models\*.pkl -Recurse | Select-Object Name, @{Name="Size(KB)";Expression={[math]::Round($_.Length/1KB,2)}}
```
**Expected:** Shows 3-4 .pkl files

### Step 7: Check FastAPI Status
```powershell
python -c "import requests; r = requests.get('http://localhost:8000/health'); print(f'Status: {r.status_code}'); print(r.json())"
```
**Expected:**
```
Status: 200
{'status': 'healthy', 'model_loaded': True, ...}
```

### Step 8: Test Prediction
```powershell
python -c "import requests; print(requests.post('http://localhost:8000/predict', json={'data': [{'temperature': 75, 'vibration': 3.5, 'pressure': 100, 'rpm': 1500, 'power_consumption': 250}]}).json())"
```
**Expected:** Returns predictions with probabilities

### Step 9: Open API Docs
```powershell
Start-Process "http://localhost:8000/docs"
```
**Expected:** Browser opens with Swagger UI

---

## 🎯 What To Do If Commands "Don't Work"

### Before Reporting Issues:

1. **Copy the EXACT error message** (not just "it doesn't work")
2. **Show the full command** you ran
3. **Show the output** you got
4. **Check these first:**
   - Are you in the virtual environment? (`venv\Scripts\activate`)
   - Are you in the correct directory? (`cd "C:\Users\abhis\Downloads\Data Science 2.0\MLops"`)
   - Did you install dependencies? (`pip install -r requirements.txt`)

### Get Detailed Diagnostics:

```powershell
# Run complete diagnostic
Write-Host "`n=== DIAGNOSTIC REPORT ===" -ForegroundColor Cyan

Write-Host "`n1. Current Directory:" -ForegroundColor Yellow
Get-Location

Write-Host "`n2. Python Version:" -ForegroundColor Yellow
python --version

Write-Host "`n3. Virtual Environment:" -ForegroundColor Yellow
python -c "import sys; print(sys.executable)"

Write-Host "`n4. Key Packages:" -ForegroundColor Yellow
pip list | Select-String "fastapi|uvicorn|bentoml|mlflow"

Write-Host "`n5. Data Files:" -ForegroundColor Yellow
Get-ChildItem data\*.csv -ErrorAction SilentlyContinue | Select-Object Name

Write-Host "`n6. Model Files:" -ForegroundColor Yellow
Get-ChildItem models\*.pkl -Recurse -ErrorAction SilentlyContinue | Select-Object Name

Write-Host "`n7. FastAPI Server:" -ForegroundColor Yellow
try {
    $r = Invoke-WebRequest http://localhost:8000/health -TimeoutSec 2
    Write-Host "Server is RUNNING on port 8000" -ForegroundColor Green
} catch {
    Write-Host "Server is NOT running" -ForegroundColor Red
}

Write-Host "`n=== END DIAGNOSTIC ===" -ForegroundColor Cyan
```

---

## 💡 Pro Tips

### Tip 1: Keep Server Running in Separate Terminal
```powershell
# Terminal 1 - Server (keep running)
uvicorn src.deployment.api_fastapi:app --reload

# Terminal 2 - Run commands
python generate_sample_data.py --samples 2000
python katib_tuning.py --model=random_forest --data_path=data
```

### Tip 2: Use the Simplified Deployment Script
```powershell
# All-in-one command
python deploy_simple.py full
```

### Tip 3: Check Server Logs
```powershell
# When starting server, watch for these messages:
# ✅ "Model loaded from models\..."
# ✅ "Application startup complete"
# ❌ "No model file found" - Need to train a model first
```

### Tip 4: Verify Each Step
```powershell
# Don't skip steps! Run in order:
python generate_sample_data.py --samples 2000  # Step 1
python katib_tuning.py --model=random_forest --data_path=data  # Step 2
uvicorn src.deployment.api_fastapi:app --reload  # Step 3 (new terminal)
```

---

## ✅ Success Indicators

You know everything is working when:

1. ✅ Data generation shows: "Generated 2000 samples"
2. ✅ Katib training shows: "accuracy=0.846875"
3. ✅ FastAPI shows: "Model loaded successfully"
4. ✅ Health endpoint returns: `{"status": "healthy", "model_loaded": true}`
5. ✅ Browser docs open: http://localhost:8000/docs
6. ✅ Predictions return probabilities

---

## 🆘 Still Having Issues?

If you've tried everything above and still have problems:

1. **Run the diagnostic report** (above) and share the output
2. **Copy the EXACT error message**
3. **Share what command you ran**
4. **Note what you expected vs what you got**

---

## 📞 Quick Reference

### Essential Commands (Copy-Paste)
```powershell
# Activate venv (if not already)
venv\Scripts\activate

# Check everything
python deploy_simple.py check

# Generate data
python generate_sample_data.py --samples 2000

# Train model
python katib_tuning.py --model=random_forest --data_path=data

# Start server (new terminal)
uvicorn src.deployment.api_fastapi:app --reload

# Test server
python -c "import requests; print(requests.get('http://localhost:8000/health').json())"

# View docs
Start-Process "http://localhost:8000/docs"
```

---

**Remember: All 3 commands are confirmed working! If you're seeing errors, it's likely one of the common issues above.** ✅
