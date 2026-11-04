"""
Module: layer3_routing.py
Description: Production Layer 3 routing automation for Cisco Packet Tracer.
             Provides Dual-Stack IPv4/IPv6 address provisioning, Router-on-a-Stick subinterfaces,
             Static Routes, OSPFv2/OSPFv3 multi-area routing, BGP peering, and Cisco IOS DHCP Server pools.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from src.bridge.pt_client import get_pt_bridge


# -----------------------------------------------------------------------------
# Pydantic Input Schemas
# -----------------------------------------------------------------------------

class ConfigureIpInput(BaseModel):
    device: str = Field(..., description="Target router or Layer 3 switch hostname (e.g. 'R1').")
    interface: str = Field(..., description="Interface name (e.g. 'GigabitEthernet0/0').")
    ip_address: str = Field(..., description="IPv4 address to assign (e.g. '192.168.1.1').")
    subnet_mask: str = Field(default="255.255.255.0", description="IPv4 subnet mask. Smart default: '255.255.255.0'.")
    ipv6_address: Optional[str] = Field(
        default=None,
        description="Optional IPv6 address with prefix (e.g. '2001:db8:acad:1::1/64'). Enables Dual-Stack."
    )


class ConfigureSubinterfaceInput(BaseModel):
    device: str = Field(..., description="Target router hostname.")
    interface: str = Field(..., description="Parent physical interface (e.g. 'GigabitEthernet0/0').")
    subinterface_id: int = Field(..., ge=1, le=4094, description="Subinterface logical index (e.g. 10).")
    vlan_id: int = Field(..., ge=1, le=4094, description="802.1Q VLAN encapsulation tag.")
    ip_address: str = Field(..., description="IPv4 address for the subinterface gateway.")
    subnet_mask: str = Field(default="255.255.255.0", description="IPv4 subnet mask.")
    ipv6_address: Optional[str] = Field(
        default=None,
        description="Optional IPv6 address with prefix length (e.g. '2001:db8:10::1/64')."
    )


class StaticRouteInput(BaseModel):
    device: str = Field(..., description="Target router hostname.")
    destination: str = Field(..., description="Destination network prefix (e.g. '10.0.0.0' or '2001:db8:dead::').")
    mask_or_prefix: str = Field(..., description="Subnet mask for IPv4 (e.g. '255.0.0.0') or prefix length for IPv6 (e.g. '64').")
    next_hop: str = Field(..., description="Next-hop IP address or exit interface (e.g. '192.168.12.2').")
    is_ipv6: bool = Field(default=False, description="Flag indicating if the route is an IPv6 static route.")


class OspfNetworkEntry(BaseModel):
    network: str = Field(..., description="Network IP prefix (e.g. '192.168.1.0').")
    wildcard_mask: str = Field(default="0.0.0.255", description="Inverse wildcard mask (e.g. '0.0.0.255').")
    area: int = Field(default=0, ge=0, description="OSPF Area ID (0 for backbone).")


class ConfigureOspfInput(BaseModel):
    device: str = Field(..., description="Target router hostname.")
    process_id: int = Field(default=1, ge=1, le=65535, description="OSPF process identifier (1-65535).")
    router_id: str = Field(..., description="32-bit dotted-decimal Router ID (e.g. '1.1.1.1').")
    networks: List[OspfNetworkEntry] = Field(..., description="List of networks, wildcards, and OSPF areas.")
    is_ospfv3: bool = Field(default=False, description="Flag indicating if OSPFv3 (IPv6) should be configured.")


class BgpNeighborEntry(BaseModel):
    ip: str = Field(..., description="Remote BGP peer IP address.")
    remote_as: int = Field(..., ge=1, le=65535, description="Autonomous System Number of the peer.")


class ConfigureBgpInput(BaseModel):
    device: str = Field(..., description="Target router hostname.")
    as_number: int = Field(..., ge=1, le=65535, description="Local Autonomous System (AS) number.")
    neighbors: List[BgpNeighborEntry] = Field(..., description="List of BGP peers and their remote ASNs.")
    networks: List[str] = Field(..., description="List of networks to advertise (e.g. ['10.0.0.0/8', '192.168.1.0 255.255.255.0']).")


class ConfigureRipInput(BaseModel):
    device: str = Field(..., description="Target router hostname.")
    networks: List[str] = Field(..., description="List of major networks to advertise under RIP (e.g. ['10.0.0.0', '192.168.10.0']).")
    version: int = Field(default=2, ge=1, le=2, description="RIP version (1 or 2). Default: 2.")
    no_auto_summary: bool = Field(default=True, description="Disable automatic network summarization (for version 2).")


class ConfigureDhcpPoolInput(BaseModel):
    device: str = Field(..., description="Target router hostname.")
    pool_name: str = Field(..., description="Name for the DHCP pool (e.g. 'LAN_USERS').")
    network: str = Field(..., description="Network address (e.g. '192.168.10.0').")
    mask: str = Field(default="255.255.255.0", description="Network subnet mask.")
    default_router: str = Field(..., description="Default gateway IP for DHCP clients.")
    dns_server: str = Field(default="8.8.8.8", description="DNS server IP. Default: '8.8.8.8'.")


# -----------------------------------------------------------------------------
# Tool Implementations
# -----------------------------------------------------------------------------

def pt_configure_ip(
    device: str,
    interface: str,
    ip_address: str,
    subnet_mask: str = "255.255.255.0",
    ipv6_address: Optional[str] = None
) -> Dict[str, Any]:
    """
    Configures Dual-Stack IPv4 and optional IPv6 addresses on a router/switch interface.
    Brings up the physical link with 'no shutdown'.
    """
    validated = ConfigureIpInput(
        device=device,
        interface=interface,
        ip_address=ip_address,
        subnet_mask=subnet_mask,
        ipv6_address=ipv6_address
    )

    commands: List[str] = []
    if validated.ipv6_address:
        commands.append("ipv6 unicast-routing")

    commands.extend([
        f"interface {validated.interface}",
        f"ip address {validated.ip_address} {validated.subnet_mask}"
    ])

    if validated.ipv6_address:
        ipv6_str = validated.ipv6_address if "/" in validated.ipv6_address else f"{validated.ipv6_address}/64"
        commands.extend([
            "ipv6 enable",
            f"ipv6 address {ipv6_str}"
        ])

    commands.extend(["no shutdown", "exit"])

    bridge = get_pt_bridge()
    cli_output = bridge.execute_cli(validated.device, commands)
    return {
        "device": validated.device,
        "interface": validated.interface,
        "ipv4": f"{validated.ip_address} {validated.subnet_mask}",
        "ipv6": validated.ipv6_address,
        "status": "configured",
        "cli_output": cli_output
    }


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
    Implements 802.1Q Router-on-a-Stick (RoAS) inter-VLAN routing with dual-stack support.
    """
    validated = ConfigureSubinterfaceInput(
        device=device,
        interface=interface,
        subinterface_id=subinterface_id,
        vlan_id=vlan_id,
        ip_address=ip_address,
        subnet_mask=subnet_mask,
        ipv6_address=ipv6_address
    )

    subif_name = f"{validated.interface}.{validated.subinterface_id}"
    commands: List[str] = []

    if validated.ipv6_address:
        commands.append("ipv6 unicast-routing")

    # Ensure parent interface is physically un-shut
    commands.extend([
        f"interface {validated.interface}",
        "no shutdown",
        "exit",
        f"interface {subif_name}",
        f"encapsulation dot1Q {validated.vlan_id}",
        f"ip address {validated.ip_address} {validated.subnet_mask}"
    ])

    if validated.ipv6_address:
        ipv6_str = validated.ipv6_address if "/" in validated.ipv6_address else f"{validated.ipv6_address}/64"
        commands.extend([
            "ipv6 enable",
            f"ipv6 address {ipv6_str}"
        ])

    commands.extend(["no shutdown", "exit"])

    bridge = get_pt_bridge()
    cli_output = bridge.execute_cli(validated.device, commands)
    return {
        "device": validated.device,
        "subinterface": subif_name,
        "vlan_id": validated.vlan_id,
        "ipv4": f"{validated.ip_address} {validated.subnet_mask}",
        "ipv6": validated.ipv6_address,
        "status": "configured",
        "cli_output": cli_output
    }


