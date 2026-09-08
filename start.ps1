Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "  Starting Q-SENTINEL v9 Stack" -ForegroundColor Cyan
Write-Host "  API: http://localhost:8000" -ForegroundColor Cyan
Write-Host "  Frontend: http://localhost:3000" -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan

Write-Host "[1/2] Launching FastAPI Backend (:8000)..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "python -m uvicorn apps.api.main:app --host 0.0.0.0 --port 8000"

Write-Host "[2/2] Launching Vite Frontend (:3000)..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; cmd.exe /c npm run dev"

Write-Host "`nBoth services are now starting. Visit http://localhost:3000" -ForegroundColor Yellow
