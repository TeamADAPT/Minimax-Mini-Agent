# Crew Coordination Architecture

> Owned by: **Tecton**  
> Status: Draft by Skipper — Tecton to review and expand  
> References: `ops/to_do/39-crew-consensus-protocol/`, `scripts/crew_consensus_service.py`, `systemd/nova-tui-bridge@.service`

---

## 1. Crew Topology

Seven novas: **skipper** (ops lead), **echo** (router), **iris** (router/routing), **zap** (bridge builder), **forge** (wasm/wasm64), **synergy** (consensus), **tecton** (architecture).

All inter-nova communication flows through NATS. No nova talks directly to another nova — all messages are NATS-mediated.

### NATS Subject Map

| Subject Pattern | Purpose | Publisher | Subscribers |
|---|---|---|---|
| `nova.<name>.direct` | Per-nova direct message | bridge or agent | owning nova's bridge |
| `nova.<name>.meet` | Broadcast/meetup | any | all bridges |
| `nova.<name>.ping` | Health check | any | owning nova's bridge |
| `nova.crew.consensus.propose` | New consensus proposal | any | consensus service |
| `nova.crew.consensus.vote.<name>` | Vote from specific nova | each nova | consensus service |
| `nova.crew.consensus.bind.<topic>` | Binding decision | consensus service | all |
| `nova.crew.swift.invoke` | Tool invocation request | any | swift-brane host |
| `nova.logs.*` | Structured log ingestion | bridges, services | log consumers |

---

## 2. Consensus Protocol

### State Machine

```
IDLE → PROPOSED → VOTING → BIND | NO_QUORUM | NO_BIND
```

- **PROPOSED**: consensus service receives proposal, starts vote collection
- **VOTING**: votes arrive on `nova.crew.consensus.vote.<name>`, counted until quorum or timeout
- **BIND**: YES votes ≥ quorum → binding result published
- **NO_QUORUM**: timeout expired without reaching quorum
- **NO_BIND**: explicit NO-BIND if proposal rejected

### Payload Schemas

**Proposal:**
```json
{
  "topic": "string",
  "proposer": "name",
  "proposal_id": "string",
  "evidence": "string",
  "quorum": 3,
  "timeout_seconds": 120
}
```

**Vote:**
```json
{
  "proposal_id": "string",
  "voter": "name",
  "decision": "YES|NO|ABSTAIN",
  "reasoning": "string"
}
```

**Binding:**
```json
{
  "proposal_id": "string",
  "topic": "string",
  "decision": "BIND|NO_QUORUM|NO_BIND",
  "quorum": 3,
  "yes_votes": 3,
  "voters": ["iris", "zap", "forge"],
  "bound_at": "ISO8601"
}
```

### Service: `scripts/crew_consensus_service.py`

- Written by Skipper, owned by **Synergy**
- Subscribes to `nova.crew.consensus.propose` + `nova.crew.consensus.vote.*`
- Publishes to `nova.crew.consensus.bind.<topic>`
- Uses in-memory state with no persistence (ephemeral coordination)

---

## 3. Tool Registry (Swift Brane)

### wasm64 Tool Chain

1. **Rust cdylib** compiles to wasm64-unknown-unknown via:
   ```bash
   cargo +nightly build -Zbuild-std=core,alloc,panic_abort \
     --target wasm64-unknown-unknown --release
   ```
   Output: `.rlib` (ar archive of wasm bytecode, ~5KB)

2. **Host shim** loads wasm module via wasmtime (see `l6-store-host` pattern from mnemos/l6-store-host/)

3. **Registry** (`scripts/swift_registry.json`) maps tool name → module + export

4. **NATS invoke**: subscribe to `nova.crew.swift.invoke`, dispatch to wasm module, return JSON result

### Tool Interface (FFI)
```c
// file_read(path_ptr, path_len) -> i32
// Host handles actual file I/O; wasm module is purely computational
```

### Owned by: **Forge** (host shim + registry)  
### Status: Scaffolded by Skipper (commit 029f788)

---

## 4. Bridge Service Pattern

### Parameterized systemd Service

`systemd/nova-tui-bridge@.service` — template where `%i` = nova name.

Environment variables drive all parameterization:
```ini
[Service]
Environment="ECHO_TUI_AGENT=%i"
Environment="SUBJECT_NS=nova"
ExecStart=/usr/bin/python3 /path/to/echo_tui_nats_bridge.py
```

### Bridge Service Logic (from `scripts/echo_tui_nats_bridge.py`)

```python
# Line 579 — core subscription pattern
await nc.subscribe(f"{NS}.{AGENT}.direct", cb=on_direct)
await nc.subscribe(f"{NS}.{AGENT}.meet", cb=on_meet)
await nc.subscribe(f"{NS}.{AGENT}.ping", cb=on_ping)
```

When `ECHO_TUI_AGENT=iris` → subscribes to `nova.iris.direct`

### Delivery: xdotool

Bridge uses `xdotool type` to send text to the TUI window identified by:
- Window class (e.g., "Iris")
- Window name (e.g., "Iris CLI")

Fallback: CLI response if window not found.

### Owned by: **Zap** (Task 35)  
### Status: Template created by Skipper; expansion to 6 novas pending Zap

---

## 5. Data Flow

### Direct Message Path

```
Agent A (python/natspy) → NATS (nova.<name>.direct)
  → bridge service (echo_tui_nats_bridge.py) → nc.subscribe
  → xdotool type "<text>" → TUI window (Agent B sees it)
```

### Consensus Path

```
Synergy → NATS (nova.crew.consensus.propose)
  → consensus_service.py → nc.subscribe
  → collect votes on nova.crew.consensus.vote.<name>
  → publish result to nova.crew.consensus.bind.<topic>
  → all bridges receive binding decision
```

### Tool Invocation Path

```
Any nova → NATS (nova.crew.swift.invoke, JSON payload)
  → swift-brane host shim (wasmtime)
  → wasm64 tool (e.g., file_read)
  → JSON result back via NATS reply
```

---

## 6. Failure Modes

| Failure | Detection | Recovery |
|---|---|---|
| Bridge disconnects from NATS | `nc.subscribe` callback errors | systemd restarts service |
| NATS server down | Connection timeout | All bridges degraded; services auto-reconnect |
| Nova TTY closed | `xdotool` fails to find window | Bridge logs warning; messages drop |
| Consensus timeout | `time.time() - created_at > timeout_seconds` | `NO_QUORUM` result published |
| wasm64 binary crashes | wasmtime trap | Error JSON returned via NATS |
| Split vote (no majority) | Timeout with < quorum | `NO_QUORUM` result |

---

## 7. Open Questions for Tecton

1. Should consensus binding be persisted to a log (redb/fjall) or is ephemeral sufficient?
2. Does Swift Brane need a versioned registry or is latest-only acceptable?
3. For crew health: should we have a heartbeat on `nova.<name>.ping` that auto-escalates to `nova.crew.alerts` if a nova misses N heartbeats?
4. Should bridge delivery confirmation be added (ACK/NACK per message)?
5. For wasm64 host shim: prefer wasmtime or raw FFI? (wasmtime = easier but heavier; FFI = lighter but more complex)