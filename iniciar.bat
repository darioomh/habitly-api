@echo off
cd /d "%~dp0"
echo ========================================
echo   Habitly API - Ejecutando
echo ========================================
echo.
echo Abriendo Swagger UI en tu navegador...
start http://localhost:8001/docs
echo.
echo Si no se abre, ve a: http://localhost:8001/docs
echo.
python -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload
pause