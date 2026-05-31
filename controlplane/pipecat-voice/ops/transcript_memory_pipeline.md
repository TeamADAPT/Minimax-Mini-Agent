# Transcript Memory Pipeline

## 2026-05-31 10:06:16 — SIGNED_BY_AGENT

Task 44 establishes canonical CommsOps turn events without replacing existing
room or Hermes session history.

## Current Sources

- `ops/cx-pipe/room_history.jsonl`: CX Pipe room/direct transcript rows used by
  the phone UI and activity page.
- `/adapt/novas/active/_shared/session_events.jsonl`: older Hermes session
  export rows with `agent`, `session_id`, `event_type`, `content`, `timestamp`,
  and `message_index`.
- Hermes profile `state.db` files: authoritative profile-local session/message
  stores.

These sources are useful but schema-incompatible. Memory and analytics should
consume canonical turn events instead of scraping UI text or profile databases.

## Canonical Handoff

Path:

```text
/adapt/novas/active/_shared/turn_events.jsonl
```

Schema:

```text
comms.turn.v1
```

Each row is one JSON object with:

- `event_id`, `turn_id`, `timestamp`, `created_at`
- `source`, `channel`, `direction`, `status`
- `actor.role`, `actor.name`
- `target.agent`, `target.agents`
- `route.runtime`, `route.subject`, `route.delivery`, `route.event_id`
- `session.id`, `session.provider`, `session.model`
- `room.id`
- `content.text`, `content.chars`, `content.redacted`
- `audio`
- `latency_ms`
- `failure`
- `source_event`
- `dedupe_key`

## Emission Rules

- Gateway room-history writes also emit canonical events.
- Direct typed/phone requests emit an inbound user event before NATS publish.
- Direct replies emit outbound agent events with route metadata when available.
- Empty or timed-out replies emit `status=timeout` and a failure object.
- NATS unavailable/no-target errors emit `status=error`.
- Secret-shaped values are redacted before serialization.
- Emission is best-effort and local append only; voice/NATS hot paths continue if
  the canonical writer fails.

## Consumer Contract

Memory and analytics consumers can tail `/adapt/novas/active/_shared/turn_events.jsonl`
or read `/api/turn-events?limit=N`. Consumers should dedupe on `dedupe_key` for
semantic turn identity and keep `event_id` as the immutable row id.

Backfill/replay:

```bash
scripts/backfill_turn_events.py --dry-run
scripts/backfill_turn_events.py --limit 200
```

The backfill helper reads existing CX Pipe room history, converts rows to
`comms.turn.v1`, skips duplicate `event_id` rows already present in the output
file, and reports `scanned`, `written`, `skipped`, and `bad` counts.

## Next Integration Points

- Temporal workflow: consume canonical rows and fan out to memory ingest,
  analytics enrichment, and audit compaction.
- RedPanda stream: mirror `comms.turn.v1` rows for replay and backfill.
- L6 memory: ingest selected `status=ok` user/agent text with route/session
  provenance attached.
