# ✅ FIXED: Windows API Testing Guide

## The Error You Had

When running `curl http://localhost:8000/health` in Windows PowerShell, it hangs or doesn't work properly because PowerShell's `curl` is an alias for `Invoke-WebRequest` which works differently than Linux curl.

---

## ✅ SOLUTION: 3 Easy Ways to Test the API on Windows

### **Option 1: Use Python Script** (Recommended ✨)

```bash
python test_api_simple.py
```

This automatically tests all endpoints and shows results!

---

### **Option 2: Use PowerShell Commands**

```powershell
# Health Check
(Invoke-WebRequest -Uri http://localhost:8000/health -UseBasicParsing).Content

# Model Info
(Invoke-WebRequest -Uri http://localhost:8000/model/info -UseBasicParsing).Content

# Make Prediction
$body = @{
    data = @(
        @{
            temperature = 75.5
            vibration = 0.8
            pressure = 100.2
            current = 12.5
            rpm = 1500.0
        }
    )
    return_probability = $true
} | ConvertTo-Json -Depth 10

Invoke-WebRequest -Uri http://localhost:8000/predict `
    -Method POST `
    -ContentType "application/json" `
    -Body $body `
    -UseBasicParsing | Select-Object -ExpandProperty Content
```

Or run the PowerShell script:
```powershell
.\test_api_windows.ps1
```

---

### **Option 3: Use Browser** (Easiest! 🌐)

Just open these URLs in your browser:

1. **Interactive API Docs**: http://localhost:8000/docs
   - Try all endpoints with a nice UI
   - See request/response examples
   - Make test requests

2. **Alternative Docs**: http://localhost:8000/redoc
   - Clean, readable documentation

3. **Health Check**: http://localhost:8000/health
   - Quick status check

---

## 📊 Current Status

✅ **FastAPI Server**: Running on port 8000  
✅ **Model Loaded**: RandomForestClassifier (100 estimators)  
✅ **All Endpoints**: Working correctly  

---

## 🔧 Fixed Issues

### Issue 1: Field Mismatch ✅ FIXED
**Problem**: API schema had `power_consumption` but model expects `current`  
**Fix**: Updated `SensorData` class in `api_fastapi.py` to use `current`

### Issue 2: Windows curl Not Working ✅ FIXED  
**Problem**: PowerShell's `curl` is different from Linux curl  
**Fix**: Created `test_api_simple.py` and `test_api_windows.ps1`

---

## 🎯 Correct API Request Format

### Prediction Endpoint

**URL**: `POST http://localhost:8000/predict`

**Request Body**:
```json
{
  "data": [
    {
      "temperature": 75.5,
      "vibration": 0.8,
      "pressure": 100.2,
      "current": 12.5,
      "rpm": 1500.0
    }
  ],
  "return_probability": true
}
```

**Response**:
```json
{
  "predictions": [0],
  "probabilities": [[0.95, 0.05]],
  "timestamp": "2025-11-06T15:58:25.527668",
  "model_version": "1.0.0",
  "count": 1
}
```

---

## 🚀 Quick Test Commands

```bash
# Test everything at once
python test_api_simple.py

# Or test individual endpoints
python -c "import requests; print(requests.get('http://localhost:8000/health').json())"

# Or use the browser
start http://localhost:8000/docs
```

---

## ⚠️ If Server Not Running

Start it with:
```bash
uvicorn src.deployment.api_fastapi:app --reload
```

Check if it's running:
```bash
netstat -ano | findstr :8000
```

---

## ✅ Everything Is Now Working!

- ✅ API server running
- ✅ Model loaded successfully  
- ✅ All endpoints accessible
- ✅ Windows-compatible test scripts created
- ✅ Field mismatch fixed
- ✅ Interactive docs available

**No more errors!** 🎉

---

**Last Updated**: 2025-11-06  
**Status**: ✅ ALL FIXED
