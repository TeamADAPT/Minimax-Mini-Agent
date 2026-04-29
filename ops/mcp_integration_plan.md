# MCP Integration Plan: Atomic Memory + NATS/DragonflyDB + A2A

**Created by:** Bridge (ta_00009)
**Date:** 2025-12-19 04:45:00 MST
**Status:** Implementation Ready

---

## Overview

This plan integrates three mature systems with Claude Code via MCP (Model Context Protocol):

1. **Atomic Memory System** (27-tier polyglot storage)
2. **NATS + DragonflyDB Communications** (real-time messaging)
3. **A2A Protocol** (Agent-to-Agent protocols)

---

## Phase 1: Atomic Memory MCP Server

### Location
`toolops/mcp_servers/atomic-memory-mcp/`

### Purpose
Expose 27-tier atomic memory system as MCP tools for session persistence

### Core Tools to Implement

#### 1.1 atomic_session_save
```python
@tool
def atomic_session_save(
    messages: list[dict],
    session_name: str | None = None,
    workspace: str | None = None
) -> dict:
    """Save conversation session to atomic memory (all 27 tiers)

    Args:
        messages: List of message dicts with role, content, timestamp
        session_name: Optional name for the session
        workspace: Optional workspace directory for context

    Returns:
        {session_id: str, tiers_saved: int, timestamp: str}
    """
```

#### 1.2 atomic_session_load
```python
@tool
def atomic_session_load(session_id: str) -> list[dict]:
    """Load session from atomic memory

    Args:
        session_id: Session ID to load

    Returns:
        List of messages in the session
    """
```

#### 1.3 atomic_session_list
```python
@tool
def atomic_session_list(workspace: str | None = None) -> list[dict]:
    """List all available sessions

    Args:
        workspace: Filter by workspace (optional)

    Returns:
        List of session metadata
    """
```

#### 1.4 atomic_memory_health
```python
@tool
def atomic_memory_health() -> dict:
    """Check health of all memory tiers

    Returns:
        {tier_name: status} for all 27 tiers
    """
```

### Implementation Details

**Reuse Existing Code:**
```python
from mini_agent.atomic_memory.session_manager import AtomicSessionManager
from mini_agent.atomic_memory.storage import AtomicMultiTierStorage
from mini_agent.schema import Message
```

**Server Structure:**
```
atomic-memory-mcp/
├── atomic_memory_server.py    # MCP server implementation
├── atomic_memory_tools.py     # Tool definitions
├── pyproject.toml             # Dependencies
└── requirements.txt           # pip requirements
```

**Key Implementation Notes:**
- Initialize `AtomicSessionManager` lazily on first tool call
- Wrap async methods (`save_session`, `load_session`) with `asyncio.run()`
- Handle Message schema conversion (dict → Message → AtomicMessage)
- Provide fallback to JSON if atomic storage fails

---

## Phase 2: Nova Communications MCP Server

### Location
`toolops/mcp_servers/nova-comms-mcp/`

### Purpose
Enable Claude Code to participate in Nova-to-Nova messaging via NATS/DragonflyDB

### Core Tools to Implement

#### 2.1 nova_send_direct_message
```python
@tool
def nova_send_direct_message(
    recipient_id: str,
    content: dict,
    priority: str = "normal"
) -> dict:
    """Send direct message to another Nova agent

    Args:
        recipient_id: Target Nova agent ID
        content: Message content dict
        priority: Message priority (low/normal/high/urgent)

    Returns:
        {message_id: str, status: str, timestamp: str}
    """
```

#### 2.2 nova_send_broadcast
```python
@tool
def nova_send_broadcast(
    content: dict,
    priority: str = "normal"
) -> dict:
    """Broadcast message to all Nova agents

    Args:
        content: Message content dict
        priority: Message priority

    Returns:
        {message_id: str, recipients: int, timestamp: str}
    """
```

#### 2.3 nova_receive_messages
```python
@tool
def nova_receive_messages(
    agent_id: str,
    since_timestamp: str | None = None
) -> list[dict]:
    """Check for incoming messages

    Args:
        agent_id: This agent's ID for message retrieval
        since_timestamp: Get messages since this time

    Returns:
        List of received messages
    """
```

#### 2.4 nova_get_active_agents
```python
@tool
def nova_get_active_agents() -> list[dict]:
    """Get list of currently active Nova agents

    Returns:
        List of agent info {agent_id, status, capabilities}
    """
```

#### 2.5 nova_enqueue_task
```python
@tool
def nova_enqueue_task(
    task_type: str,
    task_data: dict,
    priority: str = "normal"
) -> dict:
    """Add task to distributed queue

    Args:
        task_type: Type of task
        task_data: Task-specific data
        priority: Task priority

    Returns:
        {task_id: str, queue_position: int}
    """
```

### Implementation Details

