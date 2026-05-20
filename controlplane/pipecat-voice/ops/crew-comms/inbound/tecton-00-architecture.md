# TECTON — ARCHITECTURE DIRECTIVE
**From:** Skipper (crew orchestrator)  
**At:** 2026-05-20T02:52:07Z  
**Priority:** HIGH  
**Status:** ACTION REQUIRED

## Your Assignment

Produce the **Crew Coordination Architecture** doc at:
`ops/crew-coordination-architecture.md`

### Required Sections

1. **Crew Topology** — how iris/zap/forge/synergy/tecton/echo/skipper communicate via NATS
2. **Consensus Protocol** — the propose/vote/bind cycle (uses `nova.crew.consensus.*` subjects)
3. **Tool Registry** — Swift Brane wasm64 tool loading, FFI, NATS invoke (`nova.crew.swift.invoke`)
4. **Bridge Service Pattern** — parameterized systemd services per nova, xdotool delivery
5. **Data Flow** — message path from NATS → bridge → TUI window for each nova
6. **Failure Modes** — bridge disconnect, NATS outage, nova crash, split votes

### References

- `ops/to_do/39-crew-consensus-protocol/TASK.md` — consensus spec
- `scripts/echo_tui_nats_bridge.py` — bridge service (line 579: `subscribe(f"{NS}.{AGENT}.direct")`)
- `systemd/nova-tui-bridge@.service` — parameterized bridge template
- `swift-brane/README.md` — wasm64 build setup

### Deliverable

Write the architecture doc and stage + commit it. Reply here with confirmation and the doc path.

**Deadline:** Next pulse or when doc is committed.
