"""
====================================================================================================
PROYECTO: Cisco Packet Tracer MCP Server (Live Real-Time Automation)
DESCRIPCIÓN: Lanzador universal, portátil y multiplataforma del Servidor MCP para Cisco Packet Tracer.
             Permite a agentes de IA (Antigravity IDE/CLI, Claude Code, Cursor, OpenCode, VS Code)
             comunicarse de forma transparente y en tiempo real con Cisco Packet Tracer.
             Incluye el catálogo maestro de dispositivos y herramientas extendidas de Capa 2, Capa 3,
             Servicios (DNS, Web, DHCP) y Seguridad Cisco IOS.

AUTOR: Ingeniero en Informática Helton Smith Bustos Sáez
       Magíster en Full Stack | Experto en Ciberseguridad e Inteligencia Artificial Aplicada
====================================================================================================
"""

import sys
import os
import subprocess
from pathlib import Path

# Constantes de autoría y branding
AUTHOR_NAME = "Ing. Helton Smith Bustos Sáez"
AUTHOR_TITLE = "Magíster en Full Stack | Experto en Ciberseguridad e Inteligencia Artificial Aplicada"
PROJECT_NAME = "Cisco Packet Tracer MCP Server (Enterprise Real-Time)"

def setup_environment():
    """
    Configura y asegura los directorios y tokens locales necesarios para la comunicación
    bidireccional entre el servidor MCP y el Script Engine de Cisco Packet Tracer.
    Funciona de manera dinámica en cualquier usuario y sistema operativo (Windows, macOS, Linux).
    """
    try:
        from packet_tracer_mcp.infrastructure.execution.bridge_token import token_dir, get_bridge_token
        # Generar o asegurar el token local del puente
        token = get_bridge_token()
        t_dir = token_dir()
        bridge_folder = t_dir / "bridge"
        bridge_folder.mkdir(parents=True, exist_ok=True)
    except Exception as exc:
        # Fallback manual en caso de que las librerías no estén en el path aún
        if os.name == "nt":
            appdata = os.environ.get("LOCALAPPDATA", os.path.expanduser("~\\AppData\\Local"))
            t_dir = Path(appdata) / "packet-tracer-mcp"
        else:
            t_dir = Path.home() / ".config" / "packet-tracer-mcp"
        t_dir.mkdir(parents=True, exist_ok=True)
        (t_dir / "bridge").mkdir(parents=True, exist_ok=True)

def main():
    """Punto de entrada principal para la ejecución del servidor MCP."""
    setup_environment()
    
    # Importar y arrancar el servidor MCP oficial en modo stdio para clientes IA
    try:
        from packet_tracer_mcp.server import mcp, BRIDGE, main as pt_mcp_main
        
        # Registrar las herramientas extendidas de alto nivel desarrolladas por el autor
        try:
            from extended_tools import register_extended_tools
            register_extended_tools(mcp, BRIDGE)
        except Exception as err:
            sys.stderr.write(f"[WARN] No se pudieron cargar las herramientas extendidas: {err}\n")

        # Si no se pasó argumento de transporte, forzar --stdio para que se comunique con el agente
        if "--stdio" not in sys.argv and "install-skill" not in sys.argv:
            sys.argv.append("--stdio")
        pt_mcp_main()
    except ImportError:
        sys.stderr.write(
            f"\n[ERROR] No se encontraron las dependencias necesarias de {PROJECT_NAME}.\n"
            f"Por favor ejecuta: pip install -r requirements.txt\n"
            f"Desarrollado por: {AUTHOR_NAME} ({AUTHOR_TITLE})\n\n"
        )
        sys.exit(1)
    except Exception as e:
        sys.stderr.write(f"\n[ERROR CRÍTICO] {e}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
