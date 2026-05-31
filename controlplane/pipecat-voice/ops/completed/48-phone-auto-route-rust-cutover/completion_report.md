# Completion Report

## 2026-05-31 09:35:13 — SIGNED_BY_AGENT

Completed `48-phone-auto-route-rust-cutover`.

## Result

- Phone/browser `runtime=auto` resolves repaired Iris, Echo, and Tecton routes
  to Rust.
- Explicit runtime selection remains available, with a visible Rust runtime
  button added to the mobile control surface.
- Gateway direct turns now persist route metadata to room/activity history.
- Rust bridge accepts both numeric and ISO-8601 string NATS timestamps.
- Rust bridge strips non-ASCII visual noise from spoken chunks.

## Proofs

- Iris phone auto:
  - Endpoint: `/v1/chat/completions?peer=iris&channel=direct&runtime=auto`
  - Subject: `nova.iris.rust.direct`
  - Route metadata delivery: `api_session`
  - Hermes session: `nats_iris_chase`
  - Clean spoken output: `PHONE CLEAN OK.`
- Echo phone auto:
  - Endpoint: `/v1/chat/completions?peer=echo&channel=direct&runtime=auto`
  - Subject: `nova.echo.rust.direct`
  - Route metadata delivery: `api_session`
  - Hermes session: `nats_echo_chase`
  - Output: `ECHO PHONE AUTO OK`
- Tecton phone auto:
  - Endpoint: `/v1/chat/completions?peer=tecton&channel=direct&runtime=auto`
  - Subject: `nova.tecton.rust.direct`
  - Route metadata delivery: `api_session`
  - Hermes session: `nats_tecton_chase`
  - Output: `Tecton phone auto ok.`

## Verification

- `python3 -m py_compile gateway.py bot.py nats_agent.py`: passed.
- Rust bridge:
  - `cargo fmt --check`
  - `cargo check`
  - `cargo clippy -- -D warnings`
  - `cargo test`
  - `cargo build --release`
- Focused pytest still has pre-existing failures unrelated to this cutover:
  missing `_parse_tier1_tree`, missing `_activity_snapshot`, and missing
  `/api/tui-mirror/*` routes.

## Operations Notes

- `pipecat-voice.service` needed `sudo -n systemctl start` after a non-sudo
  systemctl call timed out through policy/auth handling.
- Live gateway is active on `127.0.0.1:18085`.
- `nova-hermes-nats-bridge.service` is active after release-binary restart.

## Rollback

Restore the previous `AGENT_RUNTIME_DEFAULTS` behavior in `gateway.py`, remove
the Rust runtime preference for Iris/Echo/Tecton, restart
`pipecat-voice.service`, and leave explicit runtime buttons available for
manual route selection.
