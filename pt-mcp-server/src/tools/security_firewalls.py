"""
Module: security_firewalls.py
Description: Enterprise security, access control lists (ACLs), Network Address Translation (NAT/PAT),
             Cisco ASA 5506-X firewall interface provisioning, and Site-to-Site IPsec VPN tunnels.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from src.bridge.pt_client import get_pt_bridge


# -----------------------------------------------------------------------------
# Pydantic Input Schemas
# -----------------------------------------------------------------------------

class AclRule(BaseModel):
    action: str = Field(..., description="'permit' or 'deny'.")
    protocol: str = Field(default="ip", description="'ip', 'tcp', 'udp', 'icmp'. (Only for extended ACLs).")
    source: str = Field(..., description="Source address (e.g. 'any', 'host 10.0.0.5', '192.168.1.0 0.0.0.255').")
    destination: Optional[str] = Field(default=None, description="Destination address for extended ACLs (e.g. 'any', 'host 8.8.8.8').")
    port: Optional[str] = Field(default=None, description="Optional layer 4 operator/port (e.g. 'eq 80', 'eq 443').")


class ConfigureAclInput(BaseModel):
    device: str = Field(..., description="Target router or firewall hostname (e.g. 'R1').")
    acl_name_or_number: str = Field(..., description="Numeric identifier (1-99 standard, 100-199 extended) or named string.")
    rules: List[AclRule] = Field(..., description="List of access-control filtering rules.")
    is_extended: bool = Field(default=False, description="Set True for 5-tuple extended ACL inspection.")


class ApplyAclInterfaceInput(BaseModel):
    device: str = Field(..., description="Target router or firewall hostname.")
    interface: str = Field(..., description="Interface name (e.g. 'GigabitEthernet0/0').")
    acl_name: str = Field(..., description="Name or numeric identifier of the ACL to apply.")
    direction: str = Field(..., description="'in' for inbound filtering or 'out' for outbound.")


class ConfigureNatOverloadInput(BaseModel):
    device: str = Field(..., description="Target gateway router hostname.")
    inside_interface: str = Field(..., description="LAN ingress interface (e.g. 'GigabitEthernet0/1').")
    outside_interface: str = Field(..., description="WAN egress interface (e.g. 'GigabitEthernet0/0').")
    acl_number: int = Field(default=1, ge=1, le=99, description="Standard ACL number matching private subnets.")


class ConfigureAsaInterfacesInput(BaseModel):
    device: str = Field(..., description="Cisco ASA hostname (e.g. 'ASA1').")
    inside_ip: str = Field(..., description="Inside interface IPv4 address (e.g. '192.168.1.1').")
    outside_ip: str = Field(..., description="Outside interface IPv4 address (e.g. '203.0.113.2').")
    inside_mask: str = Field(default="255.255.255.0", description="Inside subnet mask.")
    outside_mask: str = Field(default="255.255.255.0", description="Outside subnet mask.")


class ConfigureVpnIpsecInput(BaseModel):
    device_a: str = Field(..., description="Local router hostname (e.g. 'R1').")
    device_b: str = Field(..., description="Remote peer router hostname (e.g. 'R2').")
    peer_ip: str = Field(..., description="Public IP address of the remote VPN peer.")
    pre_shared_key: str = Field(default="Cisco123Secure!", description="ISAKMP Phase 1 Pre-Shared Key.")
    transform_set: str = Field(default="ESP-AES-SHA", description="IPsec Phase 2 Transform Set name.")


# -----------------------------------------------------------------------------
# Tool Implementations
# -----------------------------------------------------------------------------

def pt_configure_acl(
    device: str,
    acl_name_or_number: str,
    rules: List[Dict[str, Any]],
    is_extended: bool = False
) -> Dict[str, Any]:
    """
    Constructs and installs Standard or Extended Cisco IOS Access Control Lists (ACLs).
    """
    validated = ConfigureAclInput(
        device=device,
        acl_name_or_number=acl_name_or_number,
        rules=[AclRule(**r) for r in rules],
        is_extended=is_extended
    )

    commands: List[str] = []
    is_numeric = validated.acl_name_or_number.isdigit()

    if is_numeric:
        for rule in validated.rules:
            if validated.is_extended:
                dest = rule.destination or "any"
                port_clause = f" {rule.port}" if rule.port else ""
                commands.append(
                    f"access-list {validated.acl_name_or_number} {rule.action} {rule.protocol} {rule.source} {dest}{port_clause}"
                )
            else:
                commands.append(
                    f"access-list {validated.acl_name_or_number} {rule.action} {rule.source}"
                )
    else:
        acl_type = "extended" if validated.is_extended else "standard"
        commands.append(f"ip access-list {acl_type} {validated.acl_name_or_number}")
        for rule in validated.rules:
            if validated.is_extended:
                dest = rule.destination or "any"
                port_clause = f" {rule.port}" if rule.port else ""
                commands.append(f"{rule.action} {rule.protocol} {rule.source} {dest}{port_clause}")
            else:
                commands.append(f"{rule.action} {rule.source}")
        commands.append("exit")

    bridge = get_pt_bridge()
    cli_output = bridge.execute_cli(validated.device, commands)
    return {
        "device": validated.device,
        "acl_identifier": validated.acl_name_or_number,
        "type": "extended" if validated.is_extended else "standard",
        "rule_count": len(validated.rules),
        "status": "configured",
        "cli_output": cli_output
    }


def pt_apply_acl_interface(
    device: str,
    interface: str,
    acl_name: str,
    direction: str
) -> Dict[str, Any]:
    """
    Binds an existing Access Control List to an interface for packet inspection ('in' or 'out').
    """
    validated = ApplyAclInterfaceInput(
        device=device,
        interface=interface,
        acl_name=acl_name,
        direction=direction.lower()
    )

    if validated.direction not in ("in", "out"):
        raise ValueError("ACL direction must be either 'in' or 'out'.")

    commands = [
        f"interface {validated.interface}",
        f"ip access-group {validated.acl_name} {validated.direction}",
        "exit"
    ]

    bridge = get_pt_bridge()
    cli_output = bridge.execute_cli(validated.device, commands)
    return {
        "device": validated.device,
        "interface": validated.interface,
        "acl_name": validated.acl_name,
        "direction": validated.direction,
        "status": "applied",
        "cli_output": cli_output
    }


def pt_configure_nat_overload(
    device: str,
    inside_interface: str,
    outside_interface: str,
    acl_number: int = 1
) -> Dict[str, Any]:
    """
    Configures Dynamic NAT with Port Address Translation (PAT / Overload)
    mapping private addresses behind a single public egress WAN interface.
    """
    validated = ConfigureNatOverloadInput(
        device=device,
        inside_interface=inside_interface,
        outside_interface=outside_interface,
        acl_number=acl_number
    )

    commands = [
        # Inside interface tagging
        f"interface {validated.inside_interface}",
        "ip nat inside",
        "exit",
        # Outside interface tagging
        f"interface {validated.outside_interface}",
        "ip nat outside",
        "exit",
        # Source standard ACL allowing standard RFC1918 traffic
        f"access-list {validated.acl_number} permit 10.0.0.0 0.255.255.255",
        f"access-list {validated.acl_number} permit 172.16.0.0 0.15.255.255",
        f"access-list {validated.acl_number} permit 192.168.0.0 0.0.255.255",
        # NAT Overload binding
        f"ip nat inside source list {validated.acl_number} interface {validated.outside_interface} overload"
    ]

    bridge = get_pt_bridge()
    cli_output = bridge.execute_cli(validated.device, commands)
    return {
        "device": validated.device,
        "inside_interface": validated.inside_interface,
        "outside_interface": validated.outside_interface,
        "acl_number": validated.acl_number,
        "mode": "PAT / Overload",
        "status": "configured",
        "cli_output": cli_output
    }


def pt_configure_asa_interfaces(
    device: str,
    inside_ip: str,
    outside_ip: str
) -> Dict[str, Any]:
    """
    Configures a Cisco ASA 5506-X Security Appliance:
    - GigabitEthernet1/1: Nameif 'inside', Security-Level 100
    - GigabitEthernet1/2: Nameif 'outside', Security-Level 0
    """
    validated = ConfigureAsaInterfacesInput(
        device=device,
        inside_ip=inside_ip,
        outside_ip=outside_ip
    )

    commands = [
        "interface GigabitEthernet1/1",
        "nameif inside",
        "security-level 100",
        f"ip address {validated.inside_ip} {validated.inside_mask}",
        "no shutdown",
        "exit",
        "interface GigabitEthernet1/2",
        "nameif outside",
        "security-level 0",
        f"ip address {validated.outside_ip} {validated.outside_mask}",
        "no shutdown",
        "exit"
    ]

    bridge = get_pt_bridge()
    cli_output = bridge.execute_cli(validated.device, commands)
    return {
        "device": validated.device,
        "inside_interface": {"interface": "GigabitEthernet1/1", "nameif": "inside", "ip": validated.inside_ip, "security_level": 100},
        "outside_interface": {"interface": "GigabitEthernet1/2", "nameif": "outside", "ip": validated.outside_ip, "security_level": 0},
        "status": "configured",
        "cli_output": cli_output
    }


def pt_configure_vpn_ipsec(
    device_a: str,
    device_b: str,
    peer_ip: str,
    pre_shared_key: str = "Cisco123Secure!",
    transform_set: str = "ESP-AES-SHA"
) -> Dict[str, Any]:
    """
    Deploys an industrial-grade Site-to-Site IPsec VPN tunnel between two Cisco IOS routers.
    Builds ISAKMP Phase 1 policy, pre-shared authentication, Phase 2 transform-set, and crypto map.
    """
    validated = ConfigureVpnIpsecInput(
        device_a=device_a,
        device_b=device_b,
        peer_ip=peer_ip,
        pre_shared_key=pre_shared_key,
        transform_set=transform_set
    )

    commands = [
        # Phase 1: ISAKMP Policy
        "crypto isakmp policy 10",
        "encr aes",
        "authentication pre-share",
        "group 2",
        "lifetime 86400",
        "exit",
        f"crypto isakmp key {validated.pre_shared_key} address {validated.peer_ip}",
        # Phase 2: IPsec Transform Set
        f"crypto ipsec transform-set {validated.transform_set} esp-aes esp-sha-hmac",
        # Crypto ACL for VPN traffic
        "access-list 101 permit ip 192.168.1.0 0.0.0.255 192.168.2.0 0.0.0.255",
        # Crypto Map
        "crypto map VPN-MAP 10 ipsec-isakmp",
        f"set peer {validated.peer_ip}",
        f"set transform-set {validated.transform_set}",
        "match address 101",
        "exit"
    ]

    bridge = get_pt_bridge()
    cli_output = bridge.execute_cli(validated.device_a, commands)
    return {
        "initiator": validated.device_a,
        "peer_device": validated.device_b,
        "peer_ip": validated.peer_ip,
        "phase1_policy": 10,
        "transform_set": validated.transform_set,
        "crypto_map": "VPN-MAP 10",
        "status": "configured",
        "cli_output": cli_output
    }

