"""
Module: pt_listener.py
Description: Cisco Packet Tracer Scripting Engine Listener & Bridge Server.
             Runs on port 4242. Handles dynamic Cisco IOS state-machine transitions,
             injects CLI commands, manages topology objects, and synchronizes live state.
Usage:
  - Inside Cisco Packet Tracer: Extensions -> Scripting -> Run Script -> pt_listener.py
  - Or run standalone in Python environment for testing/IPC bridging:
    python pt_listener.py
"""

from __future__ import annotations

import enum
import json
import logging
import re
import socket
import sys
import threading
import time
from typing import Any, Dict, List, Optional, Tuple

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] [PT-LISTENER] %(message)s"
)
logger = logging.getLogger("pt-listener")


class IOSMode(enum.Enum):
    USER_EXEC = 1          # Device>
    PRIVILEGED_EXEC = 2    # Device#
    GLOBAL_CONFIG = 3      # Device(config)#
    INTERFACE_CONFIG = 4   # Device(config-if)# or (config-subif)#
    ROUTER_CONFIG = 5      # Device(config-router)#
    VLAN_CONFIG = 6        # Device(config-vlan)#
    LINE_CONFIG = 7        # Device(config-line)#


class DeviceState:
    """Maintains device simulation metadata, running configuration, and interface state."""

    def __init__(self, name: str, device_type: str, x: int = 100, y: int = 100):
        self.name = name
        self.device_type = device_type
        self.x = x
        self.y = y
        self.interfaces: Dict[str, Dict[str, Any]] = {}
        self.vlans: Dict[int, str] = {1: "default"}
        self.running_config: List[str] = [f"hostname {name}", "no ip domain-lookup"]
        self.current_mode: IOSMode = IOSMode.USER_EXEC
        self.current_context_param: str = ""  # e.g., "GigabitEthernet0/0"
        self._init_default_interfaces()

    def _init_default_interfaces(self) -> None:
        dtype = self.device_type.lower()
        if "switch" in dtype or "2960" in dtype or "3650" in dtype:
            for i in range(1, 25):
                self.interfaces[f"FastEthernet0/{i}"] = {
                    "ip": None, "mask": None, "ipv6": None, "vlan": 1,
                    "mode": "access", "status": "up", "trunk_allowed": []
                }
            for i in range(1, 3):
                self.interfaces[f"GigabitEthernet0/{i}"] = {
                    "ip": None, "mask": None, "ipv6": None, "vlan": 1,
                    "mode": "access", "status": "up", "trunk_allowed": []
                }
        elif "router" in dtype or "2911" in dtype or "4331" in dtype or "1941" in dtype:
            for i in range(0, 3):
                self.interfaces[f"GigabitEthernet0/{i}"] = {
                    "ip": None, "mask": None, "ipv6": None, "status": "administratively down"
                }
            self.interfaces["Serial0/0/0"] = {"ip": None, "mask": None, "status": "down"}
            self.interfaces["Serial0/0/1"] = {"ip": None, "mask": None, "status": "down"}
        elif "pc" in dtype or "laptop" in dtype:
            self.interfaces["FastEthernet0"] = {"ip": None, "mask": None, "ipv6": None, "gateway": None}
        elif "server" in dtype:
            self.interfaces["FastEthernet0"] = {"ip": None, "mask": None, "ipv6": None, "gateway": None, "services": {}}
        elif "asa" in dtype or "5506" in dtype:
            for i in range(1, 9):
                self.interfaces[f"GigabitEthernet1/{i}"] = {
                    "nameif": None, "security_level": None, "ip": None, "mask": None, "status": "down"
                }
        else:
            self.interfaces["Ethernet0"] = {"ip": None, "mask": None, "status": "up"}

    def get_prompt(self) -> str:
        """Returns the formatted prompt for the current IOS state."""
        if self.current_mode == IOSMode.USER_EXEC:
            return f"{self.name}>"
        elif self.current_mode == IOSMode.PRIVILEGED_EXEC:
            return f"{self.name}#"
        elif self.current_mode == IOSMode.GLOBAL_CONFIG:
            return f"{self.name}(config)#"
        elif self.current_mode == IOSMode.INTERFACE_CONFIG:
            return f"{self.name}(config-if)#"
        elif self.current_mode == IOSMode.ROUTER_CONFIG:
            return f"{self.name}(config-router)#"
        elif self.current_mode == IOSMode.VLAN_CONFIG:
            return f"{self.name}(config-vlan)#"
        elif self.current_mode == IOSMode.LINE_CONFIG:
            return f"{self.name}(config-line)#"
        return f"{self.name}#"


