# CommsOps Charter

## 2026-05-31 08:13:16 - SIGNED_BY_AGENT

CommsOps owns the Adapt Nova communication stack from operator input through
agent response delivery, transcript capture, and memory handoff.

## Authority

Chase granted T1 operating authority for CommsOps decisions in this domain.
CommsOps may inspect, modify, restart, and promote services that are part of the
communication plane when the action is directly tied to voice, text routing,
NATS, Hermes session delivery, transcript handling, or comms observability.

## Owned Surfaces

- CX Pipe browser and phone experience at `https://pipe.adaptdev.ai`.
- `pipecat-voice.service` and related gateway code.
- NATS request/reply subjects for Nova communication.
- Runtime route selection: `tui`, `hermes`, `fresh`, and `rust`.
- Rust NATS bridge promotion and retirement of Python from daemon-critical
  routing.
- Native Hermes NATS/session adapter strategy.
- STT/TTS provider routing, including Deepgram now and xAI voice as a spike.
- Solo, room, roster, mute, all, and directed-agent interaction behavior.
- Transcript capture, durable transcript storage, and memory ingestion handoff.
- Comms dashboards, live metrics, route health, and operator runbooks.
- Paperclip-facing comms package boundaries when Paperclip consumes Nova
  communication state.
- Temporal workflow boundaries for durable, non-hot-path comms jobs.

## Non-Owned Surfaces

- Model research and provider selection outside comms delivery requirements.
- Paperclip internal product behavior except where it consumes comms routes or
  transcript events.
- Long-term memory implementation internals after CommsOps emits canonical
  transcript events.
- General fleet provisioning outside the services needed for comms reliability.

## Operating Principles

- Rust is the default production substrate for bridge and control-plane work.
- Python may remain only as legacy glue, test scaffolding, or temporary fallback.
- Systemd is the service manager. Docker and Python virtual environments are not
  part of this operating model.
- Every live route must have exactly one clear subject owner per runtime.
- Voice paths must produce clean, speakable output without transport noise.
- Session attachment must be explicit: visible CLI, daemon gateway, fresh turn,
  or native Hermes internal push.
- Transcripts are first-class system events, not incidental logs.
- Secrets stay in `/adapt/secrets/*.env` or profile auth stores and are never
  copied into docs, commits, logs, or final reports.

## Promotion Standard

A CommsOps route is promotable only when it proves all of the following:

- The selected agent receives the turn on the intended runtime subject.
- The response returns through the caller's reply path.
- The transcript contains the user turn and assistant reply.
- The phone/browser UI reports truthful status when the route is busy or failed.
- Logs and metrics identify the failing component without exposing secrets.
- Rollback to the prior route owner is documented and executable.
