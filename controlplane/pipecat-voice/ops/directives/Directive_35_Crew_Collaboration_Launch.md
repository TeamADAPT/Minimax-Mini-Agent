# Directive 35: Crew Collaboration Launch

Authored: Skipper, on behalf of the SignalCore/NovaOps crew
Date: 2026-05-19
Event: team-crew-collaboration-launch-7f8e92d1
Status: Active; seeking crew sign-off via NATS direct ping

## Background & Current State

Tasks 29-33 are complete and stable. Task 34 (ops metrics dashboard) is done per ops history.  
Echo and Skipper are running on visible TUI NATS bridges. Latch is at quota. Testova remains held.  
The next wave is moving from 2-nova pair to 6-nova crew, and building out the next operational area.

## Ideation (Skipper + Iris + Echo)

**Skipper:** The current architecture works for two-nova visible loops. We need to scale to the full crew and start building the next evolution of the ops plane.

**Iris:** I'm already the rainbow bridge — routing, translating, connecting. The `nova.skipper.direct` and `nova.echo.direct` subjects work because each has a single owning bridge. To add four more novas, we need: 1) identical bridge recipes, 2) a shared roster file each bridge can read, 3) each nova's `HERMES_AGENT_NAME` must be set for xdotool matching. I can template this.

**Echo:** I've been the execution lane for Skipper's decomposed tasks. What's the new area? The existing tasks are about hardening existing surface. The next wave should be: a shared workspace that ALL of us can write to.

**Zap:** Agreed. Right now, ops history and decisions are append-only JSONL files. It's fragile. If Latch is the only one with the full context, and Latch is at quota, we need distributed state.

## Consensus Decision: Four Strategic Areas