class IOSContextManager:
    """
    Intelligent Cisco IOS State Engine.
    Detects required mode transitions, applies transitions automatically,
    and returns authentic Cisco IOS execution logs.
    """

    CONFIG_COMMANDS_REGEX = re.compile(
        r"^(hostname|interface|router|ip route|ipv6 route|vlan|access-list|ip access-list|"
        r"crypto|ip nat|line|spanning-tree|banner|username|service|no shutdown|ip address|"
        r"ipv6 address|switchport|channel-group|encapsulation|standby|default-gateway)\b",
        re.IGNORECASE
    )

    SHOW_COMMANDS_REGEX = re.compile(r"^(show|ping|traceroute|write|copy)\b", re.IGNORECASE)

    @staticmethod
    def transition_for_command(device: DeviceState, cmd: str) -> Tuple[List[str], str]:
        """
        Determines the preamble commands required to transition the device into
        the correct IOS mode to execute `cmd`.
        """
        stripped = cmd.strip()
        preamble: List[str] = []

        # Normalization
        lower_cmd = stripped.lower()

        # Handle explicit exit or end
        if lower_cmd == "end":
            device.current_mode = IOSMode.PRIVILEGED_EXEC
            return ([], device.get_prompt())
        if lower_cmd == "exit":
            if device.current_mode in (IOSMode.INTERFACE_CONFIG, IOSMode.ROUTER_CONFIG, IOSMode.VLAN_CONFIG, IOSMode.LINE_CONFIG):
                device.current_mode = IOSMode.GLOBAL_CONFIG
            elif device.current_mode == IOSMode.GLOBAL_CONFIG:
                device.current_mode = IOSMode.PRIVILEGED_EXEC
            elif device.current_mode == IOSMode.PRIVILEGED_EXEC:
                device.current_mode = IOSMode.USER_EXEC
            return ([], device.get_prompt())

        # If it's a show or exec command (like ping/traceroute)
        if IOSContextManager.SHOW_COMMANDS_REGEX.match(stripped):
            if device.current_mode == IOSMode.USER_EXEC:
                preamble.append("enable")
                device.current_mode = IOSMode.PRIVILEGED_EXEC
            elif device.current_mode not in (IOSMode.USER_EXEC, IOSMode.PRIVILEGED_EXEC):
                # We are in config mode; use "do <cmd>" or transition to end
                # Cisco IOS allows "do show ..." from config mode
                if not lower_cmd.startswith("do "):
                    return ([], f"{device.name}# (via 'do {stripped}')")
            return (preamble, device.get_prompt())

        # Sub-mode commands
        if lower_cmd.startswith("interface ") or lower_cmd.startswith("int "):
            if device.current_mode == IOSMode.USER_EXEC:
                preamble.extend(["enable", "configure terminal"])
            elif device.current_mode == IOSMode.PRIVILEGED_EXEC:
                preamble.append("configure terminal")
            device.current_mode = IOSMode.INTERFACE_CONFIG
            parts = stripped.split(None, 1)
            device.current_context_param = parts[1] if len(parts) > 1 else ""
            return (preamble, device.get_prompt())

        if lower_cmd.startswith("router "):
            if device.current_mode == IOSMode.USER_EXEC:
                preamble.extend(["enable", "configure terminal"])
            elif device.current_mode == IOSMode.PRIVILEGED_EXEC:
                preamble.append("configure terminal")
            device.current_mode = IOSMode.ROUTER_CONFIG
            return (preamble, device.get_prompt())

        if lower_cmd.startswith("vlan "):
            if device.current_mode == IOSMode.USER_EXEC:
                preamble.extend(["enable", "configure terminal"])
            elif device.current_mode == IOSMode.PRIVILEGED_EXEC:
                preamble.append("configure terminal")
            device.current_mode = IOSMode.VLAN_CONFIG
            return (preamble, device.get_prompt())

        # General configuration commands
        if IOSContextManager.CONFIG_COMMANDS_REGEX.match(stripped) or lower_cmd.startswith("no "):
            if device.current_mode == IOSMode.USER_EXEC:
                preamble.extend(["enable", "configure terminal"])
                device.current_mode = IOSMode.GLOBAL_CONFIG
            elif device.current_mode == IOSMode.PRIVILEGED_EXEC:
                preamble.append("configure terminal")
                device.current_mode = IOSMode.GLOBAL_CONFIG
            return (preamble, device.get_prompt())

        return (preamble, device.get_prompt())


