@echo off
title Q-SENTINEL v9 Launcher
echo ===================================================
echo   Starting Q-SENTINEL v9 Stack
echo   API: http://localhost:8000
echo   Frontend: http://localhost:3000
echo ===================================================

echo [1/2] Launching FastAPI Backend (:8000)...
start "Q-SENTINEL API" cmd /k "python -m uvicorn apps.api.main:app --host 0.0.0.0 --port 8000"

echo [2/2] Launching Vite Frontend (:3000)...
cd frontend
start "Q-SENTINEL Frontend" cmd /k "npm run dev"
cd ..

echo.
echo Both services launched in dedicated terminal windows.
echo Open http://localhost:3000 in your browser.
