# Native Hermes NATS Adapter Spike

## 2026-05-18 15:23:53 — SIGNED_BY_AGENT

The native path is implemented as a Hermes platform plugin under:

- `/data/vast/home/x/.hermes/hermes-agent/plugins/platforms/nats/__init__.py`
- `/data/vast/home/x/.hermes/hermes-agent/plugins/platforms/nats/adapter.py`
- `/data/vast/home/x/.hermes/hermes-agent/plugins/platforms/nats/plugin.yaml`

This follows Hermes' documented plugin adapter path instead of adding a hard-coded
core adapter in `gateway/platforms/nats.py`. The plugin still runs inside the
Hermes gateway runtime, uses the normal platform adapter interface, and avoids
X11/TUI input.

Current Hermes commit:

- `b256666f5 fix(nats-adapter): gate env enablement and trace replies — SIGNED_BY_AGENT`

Push status:

- Local commit succeeded.
- Push to `https://github.com/NousResearch/hermes-agent.git` failed with HTTP `403`
  because the available GitHub account does not have write permission to that
  upstream.

Adapter behavior:

- Env-gated enablement via `HERMES_NATS_ENABLED=true` or `NATS_PLATFORM_ENABLED=true`.
- Agent/subject selection via `NATS_AGENT_NAME`, `SUBJECT_NS`, and `NATS_SUBJECTS`.
- Optional duplicate-responder protection via `NATS_QUEUE_GROUP`.
- Access control via `NATS_ALLOWED_USERS` or `NATS_ALLOW_ALL_USERS`.
- Uses the existing NATS URL from env or `/adapt/secrets/db.env`.
- Subscribes directly to configured subjects such as `nova.echo.direct`.
- Converts JSON NATS envelopes into Hermes `MessageEvent` objects.
- Uses the sender as stable gateway `chat_id` for session continuity.
- Publishes reply chunks and terminal final messages to the incoming `reply_to`.
- Publishes trace events to `nova.logs.<agent>`:
  - `inbound`
  - `chunk`
  - `completed`

Native proof:

- Temporarily stopped `echo-tui-nats-bridge.service`.
- Ran Echo gateway from `/adapt/novas/active/echo` with:
  - `HERMES_NATS_ENABLED=true`
  - `NATS_AGENT_NAME=echo`
  - `NATS_SUBJECTS=nova.echo.direct`
  - `NATS_ALLOW_ALL_USERS=true`
  - `NATS_FINALIZE_IDLE_SECONDS=30`
- Sent structured proof `native-proof-cb4c0574d2` to `nova.echo.direct`.
- Received native NATS reply containing `NATIVE NATS LOG OK`.
- Captured log events from `nova.logs.echo`: `inbound`, `chunk`, `chunk`, `chunk`, `completed`.
- Stopped the temporary native gateway process.
- Restored `echo-tui-nats-bridge.service`; `nova.echo.ping` returned `pong:echo:tui`.

Known issue:

- Echo's `openai-codex/gpt-5.4-mini` gateway call currently emits `HTTP 401`
  provider status before falling back to NVIDIA `minimax-m2.7`. The native NATS
  adapter still delivers the fallback answer correctly, but Echo's OpenAI/Codex
  gateway credentials need separate cleanup before making native Echo the default.

Rollback:

1. Keep `HERMES_NATS_ENABLED` unset or false for Echo.
2. Ensure no manual Echo gateway process is running for NATS.
3. Start the visible bridge:
   `systemctl --user start echo-tui-nats-bridge.service`
4. Confirm ownership:
   `nova.echo.ping -> pong:echo:tui`
