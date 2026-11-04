@echo off
REM ==============================================================================
REM Agent MCP - Cisco Packet Tracer - Windows Automated Setup
REM Desarrollado por: Ing. Helton Smith Bustos Sáez
REM Magíster en Full Stack | Experto en Ciberseguridad e Inteligencia Artificial
REM ==============================================================================

echo ==============================================================================
echo Instalando dependencias de Agent MCP - Cisco Packet Tracer...
echo Desarrollado por: Ing. Helton Smith Bustos Saez
echo ==============================================================================

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo.
echo Generando configuracion dinamica para este equipo...
python setup_project.py

echo.
echo Proceso completado. Puedes abrir 'index.html' en tu navegador para ver la guia visual.
pause

