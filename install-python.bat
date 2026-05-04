@echo off
echo ========================================
echo   Instalando Python
echo ========================================
echo.
echo Opcion 1: Microsoft Store
start ms-search:python

echo.
echo Opcion 2: Descargar manualmente
echo   https://www.python.org/downloads/
echo.
echo Opcion 3: Usar winget (si esta instalado)
winget install Python.Python.3.11 --accept-package-agreements --accept-source-agreements
pause