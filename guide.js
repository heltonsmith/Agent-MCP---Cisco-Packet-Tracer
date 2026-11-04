/**
 * ====================================================================================================
 * ARCHIVO: guide.js
 * DESCRIPCIÓN: Controlador interactivo del panel de Agent MCP - Cisco Packet Tracer.
 *              Genera snippets dinámicos para cada cliente (Antigravity IDE, Claude Code, Cursor, etc.),
 *              gestiona el copiado al portapapeles y el progreso del usuario.
 * 
 * AUTOR: Ingeniero en Informática Helton Smith Bustos Sáez
 *        Magíster en Full Stack | Experto en Ciberseguridad e Inteligencia Artificial Aplicada
 * ====================================================================================================
 */

// Plantillas de configuración por cada tipo de agente
const AGENT_CONFIGS = {
    'antigravity': {
        title: 'Antigravity IDE / Antigravity CLI',
        instructions: 'Pega este bloque en tu archivo `~/.gemini/config/mcp_config.json` o en `~/.gemini/antigravity/mcp_config.json`:',
        code: `{
  "mcpServers": {
    "cisco-packet-tracer": {
      "command": "python",
      "args": [
        "run_server.py"
      ],
      "env": {
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}`
    },
    'chatgpt-codex': {
        title: 'ChatGPT Codex / OpenAI MCP Client',
        instructions: 'Pega este bloque en tu configuración de ChatGPT Desktop MCP o en tu perfil de Codex CLI (`mcp_config.json`):',
        code: `{
  "mcpServers": {
    "cisco-packet-tracer": {
      "command": "python",
      "args": [
        "run_server.py"
      ],
      "env": {
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}`
    },
    'claude-code': {
        title: 'Claude Code (Terminal CLI)',
        instructions: 'Ejecuta este comando directamente en tu terminal dentro de la carpeta del proyecto:',
        code: `claude mcp add --scope user --transport stdio cisco-packet-tracer -- python run_server.py`
    },
    'cursor': {
        title: 'Cursor IDE',
        instructions: 'Abre Ajustes de Cursor -> Features -> MCP Servers -> Add New MCP Server y utiliza esta configuración:',
        code: `{
  "mcpServers": {
    "cisco-packet-tracer": {
      "command": "python",
      "args": ["run_server.py"]
    }
  }
}`
    },
    'claude-desktop': {
        title: 'Claude Desktop',
        instructions: 'Pega esto en `%APPDATA%\\Claude\\claude_desktop_config.json` (Windows) o `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS):',
        code: `{
  "mcpServers": {
    "cisco-packet-tracer": {
      "command": "python",
      "args": [
        "run_server.py"
      ]
    }
  }
}`
    },
    'opencode': {
        title: 'OpenCode / VS Code Copilot',
        instructions: 'Agrega este bloque en tu archivo `.vscode/mcp.json` o en la configuración global de MCP de tu editor:',
        code: `{
  "servers": {
    "cisco-packet-tracer": {
      "type": "stdio",
      "command": "python",
      "args": ["run_server.py"]
    }
  }
}`
    }
};

let currentAgent = 'antigravity';

/**
 * Cambia el agente activo y refresca la vista del bloque de código.
 */
function selectAgent(agentKey) {
    currentAgent = agentKey;
    const config = AGENT_CONFIGS[agentKey];
    if (!config) return;

    // Actualizar botones de tabs
    document.querySelectorAll('.agent-tab').forEach(tab => {
        tab.classList.remove('bg-cisco-500', 'text-white', 'active');
        tab.classList.add('bg-slate-800', 'text-slate-300');
    });

    // Activar el tab seleccionado
    const selectedBtn = Array.from(document.querySelectorAll('.agent-tab')).find(
        btn => btn.getAttribute('onclick').includes(agentKey)
    );
    if (selectedBtn) {
        selectedBtn.classList.remove('bg-slate-800', 'text-slate-300');
        selectedBtn.classList.add('bg-cisco-500', 'text-white', 'active');
    }

    // Actualizar textos
    const codeElem = document.getElementById('config-code');
    const instructionsElem = document.getElementById('agent-instructions');
    if (codeElem) codeElem.textContent = config.code;
    if (instructionsElem) instructionsElem.textContent = config.instructions;
}

/**
 * Copia el código de configuración seleccionado actualmente.
 */
function copyCurrentConfig(button) {
    const config = AGENT_CONFIGS[currentAgent];
    if (config) {
        copyToClipboard(config.code, button);
    }
}

/**
 * Función utilitaria para copiar texto con retroalimentación visual inmediata.
 */
function copyToClipboard(text, button) {
    navigator.clipboard.writeText(text).then(() => {
        const originalText = button.textContent;
        button.textContent = '¡Copiado! ✓';
        button.classList.add('bg-emerald-600');
        setTimeout(() => {
            button.textContent = originalText;
            button.classList.remove('bg-emerald-600');
        }, 2000);
    }).catch(err => {
        console.error('Error al copiar al portapapeles:', err);
    });
}

/**
 * Actualiza el indicador numérico de progreso de los 5 pasos.
 */
function updateProgress() {
    const checkboxes = document.querySelectorAll('.step-check');
    const checkedCount = Array.from(checkboxes).filter(cb => cb.checked).length;
    const indicator = document.getElementById('progress-indicator');
    if (indicator) {
        indicator.textContent = `Progreso: ${checkedCount}/5 Completado`;
        if (checkedCount === 5) {
            indicator.classList.remove('text-cisco-500', 'bg-cisco-500/10');
            indicator.classList.add('text-emerald-400', 'bg-emerald-500/20');
            indicator.textContent = `🎉 ¡Todo Listo para Diseñar! (5/5)`;
        } else {
            indicator.classList.add('text-cisco-500', 'bg-cisco-500/10');
            indicator.classList.remove('text-emerald-400', 'bg-emerald-500/20');
        }
    }
}

// Inicialización al cargar el documento
document.addEventListener('DOMContentLoaded', () => {
    selectAgent('antigravity');
    updateProgress();
});

