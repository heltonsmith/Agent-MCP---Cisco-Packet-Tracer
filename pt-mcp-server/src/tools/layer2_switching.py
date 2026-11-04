"""
Module: layer2_switching.py
Description: Production Layer 2 switching automation for Cisco Packet Tracer.
             Handles VLANs, 802.1Q Trunks, Access Port assignments, Spanning Tree (STP),
             and LACP/PAgP EtherChannel port bundling.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from src.bridge.pt_client import get_pt_bridge


# -----------------------------------------------------------------------------
# Pydantic Input Schemas
# -----------------------------------------------------------------------------

class CreateVlanInput(BaseModel):
    device: str = Field(..., description="Target switch hostname (e.g. 'SW1').")
    vlan_id: int = Field(..., ge=1, le=4094, description="VLAN Identifier between 1 and 4094.")
    vlan_name: str = Field(..., description="Descriptive name for the VLAN (e.g. 'ENGINEERING').")


class AssignAccessPortInput(BaseModel):
    device: str = Field(..., description="Target switch hostname.")
    interface: str = Field(..., description="Switch interface name (e.g. 'FastEthernet0/1').")
    vlan_id: int = Field(..., ge=1, le=4094, description="VLAN ID to map as untagged access.")


class ConfigureTrunkInput(BaseModel):
    device: str = Field(..., description="Target switch hostname.")
    interface: str = Field(..., description="Switch interface or Port-Channel (e.g. 'GigabitEthernet0/1').")
    allowed_vlans: Optional[List[int]] = Field(
        default=None,
        description="List of VLAN IDs allowed across the trunk. If omitted or empty, all VLANs (1-4094) are permitted."
    )


class ConfigureStpInput(BaseModel):
    device: str = Field(..., description="Target switch hostname.")
    vlan_id: int = Field(..., ge=1, le=4094, description="Target VLAN ID for STP instance (PVST+/Rapid-PVST).")
    priority: int = Field(
        ...,
        ge=0,
        le=61440,
        description="STP Bridge Priority. Must be a multiple of 4096 (e.g. 0, 4096, 8192, ..., 32768)."
    )


class ConfigureEtherchannelInput(BaseModel):
    device: str = Field(..., description="Target switch hostname.")
    interfaces: List[str] = Field(..., min_length=2, max_length=8, description="List of physical member ports (e.g. ['FastEthernet0/1', 'FastEthernet0/2']).")
    group_id: int = Field(..., ge=1, le=255, description="Channel group number (1-255).")
    protocol: str = Field(
        default="LACP",
        description="Link bundling protocol. Options: 'LACP' (mode active), 'PAGP' (mode desirable), 'STATIC' (mode on)."
    )


# -----------------------------------------------------------------------------
# Tool Implementations
# -----------------------------------------------------------------------------

def pt_create_vlan(device: str, vlan_id: int, vlan_name: str) -> Dict[str, Any]:
    """
    Creates an 802.1Q VLAN on a Cisco switch and sets its administrative name.
    """
    validated = CreateVlanInput(device=device, vlan_id=vlan_id, vlan_name=vlan_name)
    commands = [
        f"vlan {validated.vlan_id}",
        f"name {validated.vlan_name}",
        "exit"
    ]
    bridge = get_pt_bridge()
    cli_output = bridge.execute_cli(validated.device, commands)
    return {
        "device": validated.device,
        "vlan_id": validated.vlan_id,
        "vlan_name": validated.vlan_name,
        "status": "configured",
        "cli_output": cli_output
    }


def pt_assign_access_port(device: str, interface: str, vlan_id: int) -> Dict[str, Any]:
    """
    Configures an interface as a Layer 2 access switchport in a specific VLAN and enables it.
    """
    validated = AssignAccessPortInput(device=device, interface=interface, vlan_id=vlan_id)
    commands = [
        f"interface {validated.interface}",
        "switchport mode access",
        f"switchport access vlan {validated.vlan_id}",
        "spanning-tree portfast",
        "no shutdown",
        "exit"
    ]
    bridge = get_pt_bridge()
    cli_output = bridge.execute_cli(validated.device, commands)
    return {
        "device": validated.device,
        "interface": validated.interface,
        "vlan_id": validated.vlan_id,
        "mode": "access",
        "status": "configured",
        "cli_output": cli_output
    }


def pt_configure_trunk(device: str, interface: str, allowed_vlans: Optional[List[int]] = None) -> Dict[str, Any]:
    """
    Configures an interface as an 802.1Q trunk port with optional allowed VLAN pruning.
    """
    validated = ConfigureTrunkInput(device=device, interface=interface, allowed_vlans=allowed_vlans)
    commands = [
        f"interface {validated.interface}",
        # Some Cisco switches require encapsulation command prior to trunking
        "switchport trunk encapsulation dot1q",
        "switchport mode trunk"
    ]
    if validated.allowed_vlans:
        vlan_str = ",".join(str(v) for v in sorted(validated.allowed_vlans))
        commands.append(f"switchport trunk allowed vlan {vlan_str}")
    else:
        commands.append("switchport trunk allowed vlan all")

    commands.extend(["no shutdown", "exit"])

    bridge = get_pt_bridge()
    cli_output = bridge.execute_cli(validated.device, commands)
    return {
        "device": validated.device,
        "interface": validated.interface,
        "mode": "trunk",
        "allowed_vlans": validated.allowed_vlans or "all",
        "status": "configured",
        "cli_output": cli_output
    }


def pt_configure_stp(device: str, vlan_id: int, priority: int) -> Dict[str, Any]:
    """
    Adjusts the Spanning Tree Protocol (STP) root bridge priority for a given VLAN.
    Priority must be a multiple of 4096 (0, 4096, 8192, 16384, 32768, etc.).
    """
    validated = ConfigureStpInput(device=device, vlan_id=vlan_id, priority=priority)

    # Normalize priority to closest multiple of 4096 if needed
    normalized_priority = (validated.priority // 4096) * 4096

    commands = [
        f"spanning-tree vlan {validated.vlan_id} priority {normalized_priority}",
        "exit"
    ]
    bridge = get_pt_bridge()
    cli_output = bridge.execute_cli(validated.device, commands)
    return {
        "device": validated.device,
        "vlan_id": validated.vlan_id,
        "priority_configured": normalized_priority,
        "status": "configured",
        "cli_output": cli_output
    }


def pt_configure_etherchannel(
    device: str,
    interfaces: List[str],
    group_id: int,
    protocol: str = "LACP"
) -> Dict[str, Any]:
    """
    Bundles multiple physical Ethernet interfaces into a Port-Channel using LACP, PAgP, or Static.
    """
    validated = ConfigureEtherchannelInput(
        device=device,
        interfaces=interfaces,
        group_id=group_id,
        protocol=protocol
    )

    proto_upper = validated.protocol.upper()
    if proto_upper == "LACP":
        mode_keyword = "active"
    elif proto_upper == "PAGP":
        mode_keyword = "desirable"
    else:
        mode_keyword = "on"

    commands = []
    for iface in validated.interfaces:
        commands.extend([
            f"interface {iface}",
            f"channel-group {validated.group_id} mode {mode_keyword}",
            "no shutdown",
            "exit"
        ])

    commands.extend([
        f"interface Port-channel {validated.group_id}",
        "no shutdown",
        "exit"
    ])

    bridge = get_pt_bridge()
    cli_output = bridge.execute_cli(validated.device, commands)
    return {
        "device": validated.device,
        "group_id": validated.group_id,
        "protocol": proto_upper,
        "bundled_interfaces": validated.interfaces,
        "port_channel": f"Port-channel {validated.group_id}",
        "status": "configured",
        "cli_output": cli_output
    }

