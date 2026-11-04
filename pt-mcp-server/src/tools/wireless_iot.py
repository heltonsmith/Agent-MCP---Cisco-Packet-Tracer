"""
Module: wireless_iot.py
Description: Wireless LAN (WLAN) and Internet of Things (IoT) provisioning in Cisco Packet Tracer.
             Controls Access Points, Home Gateways, WRT300N routers, smart sensors,
             wireless client associations, and IoT Registration Server binding.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

from src.bridge.pt_client import get_pt_bridge


# -----------------------------------------------------------------------------
# Pydantic Input Schemas
# -----------------------------------------------------------------------------

class ConfigureWirelessRouterInput(BaseModel):
    device: str = Field(..., description="Wireless Gateway/Router hostname (e.g. 'WRT300N' or 'HomeGateway').")
    ssid: str = Field(..., description="Service Set Identifier (Wi-Fi network broadcast name).")
    auth_type: str = Field(
        default="WPA2-PSK",
        description="Wireless authentication mechanism. Defaults to 'WPA2-PSK'. Options: 'WPA2-PSK', 'WPA3-SAE', 'Open'."
    )
    password: str = Field(..., min_length=8, description="WPA pre-shared key passphrase (minimum 8 characters).")
    channel: int = Field(default=6, ge=1, le=11, description="2.4 GHz RF Channel (1, 6, or 11 recommended).")


class AddIotSensorInput(BaseModel):
    sensor_type: str = Field(
        ...,
        description="IoT appliance type (e.g., 'Motion Detector', 'Temperature Monitor', 'Smoke Detector', 'Smart Door', 'Siren', 'Solar Panel')."
    )
    name: str = Field(..., description="Descriptive identifier for the sensor (e.g., 'TEMP_ZONE_1').")
    x: int = Field(default=350, description="X coordinate on workspace canvas.")
    y: int = Field(default=350, description="Y coordinate on workspace canvas.")


class ConnectWirelessClientInput(BaseModel):
    client_name: str = Field(..., description="Wireless client station name (e.g. 'Laptop1', 'Smartphone1', 'IoT_Sensor1').")
    ssid: str = Field(..., description="Target SSID to associate with.")
    password: str = Field(..., description="Pre-shared key / passphrase for authentication.")


class RegisterIotDeviceInput(BaseModel):
    device_name: str = Field(..., description="Name of the IoT sensor or actuator (e.g. 'TEMP_ZONE_1').")
    server_ip: str = Field(..., description="IPv4 address of the Cisco Packet Tracer IoT Registration Server.")
    username: str = Field(default="admin", description="IoT Server account username.")
    password: str = Field(default="admin", description="IoT Server account password.")


# -----------------------------------------------------------------------------
# Tool Implementations
# -----------------------------------------------------------------------------

def pt_configure_wireless_router(
    device: str,
    ssid: str,
    auth_type: str = "WPA2-PSK",
    password: str = "SecretWifi123",
    channel: int = 6
) -> Dict[str, Any]:
    """
    Configures SSID, 2.4GHz RF channel, and WPA2-Personal security on a wireless router/access point.
    """
    validated = ConfigureWirelessRouterInput(
        device=device,
        ssid=ssid,
        auth_type=auth_type,
        password=password,
        channel=channel
    )

    bridge = get_pt_bridge()
    result = bridge.send_command("configure_wireless_router", validated.model_dump())
    return {
        "device": validated.device,
        "ssid": validated.ssid,
        "channel": validated.channel,
        "auth_type": validated.auth_type,
        "status": "configured",
        "details": result
    }


def pt_add_iot_sensor(sensor_type: str, name: str, x: int = 350, y: int = 350) -> Dict[str, Any]:
    """
    Spawns an IoT environmental sensor, detector, or actuator into the Packet Tracer workspace.
    """
    validated = AddIotSensorInput(sensor_type=sensor_type, name=name, x=x, y=y)
    bridge = get_pt_bridge()
    return bridge.send_command("add_device", {
        "name": validated.name,
        "device_type": f"iot-{validated.sensor_type.lower().replace(' ', '-')}",
        "x": validated.x,
        "y": validated.y
    })


def pt_connect_wireless_client(client_name: str, ssid: str, password: str) -> Dict[str, Any]:
    """
    Associates an endpoint (Laptop, Smartphone, Tablet, or IoT thing) to a target Wi-Fi SSID
    with WPA/WPA2 pre-shared key credentials.
    """
    validated = ConnectWirelessClientInput(client_name=client_name, ssid=ssid, password=password)
    bridge = get_pt_bridge()
    result = bridge.send_command("connect_wireless_client", validated.model_dump())
    return {
        "client": validated.client_name,
        "associated_ssid": validated.ssid,
        "status": "associated",
        "details": result
    }


def pt_register_iot_device(
    device_name: str,
    server_ip: str,
    username: str = "admin",
    password: str = "admin"
) -> Dict[str, Any]:
    """
    Registers an IoT device to a centralized Cisco Packet Tracer Registration Server
    for cloud/web dashboard remote telemetry and automation rules.
    """
    validated = RegisterIotDeviceInput(
        device_name=device_name,
        server_ip=server_ip,
        username=username,
        password=password
    )
    bridge = get_pt_bridge()
    result = bridge.send_command("register_iot_device", validated.model_dump())
    return {
        "device": validated.device_name,
        "iot_server": validated.server_ip,
        "account": validated.username,
        "registration_status": "registered",
        "details": result
    }

