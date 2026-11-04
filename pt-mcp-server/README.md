# Cisco Packet Tracer MCP Server (Model Context Protocol)

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![MCP Official SDK](https://img.shields.io/badge/MCP-Official%20SDK-purple.svg)](https://modelcontextprotocol.io/)
[![Cisco IOS & Packet Tracer](https://img.shields.io/badge/Cisco-Packet%20Tracer%208.x-005073.svg)](https://www.netacad.com/courses/packet-tracer)

Servidor de grado industrial basado en el estándar **Model Context Protocol (MCP)** que dota a Modelos de Lenguaje Grande (LLMs como Claude 3.5 Sonnet, Gemini 1.5/2.0 Pro, GPT-4o) de la capacidad de interactuar, inspeccionar y manipular topologías de red en tiempo real sobre la interfaz gráfica de **Cisco Packet Tracer**.

---

## 🏛️ Arquitectura del Sistema

```
┌─────────────────────────────────┐
│     LLM (Claude / Gemini / etc) │
└────────────────┬────────────────┘
                 │ JSON-RPC vía stdio
┌────────────────▼────────────────┐
│      MCP Server (main.py)       │
│  24 Herramientas Especializadas │
└────────────────┬────────────────┘
                 │ TCP Socket (puerto 4242) / Framing Newline-JSON
┌────────────────▼────────────────┐
│   pt_client.py (Bridge Client)  │
└────────────────┬────────────────┘
                 │ Red Local / Loopback
┌────────────────▼────────────────┐
│  pt_listener.py (Bridge Server) │
│   - Autómata de Estados IOS FSM │
│   - Inyector CLI & Topology API │
└────────────────┬────────────────┘
                 │ Acceso Interno / IPC
┌────────────────▼────────────────┐
│   Cisco Packet Tracer (GUI)     │
│   Canvas, Routers, Switches,    │
│   ASA, IoT, Enlaces Físicos     │
└─────────────────────────────────┘
```

El sistema opera mediante una arquitectura cliente-servidor desacoplada:
1. **MCP Server (`src/main.py`):** Expone 24 herramientas tipadas y validadas con Pydantic v2 al LLM mediante el SDK oficial de MCP.
2. **Bridge Client (`src/bridge/pt_client.py`):** Serializa las peticiones a tramas JSON delimitadas por salto de línea (`\n`) y gestiona reconexiones automáticas contra el listener de Packet Tracer.
3. **PT Listener (`src/bridge/pt_listener.py`):** Se ejecuta en el entorno de scripting de Cisco Packet Tracer o como un daemon de IPC en el puerto 4242. Contiene una **Máquina de Estados Finitos (FSM) de Cisco IOS** que detecta transiciones de contexto (e.g. `User EXEC` ➡️ `Privileged EXEC` ➡️ `Global Config` ➡️ `Interface Config`) e inyecta los comandos necesarios (`enable`, `configure terminal`, etc.) de forma transparente.

---

## 📂 Estructura del Proyecto

```text
pt-mcp-server/
├── pyproject.toml
├── README.md
├── src/
│   ├── main.py
│   ├── bridge/
│   │   ├── pt_client.py 
│   │   └── pt_listener.py 
│   └── tools/
│       ├── topology_and_files.py
│       ├── layer2_switching.py
│       ├── layer3_routing.py
│       ├── security_firewalls.py
│       ├── wireless_iot.py
│       └── diagnostics.py
```

---

## 🚀 Instalación y Puesta en Marcha

### 1. Requisitos Previos
- Python 3.10 o superior.
- Cisco Packet Tracer 8.0, 8.1 o 8.2+.

### 2. Instalación de Dependencias
En la carpeta raíz del proyecto (`pt-mcp-server/`):
```bash
pip install -e .
```
O manualmente:
```bash
pip install "mcp>=1.0.0" "pydantic>=2.0.0" "typing-extensions>=4.8.0"
```

### 3. Iniciar el Servidor Bridge (`pt_listener.py`) antes de conectar con Packet Tracer

> ⚠️ **REQUISITO OBLIGATORIO Y CRÍTICO (ORDEN DE EJECUCIÓN):**  
> **El servidor listener DEBE estar iniciado y escuchando en la terminal ANTES de conectar o ejecutar el script en Cisco Packet Tracer.**  
> Si se intenta conectar desde Packet Tracer sin haber levantado este proceso, la conexión será rechazada (*Connection Refused*) porque no habrá ningún servicio escuchando en el puerto TCP `4242`.

#### Paso A: Lanzar el Servidor Bridge en Terminal
Abre una ventana de terminal (PowerShell o CMD) y ejecuta:
```cmd
cd pt-mcp-server\src\bridge
python pt_listener.py
```
O directamente desde la ruta:
```cmd
pt-mcp-server\src\bridge>python pt_listener.py
```
Verás la confirmación de inicio:
```text
[PT-LISTENER] Packet Tracer Listener started on 0.0.0.0:4242. Awaiting LLM Bridge connections...
```
*(Deja esta terminal corriendo en segundo plano).*

#### Paso B: Conectar el Script en Cisco Packet Tracer
Una vez que el listener está activo en el puerto 4242:
1. Abre **Cisco Packet Tracer**.
2. Ve al menú superior: **Extensions** ➡️ **Scripting** ➡️ **Script Manager** (o *Configure PT Script Modules...*).
3. Carga y ejecuta el script del bridge (`pt_listener.py` o módulo de extensión).
4. El script se conectará de inmediato al socket local `127.0.0.1:4242` sin errores y reflejará todas las acciones del LLM en la pantalla de Packet Tracer en vivo.

---

## ⚙️ Configuración en Clientes LLM

### 1. Antigravity IDE / Antigravity CLI (`mcp_config.json`)
En `~/.gemini/config/mcp_config.json`:
```json
{
  "mcpServers": {
    "cisco-packet-tracer": {
      "command": "python",
      "args": [
        "C:\\Users\\Usuario\\Desktop\\MCP Server CKEIMY\\pt-mcp-server\\src\\main.py"
      ],
      "cwd": "C:\\Users\\Usuario\\Desktop\\MCP Server CKEIMY\\pt-mcp-server"
    }
  }
}
```

### 2. ChatGPT Codex / OpenAI Desktop MCP
En tu archivo de configuración de ChatGPT Desktop o perfil de Codex CLI (`mcp_config.json`):
```json
{
  "mcpServers": {
    "cisco-packet-tracer": {
      "command": "python",
      "args": [
        "C:\\Users\\Usuario\\Desktop\\MCP Server CKEIMY\\pt-mcp-server\\src\\main.py"
      ],
      "cwd": "C:\\Users\\Usuario\\Desktop\\MCP Server CKEIMY\\pt-mcp-server"
    }
  }
}
```
O registrando el servidor vía CLI de Codex:
```bash
codex mcp add cisco-packet-tracer -- python C:\Users\Usuario\Desktop\MCP Server CKEIMY\pt-mcp-server\src\main.py
```

### 3. Claude Desktop (`claude_desktop_config.json`)
En Windows (`%APPDATA%\Claude\claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "cisco-packet-tracer": {
      "command": "python",
      "args": [
        "-m",
        "src.main"
      ],
      "cwd": "C:\\Users\\Usuario\\Desktop\\MCP Server CKEIMY\\pt-mcp-server"
    }
  }
}
```

---

## 🛠️ Desglose Técnico: ¿Para qué se utiliza cada Comando y Script?

- **`install.bat`**: Script de automatización de Windows que actualiza `pip`, instala las dependencias de `requirements.txt` y ejecuta `setup_project.py` para generar la configuración personalizada en un solo clic.
- **`install.sh`**: Script para Linux, macOS y WSL que valida el intérprete Python y despliega las librerías necesarias.
- **`pip install -r requirements.txt` (o `pip install mcp pydantic`)**: Descarga e instala el SDK oficial `mcp` para transporte JSON-RPC y `pydantic` para validación de contratos tipados de red.
- **`python setup_project.py`**: Utilidad interactiva que inspecciona tu computadora, resuelve las rutas absolutas del proyecto y emite las configuraciones listas para copiar en Antigravity, ChatGPT Codex, Claude o Cursor.
- **`pt-mcp-server\src\bridge> python pt_listener.py`**: **Comando obligatorio.** Inicia el servidor de sockets TCP en el puerto `4242` que emula el autómata de estados de Cisco IOS. Debe levantarse **antes** de conectar el script en Cisco Packet Tracer.
- **`python src/main.py` (o `python run_server.py`)**: Proceso servidor MCP ejecutado por el LLM en segundo plano mediante `stdio`, que expone las 24 herramientas de automatización de red.
- **`test_quickstart.py`**: Script de diagnóstico para validar en 5 segundos que el socket bridge, la máquina de estados IOS y los comandos `show` / `ping` funcionan antes de conectar el agente de IA.

---

---

## 🛠️ Catálogo Exhaustivo de Herramientas (24 Tools)

### 1. Topology & Workspace Management (`tools/topology_and_files.py`)
- **`pt_get_topology()`**: **[CRÍTICO]** Permite al LLM "ver" el espacio de trabajo. Retorna un snapshot JSON con todos los dispositivos, modelos, coordenadas (x, y), interfaces (IP, máscara, IPv6, VLAN, status) y enlaces físicos cableados.
- **`pt_add_device(device_type, name, x=200, y=200)`**: Coloca un router, switch, PC, servidor o firewall ASA en las coordenadas especificadas.
- **`pt_connect_ports(device1, port1, device2, port2, cable_type="Copper Straight-Through")`**: Parchea un cable físico entre dos puertos (aplica cables directos por defecto).
- **`pt_remove_device(name)`**: Elimina el dispositivo y desconecta todos sus enlaces físicos.
- **`pt_save_workspace(filename="topology_backup.pkt")`**: Guarda el estado actual en un archivo `.pkt`.

### 2. Layer 2 Switching (`tools/layer2_switching.py`)
- **`pt_create_vlan(device, vlan_id, vlan_name)`**: Crea una VLAN 802.1Q y le asigna nombre administrativo.
- **`pt_assign_access_port(device, interface, vlan_id)`**: Configura un puerto en modo acceso con PortFast.
- **`pt_configure_trunk(device, interface, allowed_vlans=None)`**: Configura enlace troncal 802.1Q con poda opcional de VLANs.
- **`pt_configure_stp(device, vlan_id, priority)`**: Configura la prioridad del Spanning Tree (múltiplos de 4096) para elegir el Root Bridge.
- **`pt_configure_etherchannel(device, interfaces, group_id, protocol="LACP")`**: Agrupa interfaces físicas en un Port-Channel mediante LACP (active), PAgP (desirable) o Static (on).

### 3. Layer 3 Routing Dual-Stack (`tools/layer3_routing.py`)
- **`pt_configure_ip(device, interface, ip_address, subnet_mask="255.255.255.0", ipv6_address=None)`**: Direccionamiento Dual-Stack IPv4 e IPv6 con `no shutdown`.
- **`pt_configure_subinterface(device, interface, subinterface_id, vlan_id, ip_address, subnet_mask="255.255.255.0", ipv6_address=None)`**: Router-on-a-Stick (RoAS) inter-VLAN con encapsulación `dot1Q`.
- **`pt_static_route(device, destination, mask_or_prefix, next_hop, is_ipv6=False)`**: Instala rutas estáticas IPv4 o IPv6.
- **`pt_configure_ospf(device, process_id, router_id, networks, is_ospfv3=False)`**: OSPFv2 / OSPFv3 con Router-ID y anuncio por áreas.
- **`pt_configure_bgp(device, as_number, neighbors, networks)`**: Sesiones de peering eBGP/iBGP y anuncios NLRI con máscaras de red.
- **`pt_configure_dhcp_pool(device, pool_name, network, mask, default_router, dns_server="8.8.8.8")`**: Servidor DHCP en Cisco IOS con exclusión automática del gateway.

### 4. Security & Firewalls (`tools/security_firewalls.py`)
- **`pt_configure_acl(device, acl_name_or_number, rules, is_extended=False)`**: ACLs estándar o extendidas (permit/deny por protocolo, origen, destino y puerto).
- **`pt_apply_acl_interface(device, interface, acl_name, direction)`**: Aplica la ACL en dirección `in` o `out`.
- **`pt_configure_nat_overload(device, inside_interface, outside_interface, acl_number=1)`**: NAT dinámico con PAT / Overload para salida a Internet.
- **`pt_configure_asa_interfaces(device, inside_ip, outside_ip)`**: Provisiona un firewall Cisco ASA 5506-X (`inside` nivel 100, `outside` nivel 0).
- **`pt_configure_vpn_ipsec(device_a, device_b, peer_ip, pre_shared_key, transform_set)`**: Túnel VPN Site-to-Site con ISAKMP Fase 1, PSK, Transform-Set Fase 2 y Crypto Map.

### 5. Wireless LAN & IoT (`tools/wireless_iot.py`)
- **`pt_configure_wireless_router(device, ssid, auth_type="WPA2-PSK", password, channel=6)`**: Configura routers Wi-Fi (WRT300N, Home Gateway), SSID y WPA2-PSK.
- **`pt_add_iot_sensor(sensor_type, name, x=350, y=350)`**: Spawnea sensores y actuadores inteligentes (Detector de Movimiento, Humo, Puertas, Temperatura).
- **`pt_connect_wireless_client(client_name, ssid, password)`**: Asocia clientes inalámbricos (Laptops, Teléfonos, Sensores) a una red Wi-Fi.
- **`pt_register_iot_device(device_name, server_ip, username="admin", password="admin")`**: Registra dispositivos en el servidor IoT de Packet Tracer.

### 6. Diagnostics & Verification (`tools/diagnostics.py`)
- **`pt_ping(source, destination)`**: Prueba de conectividad ICMP con tasa de éxito y tiempos de ida y vuelta (RTT).
- **`pt_traceroute(source, destination)`**: Traza el camino de saltos y latencia capa 3.
- **`pt_show_command(device, command)`**: Herramienta comodín para ejecutar cualquier verificación de Cisco IOS (`show ip route`, `show run`, `show ip int brief`, `show vlan brief`, etc.).

---

## 🎯 Ejemplo de Sesión de un LLM Operando en Vivo

1. **El LLM consulta la topología actual:**
   *Llamada:* `pt_get_topology()`
   *Resultado:* Observa que existe un Router `R1` y un Switch `SW1`.

2. **Crea y segmenta VLANs:**
   *Llamada:* `pt_create_vlan(device="SW1", vlan_id=10, vlan_name="VENTAS")`
   *Llamada:* `pt_assign_access_port(device="SW1", interface="FastEthernet0/5", vlan_id=10)`

3. **Configura Router-on-a-Stick en el Router:**
   *Llamada:* `pt_configure_subinterface(device="R1", interface="GigabitEthernet0/0", subinterface_id=10, vlan_id=10, ip_address="192.168.10.1")`

4. **Verifica conectividad en vivo:**
   *Llamada:* `pt_ping(source="R1", destination="192.168.10.1")`
   *Resultado:* `!!!!! Success rate is 100 percent (5/5)`.

5. **Persiste los cambios:**
   *Llamada:* `pt_save_workspace(filename="red_corporativa_final.pkt")`

---

## 🛡️ Estándares de Ingeniería y Resiliencia
- **Cero dependencias innecesarias:** Socket streaming estándar con framing a prueba de fragmentación de buffer.
- **Manejo de Errores Descriptivo:** El LLM recibe retroalimentación detallada si una interfaz está ocupada, si un dispositivo no existe o si se introduce una sintaxis no admitida.
- **Transiciones Automáticas:** El LLM puede enviar comandos de configuración sin preocuparse de en qué submodo (`config-if`, `config-router`, etc.) se encuentra el dispositivo.

