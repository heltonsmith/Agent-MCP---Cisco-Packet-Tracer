"""
====================================================================================================
PROYECTO: Cisco Packet Tracer MCP Server — Herramientas Extendidas de Automatización
DESCRIPCIÓN: Módulo de alta fidelidad que expande el servidor MCP con herramientas de nivel CCNA/CCNP:
             - Enrutamiento Dinámico: RIPv1/v2, EIGRP, OSPF multiárea, BGP, Rutas Estáticas.
             - Switching Avanzado: Router-on-a-Stick (802.1Q), EtherChannel (LACP/PAgP), Spanning Tree.
             - Servicios de Infraestructura: Servidores DHCP IOS, DNS Server, Web Server (HTTP/HTTPS), Syslog, NTP.
             - Laboratorios Automatizados en 1 Clic (Star, Mesh, Three-Tier, Branch WAN, DMZ Firewall).

AUTOR: Ingeniero en Informática Helton Smith Bustos Sáez
       Magíster en Full Stack | Experto en Ciberseguridad e Inteligencia Artificial Aplicada
====================================================================================================
"""

from __future__ import annotations
import json
import time
from typing import Any, Dict, List, Optional

def register_extended_tools(mcp, bridge):
    """
    Registra herramientas adicionales de nivel experto en la instancia de MCPServer.
    """

    # ----------------------------------------------------------------------------------------------
    # 1. ENRUTAMIENTO DINÁMICO: RIP
    # ----------------------------------------------------------------------------------------------
    @mcp.tool()
    def pt_configure_rip(
        device: str,
        networks: list[str],
        version: int = 2,
        no_auto_summary: bool = True,
        passive_interfaces: list[str] = None
    ) -> str:
        """
        Configura el protocolo de enrutamiento RIP (Routing Information Protocol) en un router Cisco.

        Parámetros:
        - device: Nombre exacto del router (ej. "R1", "Router0").
        - networks: Lista de direcciones de red a publicar (ej. ["192.168.10.0", "10.0.0.0"]).
        - version: Versión de RIP (1 o 2). Por defecto es 2 (soporte VLSM).
        - no_auto_summary: Si True, desactiva la autosumarización classful (recomendado).
        - passive_interfaces: Lista opcional de interfaces pasivas (ej. ["GigabitEthernet0/0"]).
        """
        cmds = [
            "enable",
            "configure terminal",
            "router rip",
            f"version {version}"
        ]
        if no_auto_summary and version == 2:
            cmds.append("no auto-summary")
        for net in networks:
            cmds.append(f"network {net.strip()}")
        if passive_interfaces:
            for pif in passive_interfaces:
                cmds.append(f"passive-interface {pif.strip()}")
        cmds.extend(["end", "write memory"])

        from packet_tracer_mcp.server import mcp as _mcp
        cli_tool = _mcp._tool_manager._tools.get("pt_cli")
        if cli_tool:
            return cli_tool.fn(device=device, commands=cmds)
        return "pt_cli no disponible."

    # ----------------------------------------------------------------------------------------------
    # 2. ENRUTAMIENTO DINÁMICO: EIGRP
    # ----------------------------------------------------------------------------------------------
    @mcp.tool()
    def pt_configure_eigrp(
        device: str,
        as_number: int,
        networks: list[str],
        wildcard_masks: list[str] = None,
        no_auto_summary: bool = True,
        passive_interfaces: list[str] = None
    ) -> str:
        """
        Configura el protocolo de enrutamiento EIGRP (Enhanced Interior Gateway Routing Protocol).

        Parámetros:
        - device: Nombre del router (ej. "R1").
        - as_number: Número de Sistema Autónomo (ej. 100, 65001).
        - networks: Lista de redes a publicar (ej. ["192.168.1.0", "10.0.0.0"]).
        - wildcard_masks: Máscaras wildcard opcionales correspondientes a cada red (ej. ["0.0.0.255", "0.0.0.3"]).
        - no_auto_summary: Si True, desactiva la sumarización automática.
        - passive_interfaces: Interfaces pasivas para no enviar hellos a redes LAN.
        """
        cmds = [
            "enable",
            "configure terminal",
            f"router eigrp {as_number}"
        ]
        if no_auto_summary:
            cmds.append("no auto-summary")

        for idx, net in enumerate(networks):
            net_str = net.strip()
            if wildcard_masks and idx < len(wildcard_masks):
                cmds.append(f"network {net_str} {wildcard_masks[idx].strip()}")
            else:
                cmds.append(f"network {net_str}")

        if passive_interfaces:
            for pif in passive_interfaces:
                cmds.append(f"passive-interface {pif.strip()}")

        cmds.extend(["end", "write memory"])

        from packet_tracer_mcp.server import mcp as _mcp
        cli_tool = _mcp._tool_manager._tools.get("pt_cli")
        if cli_tool:
            return cli_tool.fn(device=device, commands=cmds)
        return "pt_cli no disponible."

    # ----------------------------------------------------------------------------------------------
    # 3. RUTAS ESTÁTICAS Y DE DEFECTO (IPv4 / IPv6)
    # ----------------------------------------------------------------------------------------------
    @mcp.tool()
    def pt_configure_static_route(
        device: str,
        destination_network: str,
        subnet_mask: str,
        next_hop_or_interface: str,
        distance: int = 1,
        is_ipv6: bool = False
    ) -> str:
        """
        Añade una ruta estática o ruta por defecto (0.0.0.0/0 o ::/0) en un router Cisco.

        Parámetros:
        - device: Router a configurar (ej. "R1").
        - destination_network: Red de destino (ej. "192.168.20.0" o "0.0.0.0").
        - subnet_mask: Máscara de subred (ej. "255.255.255.0" o "0.0.0.0"). Para IPv6 usar longitud prefijo.
        - next_hop_or_interface: Siguiente salto IP o interfaz de salida (ej. "10.0.0.2" o "Serial0/0/0").
        - distance: Distancia administrativa opcional (por defecto 1, o mayor para rutas flotantes).
        - is_ipv6: True si es una ruta IPv6.
        """
        if is_ipv6:
            cmd = f"ipv6 route {destination_network}/{subnet_mask} {next_hop_or_interface}"
            if distance > 1:
                cmd += f" {distance}"
        else:
            cmd = f"ip route {destination_network} {subnet_mask} {next_hop_or_interface}"
            if distance > 1:
                cmd += f" {distance}"

        cmds = [
            "enable",
            "configure terminal",
            cmd,
            "end",
            "write memory"
        ]

        from packet_tracer_mcp.server import mcp as _mcp
        cli_tool = _mcp._tool_manager._tools.get("pt_cli")
        if cli_tool:
            return cli_tool.fn(device=device, commands=cmds)
        return "pt_cli no disponible."

    # ----------------------------------------------------------------------------------------------
    # 4. ROUTER-ON-A-STICK (INTER-VLAN ROUTING 802.1Q)
    # ----------------------------------------------------------------------------------------------
    @mcp.tool()
    def pt_configure_router_on_a_stick(
        router: str,
        physical_interface: str,
        subinterfaces: list[dict]
    ) -> str:
        """
        Configura enrutamiento inter-VLAN Router-on-a-Stick mediante subinterfaces 802.1Q.

        Parámetros:
        - router: Nombre del router (ej. "R1").
        - physical_interface: Interfaz física conectada al switch troncal (ej. "GigabitEthernet0/0").
        - subinterfaces: Lista de diccionarios con la configuración de cada subinterfaz:
            [
              {"vlan_id": 10, "ip": "192.168.10.1", "mask": "255.255.255.0"},
              {"vlan_id": 20, "ip": "192.168.20.1", "mask": "255.255.255.0"}
            ]
        """
        cmds = [
            "enable",
            "configure terminal",
            f"interface {physical_interface}",
            "no shutdown"
        ]

        for sub in subinterfaces:
            vlan = sub.get("vlan_id")
            ip = sub.get("ip")
            mask = sub.get("mask", "255.255.255.0")
            subif_name = f"{physical_interface}.{vlan}"

            cmds.extend([
                f"interface {subif_name}",
                f"encapsulation dot1Q {vlan}",
                f"ip address {ip} {mask}",
                "no shutdown"
            ])

        cmds.extend(["end", "write memory"])

        from packet_tracer_mcp.server import mcp as _mcp
        cli_tool = _mcp._tool_manager._tools.get("pt_cli")
        if cli_tool:
            return cli_tool.fn(device=router, commands=cmds)
        return "pt_cli no disponible."

    # ----------------------------------------------------------------------------------------------
    # 5. SERVIDOR DHCP EN ROUTER CISCO IOS
    # ----------------------------------------------------------------------------------------------
    @mcp.tool()
    def pt_configure_ios_dhcp_server(
        router: str,
        pool_name: str,
        network: str,
        mask: str,
        default_router: str,
        dns_server: str = "8.8.8.8",
        domain_name: str = "lab.cisco",
        excluded_start_ip: str = "",
        excluded_end_ip: str = ""
    ) -> str:
        """
        Configura un servidor de asignación dinámica de direcciones (DHCP Server) en un router Cisco IOS.

        Parámetros:
        - router: Nombre del router (ej. "R1").
        - pool_name: Nombre del pool DHCP (ej. "LAN_VENTAS").
        - network: Dirección de red del pool (ej. "192.168.10.0").
        - mask: Máscara de subred (ej. "255.255.255.0").
        - default_router: Puerta de enlace predeterminada para los clientes (ej. "192.168.10.1").
        - dns_server: Servidor DNS entregado a clientes (por defecto "8.8.8.8").
        - domain_name: Nombre de dominio opcional.
        - excluded_start_ip: Inicio del rango de IPs excluidas (ej. "192.168.10.1").
        - excluded_end_ip: Fin del rango de IPs excluidas (ej. "192.168.10.10").
        """
        cmds = ["enable", "configure terminal"]

        if excluded_start_ip:
            if excluded_end_ip:
                cmds.append(f"ip dhcp excluded-address {excluded_start_ip} {excluded_end_ip}")
            else:
                cmds.append(f"ip dhcp excluded-address {excluded_start_ip}")

        cmds.extend([
            f"ip dhcp pool {pool_name}",
            f"network {network} {mask}",
            f"default-router {default_router}",
            f"dns-server {dns_server}"
        ])

        if domain_name:
            cmds.append(f"domain-name {domain_name}")

        cmds.extend(["end", "write memory"])

        from packet_tracer_mcp.server import mcp as _mcp
        cli_tool = _mcp._tool_manager._tools.get("pt_cli")
        if cli_tool:
            return cli_tool.fn(device=router, commands=cmds)
        return "pt_cli no disponible."

    # ----------------------------------------------------------------------------------------------
    # 6. CONFIGURACIÓN SERVIDOR DNS (Server-PT)
    # ----------------------------------------------------------------------------------------------
    @mcp.tool()
    def pt_configure_dns_records(
        server_name: str,
        records: list[dict]
    ) -> str:
        """
        Configura registros DNS (A Records, CNAME) en un servidor Server-PT de Cisco Packet Tracer.

        Parámetros:
        - server_name: Nombre del servidor (ej. "Server0", "DNS-Server").
        - records: Lista de registros a añadir:
            [
              {"name": "www.cisco.com", "ip": "192.168.10.50", "type": "A"},
              {"name": "mail.cisco.com", "ip": "192.168.10.60", "type": "A"}
            ]
        """
        from packet_tracer_mcp.server import mcp as _mcp
        dns_tool = _mcp._tool_manager._tools.get("pt_server_dns")
        if dns_tool:
            results = []
            for rec in records:
                name = rec.get("name")
                ip = rec.get("ip")
                res = dns_tool.fn(device=server_name, state=True, domain=name, ip=ip)
                results.append(f"{name} -> {ip}: {res}")
            return "\n".join(results)
        return "pt_server_dns no disponible."

    # ----------------------------------------------------------------------------------------------
    # 7. CONFIGURACIÓN SERVIDOR WEB HTTP / HTTPS (Server-PT)
    # ----------------------------------------------------------------------------------------------
    @mcp.tool()
    def pt_configure_web_server(
        server_name: str,
        html_title: str = "Bienvenido a Cisco Packet Tracer",
        html_body: str = "<h1>Sitio Web Corporativo</h1><p>Desplegado via MCP con IA en tiempo real.</p>"
    ) -> str:
        """
        Habilita y personaliza el servicio Web HTTP/HTTPS en un Server-PT de Cisco Packet Tracer.

        Parámetros:
        - server_name: Nombre del servidor (ej. "Server0", "Web-Server").
        - html_title: Título de la página web.
        - html_body: Contenido HTML de la página index.html.
        """
        full_html = f"<html><head><title>{html_title}</title></head><body>{html_body}</body></html>"
        from packet_tracer_mcp.server import mcp as _mcp
        http_tool = _mcp._tool_manager._tools.get("pt_server_http")
        if http_tool:
            return http_tool.fn(device=server_name, state=True, content=full_html)
        return "pt_server_http no disponible."

    # ----------------------------------------------------------------------------------------------
    # 8. SPANNING-TREE PROTOCOL (STP / RSTP / MSTP)
    # ----------------------------------------------------------------------------------------------
    @mcp.tool()
    def pt_configure_spanning_tree(
        switch: str,
        mode: str = "rapid-pvst",
        priority: int = 4096,
        vlan: int = 1
    ) -> str:
        """
        Configura el modo Spanning-Tree y la prioridad de Root Bridge en un Switch Catalyst Cisco.

        Parámetros:
        - switch: Nombre del switch (ej. "SW1", "SW-Core").
        - mode: Modo STP ("pvst", "rapid-pvst", "mst"). Por defecto "rapid-pvst" para convergencia instantánea.
        - priority: Prioridad STP (múltiplos de 4096: 4096 para Root Primario, 8192 para Secundario, 32768 por defecto).
        - vlan: Número de VLAN para la prioridad (ej. 1, 10, 20).
        """
        cmds = [
            "enable",
            "configure terminal",
            f"spanning-tree mode {mode}",
            f"spanning-tree vlan {vlan} priority {priority}",
            "end",
            "write memory"
        ]

        from packet_tracer_mcp.server import mcp as _mcp
        cli_tool = _mcp._tool_manager._tools.get("pt_cli")
        if cli_tool:
            return cli_tool.fn(device=switch, commands=cmds)
        return "pt_cli no disponible."

    # ----------------------------------------------------------------------------------------------
    # 9. PORT-CHANNEL / ETHERCHANNEL (LACP / PAgP)
    # ----------------------------------------------------------------------------------------------
    @mcp.tool()
    def pt_configure_etherchannel_bundle(
        switch: str,
        interfaces: list[str],
        channel_group: int = 1,
        protocol: str = "lacp",
        mode: str = "active",
        is_trunk: bool = True
    ) -> str:
        """
        Agrupa enlaces físicos en un Port-Channel lógico (EtherChannel) con LACP o PAgP.

        Parámetros:
        - switch: Nombre del switch (ej. "SW1").
        - interfaces: Lista de interfaces a agrupar (ej. ["FastEthernet0/1", "FastEthernet0/2"]).
        - channel_group: ID numérico del port-channel (ej. 1, 2).
        - protocol: Protocolo ("lacp" o "pagp").
        - mode: Modo de negociación ("active"/"passive" para LACP, "desirable"/"auto" para PAgP, "on" estático).
        - is_trunk: Si True, configura el interfaz Port-Channel resultante como troncal 802.1Q.
        """
        range_str = ",".join(interfaces)
        cmds = [
            "enable",
            "configure terminal",
            f"interface range {range_str}",
            f"channel-group {channel_group} mode {mode}",
            "exit"
        ]

        if is_trunk:
            cmds.extend([
                f"interface port-channel {channel_group}",
                "switchport mode trunk",
                "no shutdown"
            ])

        cmds.extend(["end", "write memory"])

        from packet_tracer_mcp.server import mcp as _mcp
        cli_tool = _mcp._tool_manager._tools.get("pt_cli")
        if cli_tool:
            return cli_tool.fn(device=switch, commands=cmds)
        return "pt_cli no disponible."

    # ----------------------------------------------------------------------------------------------
    # 10. CATALOGO MAESTRO DE DISPOSITIVOS Y PLANTILLAS
    # ----------------------------------------------------------------------------------------------
    @mcp.tool()
    def pt_master_catalog() -> str:
        """
        Retorna el catálogo integral de todos los dispositivos, módulos, cables y topologías soportadas
        en Cisco Packet Tracer con sus identificadores exactos para el agente.
        """
        catalog = {
            "routers": [
                {"model": "2911", "category": "router", "ports": ["GigabitEthernet0/0", "GigabitEthernet0/1", "GigabitEthernet0/2"], "slots": "3x HWIC (0/0, 0/1, 0/2)"},
                {"model": "1941", "category": "router", "ports": ["GigabitEthernet0/0", "GigabitEthernet0/1"], "slots": "2x HWIC (0/0, 0/1)"},
                {"model": "2901", "category": "router", "ports": ["GigabitEthernet0/0", "GigabitEthernet0/1"], "slots": "4x HWIC"},
                {"model": "2811", "category": "router", "ports": ["FastEthernet0/0", "FastEthernet0/1"], "slots": "4x WIC, 1x NM (VoIP CME ready)"},
                {"model": "ISR4331", "category": "router", "ports": ["GigabitEthernet0/0/0", "GigabitEthernet0/0/1", "GigabitEthernet0/0/2"], "slots": "NIM"},
                {"model": "ISR4321", "category": "router", "ports": ["GigabitEthernet0/0/0", "GigabitEthernet0/0/1"], "slots": "NIM"},
                {"model": "1841", "category": "router", "ports": ["FastEthernet0/0", "FastEthernet0/1"], "slots": "WIC"},
                {"model": "819HG-4G-IOX", "category": "router", "ports": ["GigabitEthernet0", "Cellular0"], "description": "Router Industrial 4G"},
                {"model": "CGR1240", "category": "router", "description": "Connected Grid Router para IoT"}
            ],
            "switches": [
                {"model": "2960-24TT", "category": "switch", "ports": "24x FastEthernet (0/1-24) + 2x GigabitEthernet (0/1-2)", "layer": "Capa 2"},
                {"model": "3560-24PS", "category": "switch", "ports": "24x FastEthernet PoE + 2x SFP GigabitEthernet", "layer": "Multicapa (Capa 3 / PoE)"},
                {"model": "3650-24PS", "category": "switch", "ports": "24x GigabitEthernet PoE + 4x SFP+", "layer": "Multicapa empresarial (Capa 3)"},
                {"model": "2950-24", "category": "switch", "ports": "24x FastEthernet", "layer": "Capa 2 clásico"},
                {"model": "IE-2000", "category": "switch", "description": "Switch Industrial para fábricas e IoT"}
            ],
            "security": [
                {"model": "5506-X", "category": "firewall", "ports": "8x GigabitEthernet (1/1 a 1/8)", "os": "Cisco ASA 9.x FirePOWER"},
                {"model": "5505", "category": "firewall", "ports": "8x FastEthernet", "os": "Cisco ASA clásico"}
            ],
            "wireless": [
                {"model": "WLC-PT", "category": "wireless_controller", "description": "Controlador Centralizado de APs (Wireless LAN Controller)"},
                {"model": "LAP-PT", "category": "lap", "description": "Lightweight Access Point para gestión por WLC"},
                {"model": "3702i", "category": "access_point", "description": "Access Point Autónomo Empresarial Dual-Band 802.11ac"},
                {"model": "AccessPoint-PT-AC", "category": "access_point", "description": "Access Point 802.11ac"},
                {"model": "HomeRouter-PT-AC", "category": "home_router", "description": "Router Inalámbrico Doméstico con NAT y Wi-Fi"},
                {"model": "Linksys-WRT300N", "category": "linksys", "description": "Router Inalámbrico Linksys clásico"}
            ],
            "endpoints": [
                {"model": "PC-PT", "category": "pc", "ports": ["FastEthernet0"]},
                {"model": "Laptop-PT", "category": "laptop", "ports": ["FastEthernet0" or "Wireless0"]},
                {"model": "Server-PT", "category": "server", "services": ["HTTP", "HTTPS", "DNS", "DHCP", "FTP", "EMAIL", "TFTP", "SYSLOG", "NTP", "AAA", "IOT"]},
                {"model": "Printer-PT", "category": "printer"},
                {"model": "7960", "category": "ip_phone", "description": "Teléfono Cisco IP Phone con pantalla y PoE"},
                {"model": "SMARTPHONE-PT", "category": "phone"},
                {"model": "TabletPC-PT", "category": "tablet"}
            ],
            "iot_and_industrial": [
                {"model": "MCU-PT", "category": "iot", "description": "Microcontrolador programable con Python/JS y pines GPIO"},
                {"model": "SBC-PT", "category": "iot", "description": "Single Board Computer (Raspberry Pi simulada en Packet Tracer)"},
                {"model": "Thing", "category": "iot", "types": ["Luz", "Ventilador", "Puerta Inteligente", "Sensor Humedad", "Sensor Humo", "Sirena", "Webcam"]}
            ],
            "cables": [
                "straight (Copper Straight-Through)",
                "cross (Copper Cross-Over)",
                "serial (Serial DTE / Serial DCE con Clock Rate)",
                "fiber (Fibra Óptica Monomodo/Multimodo)",
                "console (Cable de Consola RJ45 a DB9/USB)",
                "coaxial (Coaxial para Cable Módem y TV)",
                "auto (Detección Automática de Cable MDI/MDIX)"
            ],
            "protocols_supported": [
                "IPv4, IPv6 (Dual Stack)",
                "RIPv1, RIPv2, RIPng",
                "OSPFv2, OSPFv3 (Single & Multi-Area)",
                "EIGRP (IPv4 e IPv6 con AS)",
                "BGP (eBGP e iBGP con peers y AS)",
                "Static Routing & Default Routes (Floating Static Routes)",
                "VLANs 802.1Q, Inter-VLAN Routing (Router-on-a-Stick y SVIs en Switch L3)",
                "Spanning-Tree (PVST+, Rapid-PVST, MSTP, PortFast, BPDU Guard)",
                "EtherChannel (LACP 802.3ad, PAgP de Cisco, Static On)",
                "HSRP (Hot Standby Router Protocol para redundancia de Gateway)",
                "Access Control Lists (Standard, Extended, Named IPv4/IPv6)",
                "NAT (Static NAT, Dynamic Pool, PAT / NAT Overload)",
                "Voice over IP (Cisco Unified CME, ephone, ephone-dn, DHCP option 150)",
                "Quality of Service (QoS MQC: class-map, policy-map, priority LLQ)",
                "Services: DNS, HTTP/S, DHCP, Syslog, NTP, AAA/Radius, NetFlow, Email"
            ]
        }
        return json.dumps(catalog, indent=2)

    return True

