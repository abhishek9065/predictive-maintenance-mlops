
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
