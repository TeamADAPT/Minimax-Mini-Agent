# CommsOps Status

## 2026-05-31 17:21:48 - SIGNED_BY_AGENT

Task 37 is complete as a Rust/no-Python Swift Brane pilot:

- Added and verified the `swift-brane` workspace host/agent path.
- wasm64 `file_read` builds with nightly `build-std`.
- Installed `/usr/local/bin/swift-brane-agent` and
  `/usr/local/bin/swift-brane-host`.
- Deployed `swift-brane-agent.service`.
- Live NATS request/reply on `nova.crew.swift.invoke` returns file content.
- `SWIFT_BRANE_ROOT` confines file reads to the repo root.
- `/adapt/secrets/db.env` and traversal attempts were denied in live proofs.

## 2026-05-31 17:15:18 - SIGNED_BY_AGENT

Task 39 is complete as a Rust-owned crew consensus service:

- Added `rust/nova-crew-consensus`.
- Installed `/usr/local/bin/nova-crew-consensus`.
- Added and deployed `nova-crew-consensus.service`.
- Service is active on `nova.crew.consensus.propose` and
  `nova.crew.consensus.vote.*`.
- Resolution output publishes to `nova.crew.consensus.bind.<topic>`.
- Live systemd proofs passed:
  - `rust-systemd-bind-20260531` -> `BIND`.
  - `rust-systemd-timeout-20260531` -> `NO_QUORUM`.

## 2026-05-31 16:54:47 - SIGNED_BY_AGENT

Task 43 is complete as the Rust-owned provider-abstraction milestone:

- Added `rust/nova-voice-provider-core`.
- Added Rust provider trait/config model for Deepgram and xAI.
- Added `voice_provider_plan` CLI and `/api/voice/provider-plan` gateway
  endpoint.
- Added guarded xAI TTS probe binary.
- Deepgram route planning is live and default-safe.
- xAI route planning requires explicit `allow_experimental=true`.
- The live `/ws/voice` path remains Deepgram; no default audio route was moved.

## 2026-05-31 10:11:43 - SIGNED_BY_AGENT

Task 44 is complete. Canonical transcript-memory handoff is live:

- New schema: `comms.turn.v1`.
- Durable handoff: `/adapt/novas/active/_shared/turn_events.jsonl`.
- API handoff: `/api/turn-events?limit=N`.
- Gateway emits direct inbound user turns, direct outbound agent turns, room
  user/agent/moderator turns, and timeout/error rows.
- Direct Rust route proof against `commscanary` wrote two service-owned rows
  with route subject, delivery, bridge event id, and Hermes session id.
- Backfill normalized 194 existing CX Pipe room-history rows; canonical file
  now contains 196 rows after proof plus backfill.
- `pipecat-voice.service` keeps `ProtectSystem=strict` and has scoped write
  access only to the repo and `/adapt/novas/active/_shared`.

## 2026-05-31 09:57:08 - SIGNED_BY_AGENT

Task 45 is complete. The gateway now exposes `/activity`, `/api/activity`,
and `/api/tui-mirror/{name}` for operator-grade CommsOps observability:

- Summary cards report roster, Tier 1 coverage, online agents, visible CLIs,
  NATS subject count, and room history volume.
- Charts cover roster status, Tier 1 coverage, NATS subject shape, session
  activity, message volume, room events, and task lanes.
- Drill-down tables show Tier 1 lead roster/profile status and per-agent
  daemon/CLI/session/message state.
- Agent rows expose bounded live log tails without exposing secrets.
- Desktop and mobile browser checks passed against the live service.

## 2026-05-31 09:35:13 - SIGNED_BY_AGENT

Phone/browser `auto` route cutover is complete for Iris, Echo, and Tecton:

- Auto direct sends route to `nova.<agent>.rust.direct`.
- `/v1/chat/completions` proofs passed for all three.
- Activity history records route metadata and Hermes session ids.
- Voice chunks are denoised before reaching callers.
- `pipecat-voice.service` is active on `127.0.0.1:18085`.

## 2026-05-31 09:22:58 - SIGNED_BY_AGENT

Task 42 is complete. Native NATS-to-Hermes API-session delivery is promoted for
the runtime-scoped Rust route, with Iris, Echo, Tecton, and `commscanary`
proven through streamed chunks, route metadata, and persisted Hermes sessions.
Task 48 now owns phone/browser `auto` route cutover.

## 2026-05-31 09:22:19 - SIGNED_BY_AGENT

Iris, Echo, and Tecton are repaired on the Rust API-session route:

- Local default provider/model moved to NVIDIA NIM
  `qwen/qwen3.5-397b-a17b`.