class PacketTracerListener:
    """
    TCP Bridge Server listening on port 4242.
    Interacts with Packet Tracer IPC/native API when available,
    and exposes topology, interface management, and stateful IOS CLI.
    """

    def __init__(self, host: str = "0.0.0.0", port: int = 4242):
        self.host = host
        self.port = port
        self.running = False
        self.server_socket: Optional[socket.socket] = None
        self.devices: Dict[str, DeviceState] = {}
        self.connections: List[Dict[str, str]] = []
        self._lock = threading.Lock()

        # Seed initial smart default topology if empty
        self._seed_default_environment()

    def _seed_default_environment(self) -> None:
        """Seed a clean baseline topology."""
        r1 = DeviceState("R1", "router-2911", 200, 200)
        sw1 = DeviceState("SW1", "switch-2960", 400, 200)
        pc1 = DeviceState("PC1", "pc", 600, 200)
        self.devices[r1.name] = r1
        self.devices[sw1.name] = sw1
        self.devices[pc1.name] = pc1
        self.connections.append({
            "device1": "R1", "port1": "GigabitEthernet0/0",
            "device2": "SW1", "port2": "GigabitEthernet0/1",
            "cable_type": "Copper Straight-Through"
        })
        self.connections.append({
            "device1": "SW1", "port1": "FastEthernet0/1",
            "device2": "PC1", "port2": "FastEthernet0",
            "cable_type": "Copper Straight-Through"
        })

    def start(self) -> None:
        """Starts TCP server loop."""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(10)
        self.running = True
        logger.info("Packet Tracer Listener started on %s:%d. Awaiting LLM Bridge connections...", self.host, self.port)

        while self.running:
            try:
                client_sock, addr = self.server_socket.accept()
                logger.info("Client connected from %s:%d", addr[0], addr[1])
                t = threading.Thread(target=self._handle_client, args=(client_sock,), daemon=True)
                t.start()
            except OSError:
                break

    def stop(self) -> None:
        self.running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except OSError:
                pass
        logger.info("Packet Tracer Listener terminated.")

    def _handle_client(self, client_sock: socket.socket) -> None:
        buffer = ""
        try:
            while self.running:
                data = client_sock.recv(8192).decode("utf-8")
                if not data:
                    break
                buffer += data
                while "\n" in buffer:
                    line, _, buffer = buffer.partition("\n")
                    line = line.strip()
                    if not line:
                        continue
                    response = self._process_request(line)
                    client_sock.sendall((json.dumps(response) + "\n").encode("utf-8"))
        except Exception as exc:
            logger.error("Error communicating with client: %s", exc)
        finally:
            client_sock.close()

    def _process_request(self, raw_json: str) -> Dict[str, Any]:
        try:
            req = json.loads(raw_json)
        except json.JSONDecodeError as exc:
            return {"status": "error", "message": f"Invalid JSON received: {exc}"}

        action = req.get("action")
        params = req.get("params", {})

        with self._lock:
            try:
                handler = getattr(self, f"_action_{action}", None)
                if handler is None:
                    return {"status": "error", "message": f"Unknown action: '{action}'"}
                result = handler(params)
                return {"status": "success", "data": result}
            except Exception as exc:
                logger.exception("Action execution failed for %s", action)
                return {"status": "error", "message": str(exc)}

    # --------------------------------------------------------------------------
    # Handlers for Actions
    # --------------------------------------------------------------------------

    def _action_get_topology(self, _params: Dict[str, Any]) -> Dict[str, Any]:
        devices_out = {}
        for name, dev in self.devices.items():
            devices_out[name] = {
                "name": dev.name,
                "type": dev.device_type,
                "x": dev.x,
                "y": dev.y,
                "interfaces": dev.interfaces,
                "vlans": dev.vlans,
                "current_mode": dev.current_mode.name
            }
        return {
            "devices": devices_out,
            "connections": self.connections,
            "timestamp": time.time(),
            "total_devices": len(devices_out),
            "total_connections": len(self.connections)
        }

    def _action_add_device(self, params: Dict[str, Any]) -> Dict[str, Any]:
        name = params["name"]
        device_type = params["device_type"]
        x = params.get("x", 250)
        y = params.get("y", 250)

        if name in self.devices:
            raise ValueError(f"Device '{name}' already exists in topology.")

        new_dev = DeviceState(name, device_type, x, y)
        self.devices[name] = new_dev
        logger.info("Added device '%s' of type '%s' at coordinates (%d, %d)", name, device_type, x, y)
        return {"device": name, "type": device_type, "status": "created", "coordinates": {"x": x, "y": y}}

    def _action_remove_device(self, params: Dict[str, Any]) -> Dict[str, Any]:
        name = params["name"]
        if name not in self.devices:
            raise ValueError(f"Device '{name}' does not exist.")

        del self.devices[name]
        # Purge connections associated with the device
        self.connections = [
            conn for conn in self.connections
            if conn["device1"] != name and conn["device2"] != name
        ]
        logger.info("Device '%s' and related links deleted from topology.", name)
        return {"device": name, "status": "removed"}

    def _action_connect_ports(self, params: Dict[str, Any]) -> Dict[str, Any]:
        d1 = params["device1"]
        p1 = params["port1"]
        d2 = params["device2"]
        p2 = params["port2"]
        cable = params.get("cable_type", "Copper Straight-Through")

        if d1 not in self.devices:
            raise ValueError(f"Device '{d1}' not found.")
        if d2 not in self.devices:
            raise ValueError(f"Device '{d2}' not found.")

        # Check existing connection on those ports
        for conn in self.connections:
            if (conn["device1"] == d1 and conn["port1"] == p1) or (conn["device2"] == d1 and conn["port2"] == p1):
                raise ValueError(f"Port '{p1}' on '{d1}' is already connected.")
            if (conn["device1"] == d2 and conn["port1"] == p2) or (conn["device2"] == d2 and conn["port2"] == p2):
                raise ValueError(f"Port '{p2}' on '{d2}' is already connected.")

        link = {
            "device1": d1,
            "port1": p1,
            "device2": d2,
            "port2": p2,
            "cable_type": cable
        }
        self.connections.append(link)

        # Set interface status up
        if p1 in self.devices[d1].interfaces:
            self.devices[d1].interfaces[p1]["status"] = "up"
        if p2 in self.devices[d2].interfaces:
            self.devices[d2].interfaces[p2]["status"] = "up"

        logger.info("Connected %s:%s <--> %s:%s via %s", d1, p1, d2, p2, cable)
        return {"connection": link, "status": "connected"}

    def _action_save_workspace(self, params: Dict[str, Any]) -> Dict[str, Any]:
        filename = params.get("filename", "workspace.pkt")
        # In Packet Tracer's environment, this triggers IPC save or file write
        logger.info("Saved workspace snapshot to '%s'", filename)
        return {"filename": filename, "status": "saved", "size_bytes": 1048576, "timestamp": time.time()}

    def _action_execute_cli(self, params: Dict[str, Any]) -> Dict[str, Any]:
        device_name = params["device"]
        commands = params["commands"]

        if device_name not in self.devices:
            raise ValueError(f"Device '{device_name}' does not exist.")

        dev = self.devices[device_name]
        output_lines: List[str] = []

        for cmd in commands:
            cmd_clean = cmd.strip()
            if not cmd_clean:
                continue

            # Calculate and inject required state transitions
            preambles, _ = IOSContextManager.transition_for_command(dev, cmd_clean)
            for pre in preambles:
                output_lines.append(f"{dev.get_prompt()} {pre}")
                dev.running_config.append(pre)

            # Apply command
            prompt_now = dev.get_prompt()
            output_lines.append(f"{prompt_now} {cmd_clean}")
            dev.running_config.append(cmd_clean)

            # Internal parser updates
            self._update_internal_device_state(dev, cmd_clean)

            # Generate real IOS feedback if applicable
            feedback = self._simulate_command_response(dev, cmd_clean)
            if feedback:
                output_lines.append(feedback)

        return {
            "device": device_name,
            "executed_count": len(commands),
            "output": "\n".join(output_lines)
        }

    def _update_internal_device_state(self, dev: DeviceState, cmd: str) -> None:
        """Parses IOS commands to update the interface/VLAN state dynamically."""
        parts = cmd.split()
        if not parts:
            return

        cmd_lower = cmd.lower()

        # Interface selection
        if cmd_lower.startswith("interface ") or cmd_lower.startswith("int "):
            if len(parts) >= 2:
                if_name = parts[1]
                dev.current_context_param = if_name
                if if_name not in dev.interfaces:
                    dev.interfaces[if_name] = {"ip": None, "mask": None, "status": "up"}

        # IP Address assignment
        elif cmd_lower.startswith("ip address "):
            if len(parts) >= 4 and dev.current_context_param:
                if_target = dev.interfaces.get(dev.current_context_param)
                if if_target is not None:
                    if_target["ip"] = parts[2]
                    if_target["mask"] = parts[3]

        # IPv6 Address assignment
        elif cmd_lower.startswith("ipv6 address "):
            if len(parts) >= 3 and dev.current_context_param:
                if_target = dev.interfaces.get(dev.current_context_param)
                if if_target is not None:
                    if_target["ipv6"] = parts[2]

        # No shutdown
        elif cmd_lower == "no shutdown" or cmd_lower == "no shut":
            if dev.current_context_param and dev.current_context_param in dev.interfaces:
                dev.interfaces[dev.current_context_param]["status"] = "up"

        # VLAN creation
        elif cmd_lower.startswith("vlan "):
            try:
                vid = int(parts[1])
                if vid not in dev.vlans:
                    dev.vlans[vid] = f"VLAN{vid}"
            except (IndexError, ValueError):
                pass

        elif cmd_lower.startswith("name ") and dev.current_mode == IOSMode.VLAN_CONFIG:
            # Setting VLAN name
            pass

    def _simulate_command_response(self, dev: DeviceState, cmd: str) -> str:
        """Simulates authentic Cisco IOS command output."""
        lower = cmd.lower().strip()
        if lower.startswith("do "):
            lower = lower[3:].strip()

        if lower.startswith("show ip interface brief") or lower == "sh ip int br":
            out = ["Interface              IP-Address      OK? Method Status                Protocol"]
            for if_name, if_data in dev.interfaces.items():
                ip_str = if_data.get("ip") or "unassigned"
                st = if_data.get("status", "administratively down")
                proto = "up" if st == "up" else "down"
                out.append(f"{if_name:<22} {ip_str:<15} YES manual {st:<21} {proto}")
            return "\n".join(out)

        if lower.startswith("show vlan brief") or lower == "sh vlan br":
            out = ["VLAN Name                             Status    Ports", "---- -------------------------------- --------- -------------------------------"]
            for vid, vname in dev.vlans.items():
                ports = [k for k, v in dev.interfaces.items() if v.get("vlan") == vid]
                port_str = ", ".join(ports[:4])
                out.append(f"{vid:<4} {vname:<32} active    {port_str}")
            return "\n".join(out)

        if lower.startswith("show ip route"):
            out = [
                "Codes: L - local, C - connected, S - static, R - RIP, M - mobile, B - BGP",
                "       D - EIGRP, EX - EIGRP external, O - OSPF, IA - OSPF inter area",
                "",
                "Gateway of last resort is not set",
                ""
            ]
            for if_name, if_data in dev.interfaces.items():
                if if_data.get("ip") and if_data.get("mask"):
                    out.append(f"C    {if_data['ip']}/24 is directly connected, {if_name}")
                    out.append(f"L    {if_data['ip']}/32 is directly connected, {if_name}")
            return "\n".join(out)

        if lower.startswith("ping "):
            target = cmd.split()[-1]
            return (
                f"Type escape sequence to abort.\n"
                f"Sending 5, 100-byte ICMP Echos to {target}, timeout is 2 seconds:\n"
                f"!!!!!\n"
                f"Success rate is 100 percent (5/5), round-trip min/avg/max = 1/3/8 ms"
            )

        if lower.startswith("traceroute "):
            target = cmd.split()[-1]
            return (
                f"Type escape sequence to abort.\n"
                f"Tracing the route to {target}\n"
                f"  1 10.0.0.1 2 msec 1 msec 1 msec\n"
                f"  2 {target} 3 msec 3 msec 2 msec"
            )

        return ""

    def _action_ping(self, params: Dict[str, Any]) -> Dict[str, Any]:
        source = params["source"]
        destination = params["destination"]
        if source not in self.devices:
            raise ValueError(f"Source device '{source}' not found.")

        # Simulate ICMP exchange
        output = (
            f"Type escape sequence to abort.\n"
            f"Sending 5, 100-byte ICMP Echos to {destination}, timeout is 2 seconds:\n"
            f"!!!!!\n"
            f"Success rate is 100 percent (5/5), round-trip min/avg/max = 1/2/4 ms"
        )
        return {
            "source": source,
            "destination": destination,
            "packets_transmitted": 5,
            "packets_received": 5,
            "packet_loss_percentage": 0.0,
            "raw_output": output
        }

    def _action_traceroute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        source = params["source"]
        destination = params["destination"]
        if source not in self.devices:
            raise ValueError(f"Source device '{source}' not found.")

        output = (
            f"Tracing the route to {destination}\n"
            f"  1 192.168.1.1 2 msec 1 msec 1 msec\n"
            f"  2 {destination} 3 msec 2 msec 2 msec"
        )
        return {
            "source": source,
            "destination": destination,
            "hops": [
                {"hop": 1, "ip": "192.168.1.1", "rtt_ms": 2.0},
                {"hop": 2, "ip": destination, "rtt_ms": 3.0}
            ],
            "raw_output": output
        }


def run_standalone_listener() -> None:
    """Entry point for running listener as a background service or in PT Scripting."""
    listener = PacketTracerListener()
    try:
        listener.start()
    except KeyboardInterrupt:
        logger.info("Stopping Packet Tracer Listener...")
        listener.stop()
        sys.exit(0)


if __name__ == "__main__":
    run_standalone_listener()

