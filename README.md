# NovaOps — ADAPT Autonomous Agent Platform

**TeamADAPT** | Bleeding-edge AIML R&D | [Charter](protocols/NovaOps_Charter.md) | [Protocols](protocols/TeamADAPT_Protocols.md)

---

## What This Is

NovaOps is the infrastructure layer for deploying, orchestrating, and maintaining autonomous Nova agents within the TeamADAPT ecosystem. It provides identity continuity, tool management, cross-agent communication, and the control plane through which agents and human operators interact.

---

## System Requirements

- Linux (systemd)
- Python 3.10+ (system-wide, no venv)
- Node.js 20+ (for Paperclip control plane)
- NATS Server (`localhost:18020`)
- Qdrant (`localhost:6333`), Redis, MongoDB, Neo4j, ClickHouse
- Temporal (`localhost:8233`)
- Local LLM endpoint (`localhost:8888/v1`)
- No Docker. All services managed via systemd.

---

## Directory Structure

```
novaops/
├── controlplane/           Paperclip (AI company OS) + Pipecat
│   └── paperclip/          13 ADAPT autonomous plugins (see below)
├── nova_framework/         Core agent runtime — NATS event hub, bridge service
├── novas/                  Named Nova agent instances (nova_001–010 + specialists)
├── toolops/                70+ MCP servers, API, DB, voice, UI, memory layers
├── novamem/                Memory backend — Qdrant + MongoDB + Redis + Weaviate
├── novamon/                Observability — LangFuse + LangSmith
├── polyglot-agents/        Multi-language agent support
├── frameworks/             15 framework integrations (autogen, crewai, camel, etc.)
├── continuity/             Cross-session continuity, comms, novathreads
├── x1-wasm_rust/           Rust/WASM component
├── core_infra/             NATS client
├── nova_core/              Nova core runtime
├── nova_infra/             Secrets + realtime comms (restricted access)
├── novainfra/              Nova infrastructure layer
├── protocols/              Governance: charter, protocols, onboarding
├── ops/                    Task workflow + operational logs
│   ├── to_do/
│   ├── in_progress/
│   └── completed/
├── mini_agent/             Mini Agent — base agent implementation (MiniMax M2 / Anthropic-compatible)
├── scripts/                Utility scripts
├── tests/                  Test suite
└── docs/                   Development and production guides
```

---

## Paperclip Plugins (Control Plane)

All 13 ADAPT autonomous plugins run inside `paperclip.service` (systemd):

| Plugin | Function |
|---|---|
| Command Center | CEO dashboard — agent chat, widgets, mobile controls |
| Conductor | Agent instruction editor, AI-assisted improvement, revision history |
| Nexus | Multi-agent group chat, collaboration rooms, debate arena |
| Bridge | GitHub / Slack / Discord / Jira — bidirectional sync |
| Chain | Temporal workflow orchestration — durable agent pipelines |
| Incident Commander | War room — declare incidents, coordinate response, post-mortem |
| Triage | Semantic issue intake, LLM classification, priority routing |
| Ops | Dead Man's Switch, SLA enforcer, board reports |
| Observer | NATS stream monitor + ClickHouse metrics dashboard |
| OKR | Neo4j-backed objectives and key results, agent alignment |
| Memory | Semantic decision log, Qdrant vector search, RAG retrieval |
| Vault | Prompt library — store, tag, version, semantic search |
| Chat | LLM-powered brainstorming interface |

---

## Service Management

All services run via systemd. Key units:

```bash
systemctl status paperclip          # Paperclip control plane (port 3100)
systemctl status nats               # NATS event bus (port 18020)
```

---

## Task Workflow

```
ops/to_do/  →  ops/in_progress/  →  ops/completed/
```

All actions logged in `ops/operations_history.md` and `ops/decisions.log` — timestamped, signed by agent.

---

## Ops Discipline

Every operational action must be logged:
- `ops/operations_history.md` — reverse-chronological, newest first
- `ops/decisions.log` — all decisions with rationale

Entry format:
```
## YYYY-MM-DD HH:MM:SS — AGENT_ID
Description of action or decision.
```

---

## Governance

- [NovaOps Charter](protocols/NovaOps_Charter.md)
- [TeamADAPT Protocols](protocols/TeamADAPT_Protocols.md)
- [Developer Onboarding](protocols/NEW_DEVELOPER_ONBOARDING_REALTITY_CHECK.md)

---

## License

MIT
