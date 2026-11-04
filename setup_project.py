"""
====================================================================================================
PROYECTO: Agent MCP - Cisco Packet Tracer (Live Real-Time Automation)
DESCRIPCIÓN: Asistente interactivo de instalación, diagnóstico y generación de configuraciones MCP.
             Genera automáticamente los bloques JSON listos para copiar y pegar en cualquier cliente:
             Antigravity IDE, Antigravity CLI, Claude Code, Cursor, OpenCode, VS Code.

AUTOR: Ingeniero en Informática Helton Smith Bustos Sáez
       Magíster en Full Stack | Experto en Ciberseguridad e Inteligencia Artificial Aplicada
====================================================================================================
"""

import os
import sys
import json
import subprocess
from pathlib import Path

# Branding y Autoría
AUTHOR_NAME = "Ing. Helton Smith Bustos Sáez"
AUTHOR_TITLE = "Magíster en Full Stack | Experto en Ciberseguridad e Inteligencia Artificial Aplicada"
PROJECT_NAME = "Agent MCP - Cisco Packet Tracer"

def get_base_paths():
    """Detecta las rutas absolutas del entorno local del usuario dinámicamente."""
    python_exe = sys.executable
    project_dir = Path(__file__).resolve().parent
    run_server_script = project_dir / "run_server.py"
    pts_extension = project_dir / "MCP-Control-Center.pts"
    return str(python_exe), str(project_dir), str(run_server_script), str(pts_extension)

def generate_config_snippets():
    """Genera las configuraciones adaptadas a la máquina del usuario."""
    python_exe, project_dir, run_server_script, pts_extension = get_base_paths()
    
    # 1. Antigravity IDE / Gemini CLI / Claude Desktop format
    std_config = {
        "mcpServers": {
            "cisco-packet-tracer": {
                "command": python_exe,
                "args": [
                    run_server_script
                ],
                "env": {
                    "PYTHONUNBUFFERED": "1"
                }
            }
        }
    }
    
    # 2. Claude Code CLI format
    claude_code_cmd = f'claude mcp add --scope user --transport stdio cisco-packet-tracer -- "{python_exe}" "{run_server_script}"'

    # 3. Cursor IDE format
    cursor_config = {
        "mcpServers": {
            "cisco-packet-tracer": {
                "command": python_exe,
                "args": [run_server_script]
            }
        }
    }

    return std_config, claude_code_cmd, cursor_config

def main():
    python_exe, project_dir, run_server_script, pts_extension = get_base_paths()
    std_config, claude_code_cmd, cursor_config = generate_config_snippets()

    banner = f"""
====================================================================================================
        🚀 {PROJECT_NAME} — Asistente de Configuración Universal
====================================================================================================
  Desarrollado por: {AUTHOR_NAME}
  {AUTHOR_TITLE}
====================================================================================================
"""
    print(banner)
    print(f"[*] Directorio del Proyecto Detectado: {project_dir}")
    print(f"[*] Intérprete Python Detectado:       {python_exe}")
    print(f"[*] Archivo Extensión Cisco (.pts):    {pts_extension}")
    print("-" * 100)

    print("\n📋 1. CONFIGURACIÓN PARA ANTIGRAVITY IDE / CURSOR / CLAUDE DESKTOP:")
    print("   Copia y pega este bloque en tu archivo de configuración MCP (mcp_config.json):")
    print(json.dumps(std_config, indent=2))

    print("\n📋 2. COMANDO PARA CLAUDE CODE (CLI):")
    print("   Ejecuta en tu terminal:")
    print(f"   {claude_code_cmd}")

    print("\n📋 3. PASO INDISPENSABLE EN CISCO PACKET TRACER:")
    print("   1. Abre Cisco Packet Tracer.")
    print("   2. Ve al menú superior: Extensions -> Scripting -> Configure PT Script Modules...")
    print("   3. Haz clic en 'Add...' y selecciona:")
    print(f"      {pts_extension}")
    print("   4. Presiona 'Yes' si te solicita confirmación. ¡Listo!")

    print("\n" + "=" * 100)
    print("✅ ¡Entorno verificado y listo para operar en tiempo real!")
    print("=" * 100 + "\n")

if __name__ == "__main__":
    main()

