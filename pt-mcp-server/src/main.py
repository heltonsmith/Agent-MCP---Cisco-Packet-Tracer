"""
Module: main.py
Description: Production Model Context Protocol (MCP) Server for Cisco Packet Tracer.
             Registers all Layer 2, Layer 3, Security, Wireless, IoT, Topology, and Diagnostic
             tools using the official MCP Python SDK and handles communication over stdio.
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys

# Ensure project root is always in sys.path for MCP spawners
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from typing import Any, Dict, List, Optional

from mcp.server import MCPServer
from mcp.server.stdio import stdio_server

# Import tools from modules
from src.tools.topology_and_files import (
    pt_get_topology as _pt_get_topology,
    pt_add_device as _pt_add_device,
    pt_connect_ports as _pt_connect_ports,
    pt_remove_device as _pt_remove_device,
    pt_save_workspace as _pt_save_workspace,
)

from src.tools.layer2_switching import (
    pt_create_vlan as _pt_create_vlan,
    pt_assign_access_port as _pt_assign_access_port,
    pt_configure_trunk as _pt_configure_trunk,
    pt_configure_stp as _pt_configure_stp,
    pt_configure_etherchannel as _pt_configure_etherchannel,
)

from src.tools.layer3_routing import (
    pt_configure_ip as _pt_configure_ip,
    pt_configure_subinterface as _pt_configure_subinterface,
    pt_static_route as _pt_static_route,
    pt_configure_ospf as _pt_configure_ospf,
    pt_configure_bgp as _pt_configure_bgp,
    pt_configure_dhcp_pool as _pt_configure_dhcp_pool,
    pt_configure_rip as _pt_configure_rip,
)

from src.tools.security_firewalls import (
    pt_configure_acl as _pt_configure_acl,
    pt_apply_acl_interface as _pt_apply_acl_interface,
    pt_configure_nat_overload as _pt_configure_nat_overload,
    pt_configure_asa_interfaces as _pt_configure_asa_interfaces,
    pt_configure_vpn_ipsec as _pt_configure_vpn_ipsec,
)

from src.tools.wireless_iot import (
    pt_configure_wireless_router as _pt_configure_wireless_router,
    pt_add_iot_sensor as _pt_add_iot_sensor,
    pt_connect_wireless_client as _pt_connect_wireless_client,
    pt_register_iot_device as _pt_register_iot_device,
)

from src.tools.diagnostics import (
    pt_ping as _pt_ping,
    pt_traceroute as _pt_traceroute,
    pt_show_command as _pt_show_command,
)

# Configure logging to stderr to keep stdout pure for JSON-RPC
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] [MCP-SERVER] %(message)s",
    stream=sys.stderr
)
logger = logging.getLogger("cisco-packet-tracer-mcp")

# Initialize MCPServer
app = MCPServer(
    name="cisco-packet-tracer",
    instructions="Comprehensive CCIE-level Model Context Protocol Server for real-time Cisco Packet Tracer orchestration."
)


# =============================================================================
# 1. TOPOLOGY & WORKSPACE MANAGEMENT TOOLS
# =============================================================================

@app.tool()
def pt_get_topology() -> Dict[str, Any]:
    """
    [TOPOLOGY AWARENESS] Inspects the live Packet Tracer canvas and returns a complete
    inventory of all devices, models, canvas coordinates, interfaces (with IP/IPv6, status, VLAN),
    and active physical cable connections. Allows the LLM to 'see' the entire topology.
    """
    return _pt_get_topology()


@app.tool()
def pt_add_device(
    device_type: str,
    name: str,
    x: int = 200,
    y: int = 200
) -> Dict[str, Any]:
    """
    Deploys a new network hardware device onto the workspace canvas.
    Parameters:
      device_type: Appliance model (e.g., '2911', 'ISR4331', '2960-24TT', 'PC', 'Server', 'ASA-5506-X').
      name: Unique hostname or identifier (e.g. 'R1', 'SW1').
      x, y: Canvas coordinates (defaults: 200, 200).
    """
    return _pt_add_device(device_type=device_type, name=name, x=x, y=y)


@app.tool()
def pt_connect_ports(
    device1: str,
    port1: str,
    device2: str,
    port2: str,
    cable_type: str = "Copper Straight-Through"
) -> Dict[str, Any]:
    """
    Patches a physical cable connection between two interfaces on the workspace canvas.
    Smart default cable_type is 'Copper Straight-Through'.
    """
    return _pt_connect_ports(device1=device1, port1=port1, device2=device2, port2=port2, cable_type=cable_type)


@app.tool()
def pt_remove_device(name: str) -> Dict[str, Any]:
    """
    Removes a network device from the workspace and deletes all its attached cabling links.
    """
    return _pt_remove_device(name=name)


@app.tool()
def pt_save_workspace(filename: str = "topology_backup.pkt") -> Dict[str, Any]:
    """
    Saves the live network topology and device states to a .pkt file on disk.
    """
    return _pt_save_workspace(filename=filename)


# =============================================================================
# 2. LAYER 2 SWITCHING TOOLS
# =============================================================================

@app.tool()
def pt_create_vlan(device: str, vlan_id: int, vlan_name: str) -> Dict[str, Any]:
    """
    Creates an 802.1Q VLAN on a Cisco switch and assigns its administrative name.
    """
    return _pt_create_vlan(device=device, vlan_id=vlan_id, vlan_name=vlan_name)


@app.tool()
def pt_assign_access_port(device: str, interface: str, vlan_id: int) -> Dict[str, Any]:
    """
    Configures a switchport as an untagged access port in a specific VLAN and enables PortFast.
    """
    return _pt_assign_access_port(device=device, interface=interface, vlan_id=vlan_id)


@app.tool()
def pt_configure_trunk(device: str, interface: str, allowed_vlans: Optional[List[int]] = None) -> Dict[str, Any]:
    """
    Configures an interface as an 802.1Q trunk port with optional allowed VLAN pruning.
    """
    return _pt_configure_trunk(device=device, interface=interface, allowed_vlans=allowed_vlans)


@app.tool()
def pt_configure_stp(device: str, vlan_id: int, priority: int) -> Dict[str, Any]:
    """
    Sets the Spanning Tree Protocol (STP) root bridge priority for a given VLAN (multiples of 4096).
    """
    return _pt_configure_stp(device=device, vlan_id=vlan_id, priority=priority)


@app.tool()
def pt_configure_etherchannel(
    device: str,
    interfaces: List[str],
    group_id: int,
    protocol: str = "LACP"
) -> Dict[str, Any]:
    """
    Bundles physical Ethernet interfaces into a Port-Channel using LACP, PAgP, or Static.
    """
    return _pt_configure_etherchannel(device=device, interfaces=interfaces, group_id=group_id, protocol=protocol)


# =============================================================================
# 3. LAYER 3 ROUTING TOOLS (DUAL-STACK IPv4/IPv6)
# =============================================================================

@app.tool()
def pt_configure_ip(
    device: str,
    interface: str,
    ip_address: str,
    subnet_mask: str = "255.255.255.0",
    ipv6_address: Optional[str] = None
) -> Dict[str, Any]:
    """
    Configures Dual-Stack IPv4 and optional IPv6 addresses on an interface and brings it up.
    """
    return _pt_configure_ip(
        device=device,
        interface=interface,
        ip_address=ip_address,
        subnet_mask=subnet_mask,
        ipv6_address=ipv6_address
    )


@app.tool()
def pt_configure_subinterface(
    device: str,
    interface: str,
    subinterface_id: int,
    vlan_id: int,
    ip_address: str,
    subnet_mask: str = "255.255.255.0",
    ipv6_address: Optional[str] = None
) -> Dict[str, Any]:
    """
    Configures Router-on-a-Stick (RoAS) 802.1Q subinterface for inter-VLAN routing (IPv4 & IPv6).
    """
    return _pt_configure_subinterface(
        device=device,
        interface=interface,
        subinterface_id=subinterface_id,
        vlan_id=vlan_id,
        ip_address=ip_address,
        subnet_mask=subnet_mask,
        ipv6_address=ipv6_address
    )


@app.tool()
def pt_static_route(
    device: str,
    destination: str,
    mask_or_prefix: str,
    next_hop: str,
    is_ipv6: bool = False
) -> Dict[str, Any]:
    """
    Installs a static route into the routing table (IPv4 or IPv6).
    """
    return _pt_static_route(
        device=device,
        destination=destination,
        mask_or_prefix=mask_or_prefix,
        next_hop=next_hop,
        is_ipv6=is_ipv6
    )


@app.tool()
def pt_configure_ospf(
    device: str,
    process_id: int,
    router_id: str,
    networks: List[Dict[str, Any]],
    is_ospfv3: bool = False
) -> Dict[str, Any]:
    """
    Configures OSPFv2 or OSPFv3 routing process, Router-ID, and network statements.
    networks format: [{"network": "192.168.1.0", "wildcard_mask": "0.0.0.255", "area": 0}]
    """
    return _pt_configure_ospf(
        device=device,
        process_id=process_id,
        router_id=router_id,
        networks=networks,
        is_ospfv3=is_ospfv3
    )


@app.tool()
def pt_configure_bgp(
    device: str,
    as_number: int,
    neighbors: List[Dict[str, Any]],
    networks: List[str]
) -> Dict[str, Any]:
    """
    Configures BGP routing process, establishes neighbor peering, and advertises networks.
    neighbors format: [{"ip": "10.0.0.2", "remote_as": 65002}]
    """
    return _pt_configure_bgp(
        device=device,
        as_number=as_number,
        neighbors=neighbors,
        networks=networks
    )


@app.tool()
def pt_configure_dhcp_pool(
    device: str,
    pool_name: str,
    network: str,
    mask: str = "255.255.255.0",
    default_router: str = "192.168.1.1",
    dns_server: str = "8.8.8.8"
) -> Dict[str, Any]:
    """
    Configures a Cisco IOS DHCP Server pool, sets gateway/DNS, and excludes gateway IP.
    """
    return _pt_configure_dhcp_pool(
        device=device,
        pool_name=pool_name,
        network=network,
        mask=mask,
        default_router=default_router,
        dns_server=dns_server
    )


@app.tool()
def pt_configure_rip(
    device: str,
    networks: List[str],
    version: int = 2,
    no_auto_summary: bool = True
) -> Dict[str, Any]:
    """
    Configures Routing Information Protocol (RIPv1 or RIPv2) on a Cisco router,
    advertises networks, and disables automatic summarization.
    """
    return _pt_configure_rip(
        device=device,
        networks=networks,
        version=version,
        no_auto_summary=no_auto_summary
    )


# =============================================================================
# 4. SECURITY & FIREWALL TOOLS
# =============================================================================

@app.tool()
def pt_configure_acl(
    device: str,
    acl_name_or_number: str,
    rules: List[Dict[str, Any]],
    is_extended: bool = False
) -> Dict[str, Any]:
    """
    Creates Standard or Extended Access Control Lists (ACLs).
    rules format: [{"action": "permit", "protocol": "tcp", "source": "192.168.1.0 0.0.0.255", "destination": "any", "port": "eq 80"}]
    """
    return _pt_configure_acl(
        device=device,
        acl_name_or_number=acl_name_or_number,
        rules=rules,
        is_extended=is_extended
    )


@app.tool()
def pt_apply_acl_interface(
    device: str,
    interface: str,
    acl_name: str,
    direction: str
) -> Dict[str, Any]:
    """
    Applies an ACL to an interface in the 'in' or 'out' direction.
    """
    return _pt_apply_acl_interface(
        device=device,
        interface=interface,
        acl_name=acl_name,
        direction=direction
    )


@app.tool()
def pt_configure_nat_overload(
    device: str,
    inside_interface: str,
    outside_interface: str,
    acl_number: int = 1
) -> Dict[str, Any]:
    """
    Configures Dynamic NAT with Port Address Translation (PAT / Overload) for private LAN access to WAN.
    """
    return _pt_configure_nat_overload(
        device=device,
        inside_interface=inside_interface,
        outside_interface=outside_interface,
        acl_number=acl_number
    )


@app.tool()
def pt_configure_asa_interfaces(
    device: str,
    inside_ip: str,
    outside_ip: str
) -> Dict[str, Any]:
    """
    Provisions a Cisco ASA 5506-X Firewall:
    - GigabitEthernet1/1: Nameif 'inside', security-level 100
    - GigabitEthernet1/2: Nameif 'outside', security-level 0
    """
    return _pt_configure_asa_interfaces(
        device=device,
        inside_ip=inside_ip,
        outside_ip=outside_ip
    )


@app.tool()
def pt_configure_vpn_ipsec(
    device_a: str,
    device_b: str,
    peer_ip: str,
    pre_shared_key: str = "Cisco123Secure!",
    transform_set: str = "ESP-AES-SHA"
) -> Dict[str, Any]:
    """
    Configures a Site-to-Site IPsec VPN tunnel between two Cisco IOS routers.
    """
    return _pt_configure_vpn_ipsec(
        device_a=device_a,
        device_b=device_b,
        peer_ip=peer_ip,
        pre_shared_key=pre_shared_key,
        transform_set=transform_set
    )


# =============================================================================
# 5. WIRELESS LAN & IoT TOOLS
# =============================================================================

@app.tool()
def pt_configure_wireless_router(
    device: str,
    ssid: str,
    auth_type: str = "WPA2-PSK",
    password: str = "SecretWifi123",
    channel: int = 6
) -> Dict[str, Any]:
    """
    Configures SSID, 2.4GHz RF channel, and WPA2 security passphrase on a wireless router/AP.
    """
    return _pt_configure_wireless_router(
        device=device,
        ssid=ssid,
        auth_type=auth_type,
        password=password,
        channel=channel
    )


@app.tool()
def pt_add_iot_sensor(
    sensor_type: str,
    name: str,
    x: int = 350,
    y: int = 350
) -> Dict[str, Any]:
    """
    Spawns an IoT environmental sensor/actuator (Motion Detector, Temperature Monitor, Smoke Detector, etc.).
    """
    return _pt_add_iot_sensor(sensor_type=sensor_type, name=name, x=x, y=y)


@app.tool()
def pt_connect_wireless_client(
    client_name: str,
    ssid: str,
    password: str
) -> Dict[str, Any]:
    """
    Associates a wireless endpoint (PC, Laptop, Smartphone, IoT device) to a target Wi-Fi SSID.
    """
    return _pt_connect_wireless_client(client_name=client_name, ssid=ssid, password=password)


@app.tool()
def pt_register_iot_device(
    device_name: str,
    server_ip: str,
    username: str = "admin",
    password: str = "admin"
) -> Dict[str, Any]:
    """
    Registers an IoT device to a centralized Packet Tracer IoT Registration Server.
    """
    return _pt_register_iot_device(
        device_name=device_name,
        server_ip=server_ip,
        username=username,
        password=password
    )


# =============================================================================
# 6. DIAGNOSTICS & TELEMETRY TOOLS
# =============================================================================

@app.tool()
def pt_ping(source: str, destination: str) -> Dict[str, Any]:
    """
    Executes a real-time ICMP ping test between two network nodes and returns latency/success rates.
    """
    return _pt_ping(source=source, destination=destination)


@app.tool()
def pt_traceroute(source: str, destination: str) -> Dict[str, Any]:
    """
    Traces the multi-hop Layer 3 path and hop latencies between source and destination.
    """
    return _pt_traceroute(source=source, destination=destination)


@app.tool()
def pt_show_command(device: str, command: str) -> Dict[str, Any]:
    """
    Executes any Cisco IOS show / verification command ('show ip route', 'show running-config', etc.).
    """
    return _pt_show_command(device=device, command=command)


# =============================================================================
# SERVER RUNTIME ENTRYPOINT
# =============================================================================

async def main() -> None:
    """Async entrypoint using stdio_server() to handle MCP JSON-RPC messages."""
    logger.info("Initializing Cisco Packet Tracer MCP Server on STDIO transport...")
    async with stdio_server() as (read_stream, write_stream):
        await app._mcp_server.run(
            read_stream,
            write_stream,
            app._mcp_server.create_initialization_options()
        )


def run() -> None:
    """Synchronous launcher entrypoint."""
    try:
        # FastMCP provides direct run() with stdio transport
        app.run(transport="stdio")
    except AttributeError:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Cisco Packet Tracer MCP Server shut down cleanly.")


if __name__ == "__main__":
    run()