def pt_static_route(
    device: str,
    destination: str,
    mask_or_prefix: str,
    next_hop: str,
    is_ipv6: bool = False
) -> Dict[str, Any]:
    """
    Installs a static route into the routing table for IPv4 or IPv6.
    """
    validated = StaticRouteInput(
        device=device,
        destination=destination,
        mask_or_prefix=mask_or_prefix,
        next_hop=next_hop,
        is_ipv6=is_ipv6
    )

    commands: List[str] = []
    if validated.is_ipv6:
        commands.append("ipv6 unicast-routing")
        prefix = validated.mask_or_prefix.lstrip("/")
        commands.append(f"ipv6 route {validated.destination}/{prefix} {validated.next_hop}")
    else:
        commands.append(f"ip route {validated.destination} {validated.mask_or_prefix} {validated.next_hop}")

    bridge = get_pt_bridge()
    cli_output = bridge.execute_cli(validated.device, commands)
    return {
        "device": validated.device,
        "route_type": "IPv6" if validated.is_ipv6 else "IPv4",
        "destination": validated.destination,
        "mask_or_prefix": validated.mask_or_prefix,
        "next_hop": validated.next_hop,
        "status": "installed",
        "cli_output": cli_output
    }


def pt_configure_ospf(
    device: str,
    process_id: int,
    router_id: str,
    networks: List[Dict[str, Any]],
    is_ospfv3: bool = False
) -> Dict[str, Any]:
    """
    Configures OSPFv2 or OSPFv3 dynamic routing process, sets Router-ID, and advertises networks across areas.
    """
    validated = ConfigureOspfInput(
        device=device,
        process_id=process_id,
        router_id=router_id,
        networks=[OspfNetworkEntry(**net) for net in networks],
        is_ospfv3=is_ospfv3
    )

    commands: List[str] = []
    if validated.is_ospfv3:
        commands.extend([
            "ipv6 unicast-routing",
            f"ipv6 router ospf {validated.process_id}",
            f"router-id {validated.router_id}"
        ])
        for entry in validated.networks:
            # In OSPFv3 Packet Tracer, network can be tied to interface or network statement
            commands.append(f"network {entry.network} area {entry.area}")
    else:
        commands.extend([
            f"router ospf {validated.process_id}",
            f"router-id {validated.router_id}"
        ])
        for entry in validated.networks:
            commands.append(f"network {entry.network} {entry.wildcard_mask} area {entry.area}")

    commands.append("exit")

    bridge = get_pt_bridge()
    cli_output = bridge.execute_cli(validated.device, commands)
    return {
        "device": validated.device,
        "process_id": validated.process_id,
        "router_id": validated.router_id,
        "protocol": "OSPFv3" if validated.is_ospfv3 else "OSPFv2",
        "advertised_networks": len(validated.networks),
        "status": "configured",
        "cli_output": cli_output
    }


