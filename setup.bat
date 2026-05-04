@echo off
cd /d "%~dp0"
echo ========================================
echo   Habitly API - Setup
echo ========================================

python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python no esta instalado
    pause
    exit /b 1
)

echo [1/3] Creando entorno virtual...
if not exist venv (
    python -m venv venv
) else (
    echo   Ya existe, saltando...
)

echo [2/3] Instalando dependencias...
call venv\Scripts\pip.exe install fastapi uvicorn python-dotenv 2>nul

echo.
echo ========================================
echo   Listo! Ejecuta run.bat
echo ========================================
pause