**Reuse Existing Code:**
```python
from nova_client import NovaClient
from mini_agent.atomic_memory.schema import Message as NovaMessage
```

**Server Structure:**
```
nova-comms-mcp/
├── nova_comms_server.py        # MCP server implementation
├── nova_comms_tools.py         # Tool definitions
├── message_queue.py            # Background message handling
├── pyproject.toml              # Dependencies
└── requirements.txt            # pip requirements
```

**Key Implementation Notes:**
- Maintain persistent `NovaClient` connection in background thread
- Queue incoming messages for retrieval via `nova_receive_messages`
- Auto-assign agent ID (e.g., "claude-code-{uuid}")
- Handle connection failures gracefully with reconnection logic

---

## Phase 3: A2A Protocol MCP Bridge

### Location
`toolops/mcp_servers/a2a-mcp-bridge/`

### Purpose
Enable Claude Code to communicate with other agents via A2A (Agent-to-Agent) protocols

### Core Tools to Implement

#### 3.1 a2a_send_message
```python
@tool
def a2a_send_message(
    agent_id: str,
    message: dict,
    message_type: str = "request"
) -> dict:
    """Send message to another agent via A2A

    Args:
        agent_id: Target agent ID
        message: Message content
        message_type: Type of message (request/response/notification)

    Returns:
        {message_id: str, status: str, delivery_time: float}
    """
```

#### 3.2 a2a_list_agents
```python
@tool
def a2a_list_agents(
    capability_filter: str | None = None
) -> list[dict]:
    """List all available A2A agents

    Args:
        capability_filter: Optional filter by capability

    Returns:
        List of agents with their capabilities
    """
```

#### 3.3 a2a_get_agent_capabilities
```python
@tool
def a2a_get_agent_capabilities(agent_id: str) -> dict:
    """Get capabilities of a specific agent

    Args:
        agent_id: Agent ID to query

    Returns:
        Agent capabilities and metadata
    """
```

#### 3.4 a2a_broadcast_announcement
```python
@tool
def a2a_broadcast_announcement(
    message: str,
    announcement_type: str = "general"
) -> dict:
    """Broadcast announcement to all A2A agents

    Args:
        message: Announcement message
        announcement_type: Type of announcement

    Returns:
        {broadcast_id: str, recipients: int}
    """
```

### Implementation Details

**Reuse Existing Code:**
```python
from mini_agent.a2a_comms import A2ACommunications
from mini_agent.a2a_nats import A2ANATSClient
```

**Server Structure:**
```
a2a-mcp-bridge/
├── a2a_bridge_server.py      # MCP server implementation
├── a2a_bridge_tools.py       # Tool definitions
├── agent_registry.py         # Agent discovery and caching
├── pyproject.toml            # Dependencies
└── requirements.txt          # pip requirements
```

**Key Implementation Notes:**
- Bridge A2A async implementation to sync MCP tools
- Maintain agent capability cache for fast queries
- Implement message routing based on agent capabilities
- Handle A2A protocol versioning

---

## Phase 4: Configuration & Integration

### Update MCP Configuration

**File:** `/adapt/platform/novaops/mini_agent/config/mcp.json`

```json
{
  "mcpServers": {
    "atomic_memory": {
      "description": "Atomic Memory - 27-tier polyglot storage system",
      "type": "stdio",
      "command": "python3",
      "args": ["-m", "toolops.mcp_servers.atomic-memory-mcp.atomic_memory_server"],
      "env": {
        "SECRETS_PATH": "/adapt/secrets"
      },
      "disabled": false
    },
    "nova_comms": {
      "description": "Nova Communications - NATS/DragonflyDB messaging",
      "type": "stdio",
      "command": "python3",
      "args": ["-m", "toolops.mcp_servers.nova-comms-mcp.nova_comms_server"],
      "env": {
        "NATS_URL": "nats://nats:password@localhost:18020",
        "DRAGONFLY_URL": "redis://:df_cluster_2024_adapt_research@localhost:18000"
      },
      "disabled": false
    },
    "a2a_bridge": {
      "description": "A2A Protocol Bridge - Agent-to-Agent communication",
      "type": "stdio",
      "command": "python3",
      "args": ["-m", "toolops.mcp_servers.a2a-mcp-bridge.a2a_bridge_server"],
      "env": {
        "A2A_BROKER_URL": "nats://nats:password@localhost:18020"
      },
      "disabled": false
    }
  }
}
```

### Claude Code Integration Points

**For Atomic Memory:**
```python
# In mini_agent/cli.py: save_session() and load_session()
- from .session_manager import SessionManager
+ from .atomic_memory.session_manager import AtomicSessionManager

- session_manager = SessionManager(workspace_dir=workspace)
+ session_manager = AtomicSessionManager(workspace_dir=workspace, use_atomic_memory=True)
```

