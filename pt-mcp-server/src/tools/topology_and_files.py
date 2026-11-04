"""
Module: topology_and_files.py
Description: Tools for workspace topology awareness, device lifecycle, physical cabling,
             and workspace file persistence (.pkt).
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

from src.bridge.pt_client import get_pt_bridge


# -----------------------------------------------------------------------------
# Pydantic Input Schemas
# -----------------------------------------------------------------------------

class AddDeviceInput(BaseModel):
    device_type: str = Field(
        ...,
        description="Hardware model or type (e.g., '2911', 'ISR4331', '2960-24TT', 'PC', 'Server', 'ASA-5506-X')."
    )
    name: str = Field(..., description="Unique hostname or identifier for the device in the workspace.")
    x: int = Field(default=200, description="X coordinate on the Packet Tracer logical workspace canvas.")
    y: int = Field(default=200, description="Y coordinate on the Packet Tracer logical workspace canvas.")


class ConnectPortsInput(BaseModel):
    device1: str = Field(..., description="Name of the source device (e.g. 'R1').")
    port1: str = Field(..., description="Source interface (e.g. 'GigabitEthernet0/0').")
    device2: str = Field(..., description="Name of the destination device (e.g. 'SW1').")
    port2: str = Field(..., description="Destination interface (e.g. 'GigabitEthernet0/1').")
    cable_type: str = Field(
        default="Copper Straight-Through",
        description="Physical cable medium. Defaults to 'Copper Straight-Through'. Options: 'Copper Straight-Through', 'Copper Cross-Over', 'Fiber', 'Serial DTE'."
    )


class RemoveDeviceInput(BaseModel):
    name: str = Field(..., description="Name of the device to be removed from the canvas.")


class SaveWorkspaceInput(BaseModel):
    filename: str = Field(
        default="topology_backup.pkt",
        description="Path or filename where the Cisco Packet Tracer state (.pkt) will be saved."
    )


# -----------------------------------------------------------------------------
# Tool Implementations
# -----------------------------------------------------------------------------

def pt_get_topology() -> Dict[str, Any]:
    """
    [CRITICAL FOR REASONING] Reads and inspects the live Packet Tracer workspace.
    Returns a structured JSON document listing every device, its hardware model,
    operational coordinates, all interfaces with assigned IP/IPv6 and VLAN tags,
    and a complete graph of active physical cable connections.
    """
    bridge = get_pt_bridge()
    return bridge.send_command("get_topology", {})


def pt_add_device(device_type: str, name: str, x: int = 200, y: int = 200) -> Dict[str, Any]:
    """
    Deploys a new network appliance (Router, Switch, Server, PC, ASA) onto the
    logical workspace canvas at the specified (x, y) coordinates.
    """
    validated = AddDeviceInput(device_type=device_type, name=name, x=x, y=y)
    bridge = get_pt_bridge()
    return bridge.send_command("add_device", validated.model_dump())


def pt_connect_ports(
    device1: str,
    port1: str,
    device2: str,
    port2: str,
    cable_type: str = "Copper Straight-Through"
) -> Dict[str, Any]:
    """
    Patches a physical cable link between two device interfaces on the workspace.
    Applies 'Copper Straight-Through' as the smart default.
    """
    validated = ConnectPortsInput(
        device1=device1,
        port1=port1,
        device2=device2,
        port2=port2,
        cable_type=cable_type
    )
    bridge = get_pt_bridge()
    return bridge.send_command("connect_ports", validated.model_dump())


def pt_remove_device(name: str) -> Dict[str, Any]:
    """
    Permanently deletes a device and teardown all its connected physical cabling
    from the Packet Tracer canvas.
    """
    validated = RemoveDeviceInput(name=name)
    bridge = get_pt_bridge()
    return bridge.send_command("remove_device", validated.model_dump())


def pt_save_workspace(filename: str = "topology_backup.pkt") -> Dict[str, Any]:
    """
    Serializes and commits the current live network topology, device states,
    and configurations into a persistent .pkt file on disk.
    """
    validated = SaveWorkspaceInput(filename=filename)
    bridge = get_pt_bridge()
    return bridge.send_command("save_workspace", validated.model_dump())

