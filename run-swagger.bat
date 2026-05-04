@echo off
title Habitly API
echo.
echo ========================================
echo   Habitly API - Swagger
echo ========================================
echo.
echo Abriendo en tu navegador...
start "" "http://localhost:8000/docs"
echo.
echo Ve a: http://localhost:8000/docs
echo.
echo Presiona Ctrl+C para detener
echo.
python -m uvicorn main:app --reload --port 8000