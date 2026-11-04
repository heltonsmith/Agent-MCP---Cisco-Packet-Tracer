"""
Module: diagnostics.py
Description: Real-time network telemetry, connectivity verification, path tracing,
             and Cisco IOS diagnostic inspection commands (show ip route, show run, etc.).
"""

from __future__ import annotations

from typing import Any, Dict
from pydantic import BaseModel, Field

from src.bridge.pt_client import get_pt_bridge


# -----------------------------------------------------------------------------
# Pydantic Input Schemas
# -----------------------------------------------------------------------------

class PingInput(BaseModel):
    source: str = Field(..., description="Hostname of initiating device (e.g. 'PC1' or 'R1').")
    destination: str = Field(..., description="Target IPv4 or IPv6 destination address or hostname (e.g. '192.168.1.1').")


class TracerouteInput(BaseModel):
    source: str = Field(..., description="Hostname of the source device (e.g. 'PC1' or 'R1').")
    destination: str = Field(..., description="Destination IPv4 or IPv6 address (e.g. '8.8.8.8').")


class ShowCommandInput(BaseModel):
    device: str = Field(..., description="Target Cisco device hostname (e.g. 'R1' or 'SW1').")
    command: str = Field(
        ...,
        description="Cisco IOS show command (e.g. 'show ip interface brief', 'show ip route', 'show running-config', 'show vlan brief', 'show cdp neighbors', 'show ip ospf neighbor')."
    )


# -----------------------------------------------------------------------------
# Tool Implementations
# -----------------------------------------------------------------------------

def pt_ping(source: str, destination: str) -> Dict[str, Any]:
    """
    Executes a real-time ICMP Echo Request test from a source device towards a destination IP.
    Returns transmission statistics and live IOS ping output.
    """
    validated = PingInput(source=source, destination=destination)
    bridge = get_pt_bridge()
    return bridge.send_command("ping", validated.model_dump())


def pt_traceroute(source: str, destination: str) -> Dict[str, Any]:
    """
    Performs layer-3 path discovery to trace hop-by-hop latency and intermediate gateways
    between source and destination.
    """
    validated = TracerouteInput(source=source, destination=destination)
    bridge = get_pt_bridge()
    return bridge.send_command("traceroute", validated.model_dump())


def pt_show_command(device: str, command: str) -> Dict[str, Any]:
    """
    Wildcard diagnostic tool: Executes any Cisco IOS show / verification command
    (e.g., 'show ip route', 'show running-config', 'show ip int brief', 'show vlan brief')
    and returns full verbatim output.
    """
    validated = ShowCommandInput(device=device, command=command)
    cmd = validated.command.strip()
    if not (cmd.lower().startswith("show") or cmd.lower().startswith("sh") or cmd.lower().startswith("do ")):
        cmd = f"show {cmd}"

    bridge = get_pt_bridge()
    cli_output = bridge.execute_cli(validated.device, [cmd])
    return {
        "device": validated.device,
        "command": cmd,
        "output": cli_output
    }

