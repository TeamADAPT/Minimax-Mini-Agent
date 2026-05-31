# CommsOps Status

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
