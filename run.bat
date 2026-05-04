@echo off
cd /d "%~dp0"
echo ========================================
echo   Habitly API
echo ========================================
echo.
echo Abriendo Swagger UI...
start http://127.0.0.1:8001/docs
echo.
echo Nota: El proyecto no esta en Supabase
echo       Debe ejecutar supabase-schema.sql
echo       en el SQL Editor de Supabase
echo.
python -m uvicorn main:app --host 127.0.0.1 --port 8001