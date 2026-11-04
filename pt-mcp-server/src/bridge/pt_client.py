"""
Module: pt_client.py
Description: High-performance TCP client bridge to communicate with Cisco Packet Tracer's
             internal scripting runtime via structured JSON-RPC over TCP sockets.
"""

from __future__ import annotations

import json
import logging
import socket
import threading
from typing import Any, Dict, List, Optional

logger = logging.getLogger("pt-mcp.client")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] [PT-CLIENT] %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


class PacketTracerBridgeError(Exception):
    """Raised when communication with the Packet Tracer listener fails or returns an error."""
    pass


class PacketTracerBridge:
    """
    Thread-safe TCP client that connects to the Packet Tracer internal listener
    running on port 4242. Serializes requests and deserializes responses using
    newline-delimited JSON.
    """

    _instance: Optional[PacketTracerBridge] = None
    _lock = threading.Lock()

    def __init__(self, host: str = "127.0.0.1", port: int = 4242, timeout: float = 15.0):
        self.host = host
        self.port = port
        self.timeout = timeout
        self._socket: Optional[socket.socket] = None
        self._io_lock = threading.Lock()

    @classmethod
    def get_instance(cls, host: str = "127.0.0.1", port: int = 4242) -> PacketTracerBridge:
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls(host=host, port=port)
            return cls._instance

    def connect(self) -> None:
        """Establishes or verifies an active TCP socket connection to PT Listener."""
        if self._socket is not None:
            return

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            sock.connect((self.host, self.port))
            self._socket = sock
            logger.info("Connected successfully to Cisco Packet Tracer Listener at %s:%d", self.host, self.port)
        except (ConnectionRefusedError, socket.timeout, OSError) as exc:
            self._socket = None
            error_msg = (
                f"Failed to connect to Cisco Packet Tracer Listener at {self.host}:{self.port}. "
                "Ensure that Cisco Packet Tracer is running and the 'pt_listener.py' script "
                "is executed in Extensions -> Scripting (or running as background IPC listener). "
                f"Underlying error: {exc}"
            )
            logger.error(error_msg)
            raise PacketTracerBridgeError(error_msg) from exc

    def disconnect(self) -> None:
        """Safely closes the TCP socket connection."""
        with self._io_lock:
            if self._socket is not None:
                try:
                    self._socket.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass
                finally:
                    self._socket.close()
                    self._socket = None
                    logger.info("Disconnected from Cisco Packet Tracer Listener.")

    def send_command(self, action: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Sends an action payload with parameters to Packet Tracer and awaits response.

        Format:
            Request:  {"action": action, "params": params}\n
            Response: {"status": "success"|"error", "data": ..., "message": ...}\n
        """
        if params is None:
            params = {}

        payload = {
            "action": action,
            "params": params
        }

        serialized = json.dumps(payload) + "\n"

        with self._io_lock:
            # Reconnect if needed
            if self._socket is None:
                self.connect()

            assert self._socket is not None

            try:
                self._socket.sendall(serialized.encode("utf-8"))
            except (BrokenPipeError, ConnectionResetError, OSError) as exc:
                logger.warning("Socket disconnected during send. Attempting one reconnect...")
                self.disconnect()
                self.connect()
                assert self._socket is not None
                self._socket.sendall(serialized.encode("utf-8"))

            # Receive buffer until newline delimiter
            buffer = ""
            while True:
                try:
                    chunk = self._socket.recv(8192).decode("utf-8")
                except socket.timeout as exc:
                    self.disconnect()
                    raise PacketTracerBridgeError(f"Timeout waiting for response from Packet Tracer on action '{action}'.") from exc
                except OSError as exc:
                    self.disconnect()
                    raise PacketTracerBridgeError(f"Socket read error during action '{action}': {exc}") from exc

                if not chunk:
                    self.disconnect()
                    raise PacketTracerBridgeError("Connection closed unexpectedly by Packet Tracer Listener.")

                buffer += chunk
                if "\n" in buffer:
                    line, _, _ = buffer.partition("\n")
                    break

            try:
                response = json.loads(line.strip())
            except json.JSONDecodeError as exc:
                raise PacketTracerBridgeError(f"Malformed JSON response from Packet Tracer: {line}") from exc

            if response.get("status") == "error":
                err_msg = response.get("message", "Unknown error in Packet Tracer execution.")
                logger.error("Error reported by PT Listener for action %s: %s", action, err_msg)
                raise PacketTracerBridgeError(f"Packet Tracer Error: {err_msg}")

            return response.get("data", {})

    def execute_cli(self, device: str, commands: List[str]) -> str:
        """
        Convenience method to execute a list of Cisco IOS CLI commands on a device.
        The listener automatically handles privilege transitions and prompt synchronization.
        """
        result = self.send_command("execute_cli", {
            "device": device,
            "commands": commands
        })
        if isinstance(result, dict) and "output" in result:
            return str(result["output"])
        return str(result)

    def get_topology(self) -> Dict[str, Any]:
        """
        Convenience method to fetch the current workspace topology.
        """
        return self.send_command("get_topology", {})


def get_pt_bridge() -> PacketTracerBridge:
    """Helper function to retrieve singleton instance of PacketTracerBridge."""
    return PacketTracerBridge.get_instance()