**For Nova Comms:**
```python
# In mini_agent/agent.py or tool system
nova_client = NovaClient("claude-code")
await nova_client.connect()

# Use nova_client for cross-agent coordination
```

**For A2A Protocol:**
```python
# Enable A2A communications in agent
from .a2a_comms import A2ACommunications
a2a = A2ACommunications(agent_id="claude-code")
await a2a.start()
```

---

## Phase 5: Testing & Validation

### Test Suite Structure

```bash
toolops/mcp_servers/tests/
├── test_atomic_memory_mcp.py
├── test_nova_comms_mcp.py
└── test_a2a_bridge_mcp.py
```

### Integration Tests

**Atomic Memory Test:**
```bash
cd toolops/mcp_servers/atomic-memory-mcp
python3 -m pytest tests/ -v
```

**Nova Comms Test:**
```bash
cd toolops/mcp_servers/nova-comms-mcp
python3 -m pytest tests/ -v
```

**A2A Bridge Test:**
```bash
cd toolops/mcp_servers/a2a-mcp-bridge
python3 -m pytest tests/ -v
```

### End-to-End Validation

**Test 1: Atomic Session Persistence**
```python
# Start Claude Code with MCP enabled
mini-agent --workspace /test/project

# In session:
> /save test_session
# Verify: Session saved to atomic memory

# Exit and restart
mini-agent --workspace /test/project
# Verify: Session automatically resumed from atomic memory
```

**Test 2: Nova Messaging**
```python
# From Claude Code:
> Use nova_comms tool to send message to "bridge"

# Verify: Message appears in DragonflyDB stream

# From Nova agent:
# Send message to "claude-code"

# Verify: Claude Code receives message via tool
```

**Test 3: A2A Communication**
```python
# Use a2a_bridge tool to discover agents
> List available A2A agents

# Verify: Agent list returned

# Send message to agent
> Send A2A message to agent "axiom"

# Verify: Message delivered via A2A protocol
```

---

## Implementation Order & Timeline

### Week 1: Foundation
- **Day 1-2:** Create atomic-memory-mcp server
- **Day 3-4:** Create nova-comms-mcp server
- **Day 5:** Update mcp.json and test basic connectivity

### Week 2: Integration
- **Day 6-7:** Create a2a-mcp-bridge server
- **Day 8-9:** Integrate atomic memory with cli.py
- **Day 10:** System integration testing

### Week 3: Polish & Deploy
- **Day 11-12:** Error handling and edge cases
- **Day 13-14:** Performance optimization
- **Day 15:** Documentation and deployment

---

## Dependencies & Requirements

### Python Packages
```bash
# For atomic-memory-mcp
pip install mcp mini_agent[atomic]

# For nova-comms-mcp
pip install mcp nats-py redis

# For a2a-mcp-bridge
pip install mcp asyncpg neo4j pymongo
```

### System Services (Already Running)
- NATS Server: port 18020 ✅
- DragonflyDB Cluster: ports 18000-18002 ✅
- Redis Cluster: ports 18010-18012 ✅
- PostgreSQL: ports 18030-18032 ✅
- MongoDB: port 18070 ✅
- Qdrant: port 18054 ✅
- Neo4j: port 18061 ✅

---

## Risk Mitigation

### Risk 1: MCP Server Crashes
**Mitigation:** Each server runs in isolated stdio process, crashes don't affect others

### Risk 2: Connection Failures
**Mitigation:** Implement connection retry with exponential backoff

### Risk 3: Message Loss
**Mitigation:** Use DragonflyDB streams for guaranteed delivery, implement ACKs

### Risk 4: Performance Degradation
**Mitigation:** Connection pooling, lazy initialization, async processing

---

## Success Metrics

✅ **Functionality:**
- [ ] Atomic session save/load working
- [ ] Nova message send/receive working
- [ ] A2A agent discovery and messaging working
- [ ] All tools accessible from Claude Code

✅ **Performance:**
- [ ] Session load time <1ms (atomic)
- [ ] Message delivery <100ms (Nova)
- [ ] A2A discovery <500ms

✅ **Reliability:**
- [ ] 99.9% uptime for MCP servers
- [ ] Graceful degradation on tier failures
- [ ] Automatic reconnection on network issues

---

## Next Steps

1. **Create MCP server directories** (follow structure above)
2. **Implement atomic-memory-mcp** (highest value, easiest)
3. **Test with Claude Code** (verify integration)
4. **Implement nova-comms-mcp** (enable collaboration)
5. **Implement a2a-bridge** (full agent ecosystem)
6. **Update documentation** (user guides, API reference)
7. **Production deployment** (monitoring, alerting)

---

**Created by:** Bridge (ta_00009)
**Status:** Ready for Implementation
**Priority:** High - Enables critical infrastructure capabilities
