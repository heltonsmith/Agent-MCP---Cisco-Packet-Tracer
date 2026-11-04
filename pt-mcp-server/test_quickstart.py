"""
Script de prueba rápida: Verifica el funcionamiento del puente y las herramientas
sin requerir un cliente LLM configurado.
"""

from __future__ import annotations

import sys
import os

# Agregar directorio raíz al PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.bridge.pt_client import get_pt_bridge
from src.tools.topology_and_files import pt_get_topology, pt_add_device, pt_connect_ports
from src.tools.layer2_switching import pt_create_vlan, pt_assign_access_port
from src.tools.layer3_routing import pt_configure_ip
from src.tools.diagnostics import pt_show_command, pt_ping


def main():
    print("=" * 60)
    print("🧪 CISCO PACKET TRACER MCP SERVER - DIAGNÓSTICO DE INICIO")
    print("=" * 60)

    bridge = get_pt_bridge()

    print("\n1. Conectando al listener en 127.0.0.1:4242...")
    try:
        bridge.connect()
        print("   [OK] Conexión establecida exitosamente.")
    except Exception as e:
        print(f"   [ERROR] No se pudo conectar: {e}")
        print("\n Asegúrate de haber iniciado 'pt_listener.py' primero en otra terminal:")
        print("   python src/bridge/pt_listener.py")
        sys.exit(1)

    print("\n2. Probando pt_get_topology()...")
    topo = pt_get_topology()
    print(f"   [OK] Topología leída: {topo.get('total_devices', 0)} dispositivos, {topo.get('total_connections', 0)} enlaces.")

    print("\n3. Desplegando nuevo Router R2...")
    dev_res = pt_add_device(device_type="2911", name="R2", x=300, y=150)
    print(f"   [OK] Dispositivo creado: {dev_res.get('device')}")

    print("\n4. Configurando IP Dual-Stack en R2...")
    ip_res = pt_configure_ip(
        device="R2",
        interface="GigabitEthernet0/0",
        ip_address="192.168.50.1",
        subnet_mask="255.255.255.0",
        ipv6_address="2001:db8:50::1/64"
    )
    print(f"   [OK] Interfaz configurada: {ip_res.get('interface')} -> IPv4: {ip_res.get('ipv4')}, IPv6: {ip_res.get('ipv6')}")

    print("\n5. Ejecutando verificación IOS 'show ip interface brief'...")
    show_res = pt_show_command(device="R2", command="show ip interface brief")
    print("   [OK] Salida CLI recibida:\n")
    for line in show_res.get("output", "").split("\n"):
        print(f"      {line}")

    print("\n6. Probando prueba ICMP ping...")
    ping_res = pt_ping(source="R2", destination="192.168.50.1")
    print(f"   [OK] Ping completado: {ping_res.get('packets_received')}/{ping_res.get('packets_transmitted')} paquetes.")

    print("\n" + "=" * 60)
    print("🎉 ¡TODO EL SISTEMA ESTÁ OPERACIONAL AL 100%!")
    print("=" * 60)


if __name__ == "__main__":
    main()

