@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Ambiente virtual nao encontrado. Rode setup.bat primeiro.
    exit /b 1
)

echo Iniciando servidor em http://localhost:8010
echo (pressione CTRL+C para parar)

start /b "" powershell -NoProfile -Command "Start-Sleep -Seconds 2; Start-Process 'http://localhost:8010'"
".venv\Scripts\python.exe" -m uvicorn app.main:app --reload --port 8010
