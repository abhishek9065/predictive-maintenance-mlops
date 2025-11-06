# PowerShell Script to Test FastAPI Endpoints on Windows
# Run this in PowerShell while the uvicorn server is running

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  TESTING FASTAPI SERVER" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if server is running
Write-Host "1. Checking if server is running on port 8000..." -ForegroundColor Yellow
$portCheck = netstat -ano | findstr :8000 | Select-String "LISTENING"
if ($portCheck) {
    Write-Host "✅ Server is running!" -ForegroundColor Green
} else {
    Write-Host "❌ Server not running. Start with: uvicorn src.deployment.api_fastapi:app --reload" -ForegroundColor Red
    exit
}
Write-Host ""

# Test 1: Health Endpoint
Write-Host "2. Testing /health endpoint..." -ForegroundColor Yellow
try {
    $health = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing
    Write-Host "✅ Status: $($health.StatusCode)" -ForegroundColor Green
    Write-Host "Response:" -ForegroundColor Cyan
    $health.Content | ConvertFrom-Json | ConvertTo-Json -Depth 10
} catch {
    Write-Host "❌ Error: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 2: Root Endpoint
Write-Host "3. Testing / (root) endpoint..." -ForegroundColor Yellow
try {
    $root = Invoke-WebRequest -Uri "http://localhost:8000/" -UseBasicParsing
    Write-Host "✅ Status: $($root.StatusCode)" -ForegroundColor Green
    Write-Host "Response:" -ForegroundColor Cyan
    $root.Content | ConvertFrom-Json | ConvertTo-Json
} catch {
    Write-Host "❌ Error: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 3: Model Info
Write-Host "4. Testing /model/info endpoint..." -ForegroundColor Yellow
try {
    $modelInfo = Invoke-WebRequest -Uri "http://localhost:8000/model/info" -UseBasicParsing
    Write-Host "✅ Status: $($modelInfo.StatusCode)" -ForegroundColor Green
    Write-Host "Response:" -ForegroundColor Cyan
    $modelInfo.Content | ConvertFrom-Json | ConvertTo-Json -Depth 10
} catch {
    Write-Host "❌ Error: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 4: Prediction
Write-Host "5. Testing /predict endpoint..." -ForegroundColor Yellow
try {
    $predictionData = @{
        temperature = 75.5
        vibration = 0.8
        pressure = 100.2
        humidity = 45.3
        rpm = 1500.0
    } | ConvertTo-Json

    $prediction = Invoke-WebRequest -Uri "http://localhost:8000/predict" `
        -Method POST `
        -ContentType "application/json" `
        -Body $predictionData `
        -UseBasicParsing
    
    Write-Host "✅ Status: $($prediction.StatusCode)" -ForegroundColor Green
    Write-Host "Response:" -ForegroundColor Cyan
    $prediction.Content | ConvertFrom-Json | ConvertTo-Json -Depth 10
} catch {
    Write-Host "❌ Error: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 5: Prometheus Metrics
Write-Host "6. Testing /metrics endpoint..." -ForegroundColor Yellow
try {
    $metrics = Invoke-WebRequest -Uri "http://localhost:8000/metrics" -UseBasicParsing
    Write-Host "✅ Status: $($metrics.StatusCode)" -ForegroundColor Green
    $metricsLines = ($metrics.Content -split "`n" | Where-Object { $_ -notmatch '^#' -and $_.Trim() -ne '' })
    Write-Host "Prometheus metrics count: $($metricsLines.Count)" -ForegroundColor Cyan
    Write-Host "Sample metrics:" -ForegroundColor Cyan
    $metricsLines | Select-Object -First 5 | ForEach-Object { Write-Host "  $_" }
} catch {
    Write-Host "❌ Error: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  TESTING COMPLETE!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "💡 Tip: You can also open in browser:" -ForegroundColor Yellow
Write-Host "   http://localhost:8000/docs (Interactive API docs)" -ForegroundColor Cyan
Write-Host "   http://localhost:8000/redoc (ReDoc documentation)" -ForegroundColor Cyan