- CLI, API sync, API stream, and live Rust NATS proofs passed for all three.
- Rust final chunks include route metadata.
- Rust voice chunks now denoise signature/CWD/date tails before reaching route
  consumers.
- Rollback backup: `config.yaml.bak.commsops47.20260531T161406Z` in each
  affected profile directory.

## 2026-05-31 09:11:23 - SIGNED_BY_AGENT

Rust runtime route proof promoted for `commscanary`:

- `nova-hermes-nats-bridge.service` restarted with the release binary.
- Rust bridge roster now includes `commscanary`.
- Live `nova.commscanary.rust.direct` returned streamed chunks.
- Final reply chunk carries route metadata: event id, agent, sender, runtime,
  channel, delivery path, and Hermes session id.
- Hermes API session `nats_commscanary_codex` contains user and assistant rows.

Task 47 now owns user-facing provider repair before Iris, Echo, Tecton, Vaeris,
Veyra, Zap, or Vox are promoted onto this path.

## 2026-05-31 09:01:31 - SIGNED_BY_AGENT

Provider health gate completed. `commscanary` is now the non-user-facing
CommsOps proof lane:

- Gateway: `hermes-gateway-commscanary.service`.
- API bind: `127.0.0.1:8675`.
- Provider/model: NVIDIA NIM `qwen/qwen3.5-397b-a17b`.
- Hermes CLI proof returned `COMMSCANARY OK`.
- API sync proof returned `API SYNC OK`.
- API stream proof emitted assistant content.
- Session persistence contains both user and assistant rows.

Current provider blockers are account/quota related: DeepSeek balance,
OpenRouter credits, Gemini quota, xAI account/credit authorization, and
Cerebras tested-model availability.

## 2026-05-31 08:13:16 - SIGNED_BY_AGENT

## Current Posture

- `nats-server.service`: active.
- `pipecat-voice.service`: active.
- `nova-hermes-nats-bridge.service`: active.
- `pipecat-hermes-agents.service`: active.
- `pipecat-hermes-fresh-agents.service`: active.
- `echo-tui-nats-bridge.service`: active.
- `iris-tui-nats-bridge.service`: inactive at inspection time.
- `veyra-tui-nats-bridge.service`: inactive at inspection time.

## Canonical Route Model

Live CommsOps routing uses runtime-scoped subjects:

```text
nova.<agent>.<runtime>.direct
nova.<agent>.<runtime>.meet
nova.<agent>.<runtime>.ping
```

Supported runtime labels:

- `tui`: visible CLI/TUI session bridge.
- `hermes`: profile-backed Hermes daemon bridge.
- `fresh`: fresh Hermes turn/session bridge.
- `rust`: Rust bridge path.
- `auto`: gateway-selected default from roster and route config.

Legacy non-runtime subjects are no longer the preferred owner path for new work.

## Working Assets

- Rust bridge crate: `rust/nova-hermes-nats-bridge`.
- Native Hermes NATS adapter proof: `ops/native_nats_adapter_spike.md`.
- Phone/browser client: `client/index.html`, `client/app.js`,
  `client/blackline.css`.
- Gateway: `gateway.py`.
- Runtime service templates: `systemd/`.
- Existing transcript surfaces: room history, session-state API, Hermes
  `state.db`, and ops runtime snapshots.

## Known Risks

- Visible TUI routes still depend on desktop/window behavior and timing.
- Hermes API delivery must be proven against exact session semantics before it
  can replace visible session routing.
- Native Hermes NATS adapter proof exists, but promotion requires a current
  Rust-first implementation path and rollback gate.
- xAI voice exists as an external provider surface, but its auth and latency
  behavior have not been proven inside CX Pipe.
- Transcript ingestion needs one canonical event schema before memory and
  analytics consume it at scale.
- Existing repository state is dirty; CommsOps commits must stay narrowly scoped
  to owned artifacts.

## Immediate Promotion Gates

1. Prove NATS-to-Hermes internal session push on Echo, Iris, and Tecton without
   X11/TUI typing.
2. Prove whether Hermes API server calls can append to an existing visible
   session or only create gateway/API sessions.
3. Convert the route proof into a Rust-native service or Hermes plugin path.
4. Add provider-neutral voice abstraction for Deepgram and xAI voice.
5. Emit canonical transcript events for every voice/text turn.
6. Expose route latency, route owner, transcript status, and provider status on
   the activity dashboard.

## 2026-05-31 08:39:08 - SIGNED_BY_AGENT

Task 42 update:

- Hermes API server has the session endpoints needed for native push.
- A local Hermes API-server bug was patched: duplicate `model` argument during
  API agent creation.
- Rust bridge now attempts API session delivery before subprocess fallback.
- Promotion remains blocked until one provider-backed proof returns assistant
  content and persists both user and assistant rows.
