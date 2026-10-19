Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "       INICIANDO O LABORATÓRIO VÉSPERA" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan

Write-Host "`n[1/2] Iniciando Servidor Backend (FastAPI)..." -ForegroundColor Yellow
Start-Process -FilePath "powershell" -ArgumentList "-NoExit", "-Command", "cd backend; .\.venv\Scripts\Activate.ps1; python -m uvicorn main:app --app-dir src --host 127.0.0.1 --port 8000"

Write-Host "[2/2] Iniciando Servidor Frontend (Vite/React)..." -ForegroundColor Yellow
Start-Process -FilePath "powershell" -ArgumentList "-NoExit", "-Command", "cd frontend; npm.cmd run dev"

Start-Sleep -Seconds 2
Write-Host "`nAbrindo navegador em http://localhost:5173/ ..." -ForegroundColor Green
Start-Process "http://localhost:5173/"

Write-Host "`nServiços em execução!" -ForegroundColor Green
