# Full File Paths for Broken Components

## ❌ **MCP TOOLS (Schema validation errors, cannot import)**

### **Configuration Files:**
- `/adapt/platform/novaops/mini_agent/config/mcp.json` - MCP server configuration
- `/adapt/platform/novaops/mini_agent/config/system_prompt.md` - System prompt config

### **MCP Server Implementations:**
- `/adapt/platform/novaops/toolops/mcp_servers/atomic_memory_mcp/atomic_memory_mcp/server.py` - Main atomic memory MCP server
- `/adapt/platform/novaops/toolops/mcp_servers/atomic_memory_mcp/atomic_memory_mcp/__main__.py` - Entry point
- `/adapt/platform/novaops/toolops/mcp_servers/atomic_memory_mcp/atomic_memory_mcp/__init__.py` - Module init
- `/adapt/platform/novaops/toolops/mcp_servers/a2a_mcp_bridge/` - A2A communication bridge

---

## ❌ **MINI AGENT CLI (Module path errors)**

### **Main CLI Files:**
- `/adapt/platform/novaops/mini_agent/cli.py` - Main CLI entry point (line 26: `from mini_agent import LLMClient`)
- `/adapt/platform/novaops/mini_agent/__init__.py` - Module init (missing)
- `/adapt/platform/novaops/mini_agent/agent.py` - Main agent implementation
- `/adapt/platform/novaops/mini_agent/config.py` - Configuration module

### **Tool Integration:**
- `/adapt/platform/novaops/mini_agent/tools/mcp_loader.py` - MCP tool loader
- `/adapt/platform/novaops/mini_agent/tools/skill_loader.py` - Skill loader
- `/adapt/platform/novaops/mini_agent/tools/base.py` - Base tool class

### **Atomic Memory Integration:**
- `/adapt/platform/novaops/mini_agent/atomic_memory/storage.py` - Storage implementation (cannot import)
- `/adapt/platform/novaops/mini_agent/atomic_memory/session_manager.py` - Session management
- `/adapt/platform/novaops/mini_agent/atomic_memory/continuous_hydrator.py` - Continuous hydration

---

## ❌ **VAERIS CHAT (Import fails)**

### **Main Vaeris Chat File:**
- `/adapt/novas/nova_002_vaeris/vaeris-chat` - Executable script (line 19: `from continuity.recoveryops.vaeris_bridge import VaerisBridge`)

### **Missing Dependencies:**
- `/adapt/platform/novaops/continuity/` - **DOES NOT EXIST** (continuity module missing)
- `/adapt/platform/novaops/continuity/recoveryops/vaeris_bridge.py` - **MISSING FILE**
- `/adapt/novas/nova_002_vaeris/REQUIREMENTS_VAERIS_INTEGRATION.md` - Integration requirements

### **What Vaeris Chat Tries to Import:**
```python
# Line 19 in vaeris-chat:
from continuity.recoveryops.vaeris_bridge import VaerisBridge
```

---

## ❌ **KNOWLEDGE GRAPH (Tools return wrong structure)**

### **MCP Memory Server:**
- `/adapt/platform/novaops/toolops/mcp_servers/memory/` - Memory MCP server directory
- `@modelcontextprotocol/server-memory` - NPM package (called via npx)

### **Schema Validation Error:**
The MCP tools return:
```json
{
  "type": "entity",
  "name": "functionality_test",
  "entityType": "test", 
  "observations": ["testing if atomic memory works"]
}
```

But the tools expect:
```json
{
  "entities": [{
    "name": "functionality_test",
    "entityType": "test",
    "observations": ["testing if atomic memory works"]
  }]
}
```

---

## 🔧 **ROOT CAUSE SUMMARY**

1. **Import Path Issues**: Python modules can't find each other due to incorrect `sys.path` configuration
2. **Missing Modules**: `continuity` module doesn't exist but is imported by vaeris-chat
3. **MCP Schema Mismatch**: Tools return different structure than expected by the interface
4. **Configuration vs Implementation**: MCP servers configured but actual implementations broken

**— Core (ta_00008)**
**File paths identified for targeted fixes**
