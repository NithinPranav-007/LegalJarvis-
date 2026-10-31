@echo off
title Needhi Launcher
echo ======================================================================
echo                  Starting Needhi (LegalJarvis) Project
echo ======================================================================
echo.

echo [1/2] Starting FastAPI Backend Daemon on http://localhost:8000 ...
start "Needhi Backend (Port 8000)" cmd /k "cd /d "%~dp0" && uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000"

timeout /t 3 /nobreak >nul

echo [2/2] Starting React + Vite Frontend UI on http://localhost:5173 ...
start "Needhi Frontend (Port 5173)" cmd /k "cd /d "%~dp0frontend" && npm run dev -- --host 127.0.0.1 --port 5173"

echo.
echo ======================================================================
echo    Needhi is now fully running!
echo.
echo    Frontend Application:   http://localhost:5173
echo    Backend Swagger Docs:   http://localhost:8000/docs
echo    Health Check:           http://localhost:8000/health
echo ======================================================================
echo.
echo Press any key to open the application in your default browser...
pause >nul
start http://localhost:5173
