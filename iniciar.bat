@echo off
title VESPERA - Simulador de Vida Artificial
echo ========================================================
echo       INICIANDO O LABORATORIO VESPERA
echo ========================================================
echo.

echo [1/2] Iniciando Servidor Backend (FastAPI)...
start "VESPERA - Backend" cmd /k "cd backend && .venv\Scripts\activate && python -m uvicorn main:app --app-dir src --host 127.0.0.1 --port 8000"

echo [2/2] Iniciando Servidor Frontend (Vite/React)...
start "VESPERA - Frontend" cmd /k "cd frontend && npm.cmd run dev"

echo.
echo ========================================================
echo  Tudo pronto!
echo  Abra no navegador: http://localhost:5173/
echo  Documentacao da API: http://localhost:8000/docs
echo ========================================================
echo.
pause