def pt_configure_bgp(
    device: str,
    as_number: int,
    neighbors: List[Dict[str, Any]],
    networks: List[str]
) -> Dict[str, Any]:
    """
    Configures Border Gateway Protocol (BGP) routing engine, establishes neighbor peering, and originates network NLRI.
    """
    validated = ConfigureBgpInput(
        device=device,
        as_number=as_number,
        neighbors=[BgpNeighborEntry(**nbr) for nbr in neighbors],
        networks=networks
    )

    commands = [
        f"router bgp {validated.as_number}",
        "bgp log-neighbor-changes"
    ]

    for nbr in validated.neighbors:
        commands.append(f"neighbor {nbr.ip} remote-as {nbr.remote_as}")

    for net in validated.networks:
        parts = net.split()
        if len(parts) == 1:
            if "/" in parts[0]:
                ip_part, cidr = parts[0].split("/")
                # Convert CIDR to subnet mask
                cidr_int = int(cidr)
                mask_int = (0xffffffff >> (32 - cidr_int)) << (32 - cidr_int)
                mask_str = f"{(mask_int >> 24) & 255}.{(mask_int >> 16) & 255}.{(mask_int >> 8) & 255}.{mask_int & 255}"
                commands.append(f"network {ip_part} mask {mask_str}")
            else:
                commands.append(f"network {parts[0]}")
        elif len(parts) >= 2 and parts[1].lower() == "mask":
            commands.append(f"network {parts[0]} mask {parts[2]}")
        elif len(parts) == 2:
            commands.append(f"network {parts[0]} mask {parts[1]}")

    commands.append("exit")

    bridge = get_pt_bridge()
    cli_output = bridge.execute_cli(validated.device, commands)
    return {
        "device": validated.device,
        "as_number": validated.as_number,
        "peers_configured": len(validated.neighbors),
        "networks_advertised": validated.networks,
        "status": "configured",
        "cli_output": cli_output
    }


def pt_configure_dhcp_pool(
    device: str,
    pool_name: str,
    network: str,
    mask: str = "255.255.255.0",
    default_router: str = "192.168.1.1",
    dns_server: str = "8.8.8.8"
) -> Dict[str, Any]:
    """
    Configures an autonomous Cisco IOS DHCP Server pool with gateway and DNS server attributes.
    Automatically reserves the default gateway address to prevent address conflicts.
    """
    validated = ConfigureDhcpPoolInput(
        device=device,
        pool_name=pool_name,
        network=network,
        mask=mask,
        default_router=default_router,
        dns_server=dns_server
    )

    commands = [
        f"ip dhcp excluded-address {validated.default_router}",
        f"ip dhcp pool {validated.pool_name}",
        f"network {validated.network} {validated.mask}",
        f"default-router {validated.default_router}",
        f"dns-server {validated.dns_server}",
        "exit"
    ]

    bridge = get_pt_bridge()
    cli_output = bridge.execute_cli(validated.device, commands)
    return {
        "device": validated.device,
        "pool_name": validated.pool_name,
        "network": validated.network,
        "mask": validated.mask,
        "default_router": validated.default_router,
        "dns_server": validated.dns_server,
        "status": "configured",
        "cli_output": cli_output
    }


def pt_configure_rip(
    device: str,
    networks: List[str],
    version: int = 2,
    no_auto_summary: bool = True
) -> Dict[str, Any]:
    """
    Configures Routing Information Protocol (RIPv1 or RIPv2) routing engine,
    advertises networks, and disables auto-summary.
    """
    validated = ConfigureRipInput(
        device=device,
        networks=networks,
        version=version,
        no_auto_summary=no_auto_summary
    )

    commands = [
        "router rip",
        f"version {validated.version}"
    ]

    if validated.no_auto_summary:
        commands.append("no auto-summary")

    for net in validated.networks:
        commands.append(f"network {net}")

    commands.append("exit")

    bridge = get_pt_bridge()
    cli_output = bridge.execute_cli(validated.device, commands)
    return {
        "device": validated.device,
        "protocol": f"RIPv{validated.version}",
        "networks": validated.networks,
        "no_auto_summary": validated.no_auto_summary,
        "status": "configured",
        "cli_output": cli_output
    }


