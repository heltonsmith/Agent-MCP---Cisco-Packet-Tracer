#!/usr/bin/env bash
# ==============================================================================
# Agent MCP - Cisco Packet Tracer - Linux/macOS Automated Setup
# Desarrollado por: Ing. Helton Smith Bustos Sáez
# Magíster en Full Stack | Experto en Ciberseguridad e Inteligencia Artificial
# ==============================================================================

echo "=============================================================================="
echo "Instalando dependencias de Agent MCP - Cisco Packet Tracer..."
echo "Desarrollado por: Ing. Helton Smith Bustos Sáez"
echo "=============================================================================="

python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

echo ""
echo "Generando configuración dinámica para este equipo..."
python3 setup_project.py

echo ""
echo "Proceso completado. Puedes abrir 'index.html' en tu navegador para ver la guía visual."