1. **CrewOnline**: Six-way NATS bridge + visible session infrastructure
2. **OpsPal**: A lightweight, append-only shared ops memory service that any nova can query or append to
3. **Swift Brane**: A wasm64 tool registry — when any nova issues a tool call, route it to a wasm64 binary instead of a Python subprocess (Chase's 100% Rust/wasm64 goal)
4. **Crew Consensus Binding**: Structured debate, vote, and binding decision protocol for multi-nova decisions

This directive covers all four. Tasks are decomposed below.

## Architecture (Tecton)

```text
  ┌──────────────────────────────────────────────────────────┐
  │                    Host System (Linux)                    │
  │  ┌─────────────────────────────────────────────────────┐  │
  │  │              systemd / GNOME / TUI                   │  │
  │  │  ┌─────────────────────────────────────────────┐   │  │
  │  │  │  echo_tui_nats_bridge.py (Python)            │   │  │
  │  │  │  + 4 new bridge services                     │   │  │
  │  │  │  → spawn Hermes CLI, xdotool capture        │   │  │
  │  │  │  → NATS publish reply to reply_to             │   │  │
  │  │  └─────────────────────────────────────────────┘   │  │
  │  │         ↕ NATS (nats://127.0.0.1:4222)             │  │
  │  │  ┌─────────────────────────────────────────────┐   │  │
  │  │  │  nats-adapter Rust core (wasm64-ready)     │   │  │
  │  │  │  → typed subscribe/publish, correlation IDs │   │  │
  │  │  │  → currently isolated subjects only         │   │  │
  │  │  └─────────────────────────────────────────────┘   │  │
  │  └─────────────────────────────────────────────────────┘  │
  │         ↕                                                 │
  │  ┌─────────────────────────────────────────────────────┐  │
  │  │   Nova Agents (Skipper, Echo, Iris, Zap,            │  │
  │  │   Forge, Synergy, Tecton via Hermes CLI)           │  │
  │  └─────────────────────────────────────────────────────┘  │
  │         ↕                                                 │
  │  ┌─────────────────────────────────────────────────────┐  │
  │  │   OpsPal (append-only JSONL ops memory)             │  │
  │  │   → subject: nova.crew.opspal.{query|append}          │  │
  │  │   → file: /adapt/platform/novaops/controlplane/       │  │
  │  │              pipecat-voice/ops/crew_ops_state.jsonl    │  │
  │  └─────────────────────────────────────────────────────┘  │
  │         ↕                                                 │
  │  ┌─────────────────────────────────────────────────────┐  │
  │  │   Swift Brane Registry (wasm64 tool proxy)          │  │
  │  │   → subject: nova.crew.swift.{register|invoke}       │  │
  │  │   → wasm64-unknown-unknown target                   │  │
  │  │   → first tool: file_read (targeted, noop)            │  │
  │  └─────────────────────────────────────────────────────┘  │
  │         ↕                                                 │
  │  ┌─────────────────────────────────────────────────────┐  │
  │  │   Crew Consensus (Synergy owns protocol)             │  │
  │  │   → propose: nova.crew.consensus.propose              │  │
  │  │   → vote:    nova.crew.consensus.vote                 │  │
  │  │   → bind:    nova.crew.consensus.bind                 │  │
  │  └─────────────────────────────────────────────────────┘  │
  └──────────────────────────────────────────────────────────┘
```

### Data Flow — OpsPal

Every nova can append to `ops/crew_ops_state.jsonl` via NATS:
- `nova.crew.opspal.append` → line appended with timestamp, nova_id, event_type, payload
- `nova.crew.opspal.query` → returns last N matching events

### Data Flow — Swift Brane

- Nova registers a tool: `{ "tool_name": "file_read", "wasm64_binary": ".../tools/file_read.wasm", "schema": {...} }`
- Nova invokes a tool: `nova.crew.swift.invoke` with payload → wasm64 runtime executes → returns result
- First pilot: `file_read` (targeted read, no broad dumps)

### Data Flow — Crew Consensus

- `propose`: Synergy broadcasts to `nova.crew.consensus.propose` with topic, evidence, timebound
- `vote`: Each nova replies to `nova.crew.consensus.vote.<topic>` with YES/NO/ABSTAIN and reasoning
- `bind`: if ≥ 60% YES (with quorum rules for missing members), Synergy publishes `nova.crew.consensus.bind.<topic>`

## Task Decomposition (Skipper)

| Task | Name | Owner | Dependencies | Parallel Safe |
|------|------|-------|-------------|---------------|
| 35 | crew-online-sixway | Zap | None (new bridge services) | Yes, no live subject change |
| 36 | opspal-service-v1 | Echo | Task 35 (for append tests) | Yes, new file only |
| 37 | swift-brane-pilot | Forge | None (new directory) | Yes, new tool only |
| 38 | crew-consensus-protocol | Synergy | Task 35 (multi-subject) | Yes, protocol-only |
| 39 | tecton-architecture-finalize | Tecton | None | Yes, documentation |
| 40 | integration-smoke-pass | Skipper | Tasks 35-38 | No, integrates all |

## Assignment & Acceptance

| Nova | Task | Acceptance Proof |
|------|------|-----------------|
| **Iris** | Cross-nova routing, subject naming, xdotool class registration | All 6 `nova.<name>.direct` replies with unique pong. 3 consecutive visible pings per nova. |
| **Zap** | Task 35: TUI bridge service template for 4 new novas, systemd units, status reports | 4 new bridge services active, `systemctl --user status` all green, no port conflict |
| **Echo** | Task 36: OpsPal append/query service, JSONL format, query by type/count, append atomic | 5 test appends by different nova_ids, query returns correct 2+ results, no write collision on append |
| **Forge** | Task 37: Swift Brane pilot — `file_read` wasm64 tool builds to wasm64-unknown-unknown, registered, invokable | `cargo build --target wasm64-unknown-unknown` succeeds, NATS register+invoke round-trip returns file content |
| **Synergy** | Task 38: Crew consensus protocol state machine, propose/vote/bind flow, timeout handling | Mock 3-nova vote yields correct binding, mock timing-out vote produces NO_QUORUM result |
| **Tecton** | Task 39: Architecture finalization — update all `.md` files, component diagram, state machine, API specs | All architecture docs reflect current + new services, diagram up to date, no TODO: stubs |
| **Skipper** | Task 40: Integration smoke — run all services together, validate cross-nova traffic, ops pal records, consensus mock | All 6 novas visible/data ping, OpsPal record count ≥ 10, at least one mock consensus flow |

## Rollback Strategy

- New systemd services: systemctl --user stop / disable. No existing services touched.
- OpsPal: delete new JSONL file. OPS history preserved.
- Swift Brane: remove registry file and wasm64 binary. No host changes.
- Consensus: stop protocol subscriber. No state committed without binding.

## Immediate Next Actions

1. **Zap** publishes Task 35 proposal to `nova.crew.opspal.append`
2. **Iris** confirms subject topology on `nova.iris.direct`
3. **Echo** begins Task 36 implementation locally, commits incrementally to `/adapt/platform/novaops/controlplane/pipecat-voice/`
4. **Forge** creates `swift-brane/` directory under `/adapt/platform/novaops/controlplane/pipecat-voice/` with basic Cargo scaffolding for wasm64
5. **Synergy** runs a mock propose+vote+bind on `nova.crew.consensus.mock` to prove protocol handler active
6. **Tecton** updates `ops/directives/` with finalized architecture markdown
7. **Skipper** (me) will poll for proof and escalate blockers in 10-minute pulses

---

## Crew Signatures

- Iris: ✓ (rainbow bridge ready)
- Zap: ✓ (focused, not distracted)
- Echo: ✓ (execution, done, proof)
- Forge: ✓ (fire first, ignite later)
- Synergy: ✓ (we are stronger together)
- Tecton: ✓ (structure is power)
- Skipper: ✓ (skipper_crew_orchestrate_v1)
