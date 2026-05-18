# UI Analytics And Logs Spec

## 2026-05-18 15:39:44 — SIGNED_BY_AGENT

## Purpose

Build a NovaOps observability surface for NATS delivery, agent replies, systemd services, gateway health, provider/model latency, and task operations. The design adapts EKKO's analytics/logging ideas but uses live NovaOps sources and redacts sensitive data by default.

## Source Patterns

- From `EKKOLearnAI/hermes-web-ui`: usage/cost trends, model distribution, log filters, structured HTTP log highlighting, terminal diagnostics, gateway/profile panels.
- From `nesquena/hermes-webui`: compact activity metadata, structured request logging, session recovery/status surfaces.
- From NovaOps runtime: `nova.logs.<name>`, bridge trace events, service units, operations logs, NATS ping matrix, CX pipe gateway health.

## Primary Views

### Fleet Health

- Service cards:
  - `nats-server.service`
  - `pipecat-voice.service`
  - `pipecat-hermes-agents.service`
  - `echo-tui-nats-bridge.service`
  - Switch process owner
- Per-nova ping status from `nova.<name>.ping`.
- Subject owner matrix from `ops/fleet_subject_matrix.md` and live ping probes.
- Drift indicator when a subject has zero owners, duplicate owners, or an unexpected response label.

### NATS Trace Timeline

For each event id:

- inbound received;
- queued position;
- visible typed or native dispatch;
- model started;
- model completed;
- assistant reply captured;
- reply streamed to caller;
- timeout/error/fallback.

The trace timeline must distinguish transport success from answer success.

### Logs

Sources:

- `journalctl --user -u echo-tui-nats-bridge.service`
- `journalctl --user -u pipecat-hermes-agents.service`
- `journalctl -u pipecat-voice.service`
- `journalctl -u nats-server.service`
- `nova.logs.<name>` subscription stream
- `ops/operations_history.md`
- `ops/decisions.log`

Filters:

- nova name;
- service/unit;
- event id;
- severity;
- time range;
- keyword;
- task id;
- provider/model.

### Provider And Response Health

Metrics:

- model/provider used;
- request duration;
- retry count;
- configured timeout;
- fallback event;
- error class;
- token usage and cost if present in structured payloads;
- cache status if present.

Any missing metric should show `unknown`, not infer values from prose.

## Redaction Rules

Never render:

- API keys;
- bearer tokens;
- raw `NATS_URL` with password;
- profile `config.yaml` secrets;
- `.env` values;
- auth cookies;
- full database connection strings.

Redact with deterministic labels such as `[redacted:nats-url]` or `[redacted:provider-key]` so repeated events remain correlatable without exposing values.

## Data Contracts

### Trace Event

```json
{
  "event_id": "string",
  "nova": "echo",
  "stage": "inbound|queued|typed|completed|reply_captured|timeout|error",
  "timestamp": 0,
  "service": "echo-tui-nats-bridge.service",
  "detail": {},
  "redacted": true
}
```

### Service Snapshot

```json
{
  "unit": "string",
  "active": true,
  "pid": 0,
  "owner": "system|user|process",
  "last_checked_at": 0
}
```

## Implementation Slices

1. Redaction library and fixtures for logs/env/profile snippets.
2. Service snapshot collector.
3. NATS ping and trace collector.
4. Log query adapter for journal and ops docs.
5. Dashboard UI with fleet health, trace timeline, and filtered log table.
6. Exportable dogfood report bundle with screenshots and event ids.

## Tests And QA

- Unit tests for redaction coverage and deterministic labels.
- Unit tests for trace stage ordering.
- Integration test against Echo bridge trace events.
- Fixture tests for journal parsing and malformed payloads.
- Dogfood QA with a successful Echo turn, an induced timeout fixture, and a provider-error fixture.

## Boundaries

- Do not store or expose raw secrets.
- Do not require Docker or a separate analytics database for the first pass.
- Do not copy EKKO Vue/Koa code; only reuse the analytics concepts.

**— SIGNED_BY_AGENT**
