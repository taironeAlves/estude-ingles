@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Criando ambiente virtual em .venv ...
    python -m venv .venv
    if errorlevel 1 (
        echo Falha ao criar o ambiente virtual. Verifique se o Python esta instalado e no PATH.
        exit /b 1
    )
) else (
    echo Ambiente virtual ja existe, pulando criacao.
)

echo Instalando dependencias...
".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -r requirements.txt

echo.
echo Setup concluido! Use start.bat para iniciar o servidor.
