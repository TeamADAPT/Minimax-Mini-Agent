# Rust Hermes NATS Bridge

## 2026-05-18 20:51:58 — SIGNED_BY_AGENT

## Outcome

Created the first Rust-native Nova Hermes NATS bridge under:

`controlplane/pipecat-voice/rust/nova-hermes-nats-bridge`

The bridge is a sidecar subject owner. It does not replace the visible Echo bridge by default.

## Default Subjects

Safe Echo test defaults:

- direct: `nova.echo.native`
- meet: `nova.echo.native.meet`
- ping: `nova.echo.native.ping`
- logs: `nova.logs.echo`

The systemd template overrides direct/ping to the same safe native subject family. Promotion to `nova.echo.direct` requires explicit env override and stopping `echo-tui-nats-bridge.service`.

## Implemented

- Rust `async-nats` connection with env-supplied credentials.
- Direct, meet, and ping subscribers.
- Bounded per-agent work queue.
- Serialized Hermes invocation via worker loop.
- `reply_to` chunk streaming using the same `{"chunk": "...", "final": ...}` contract as the Python bridge.
- Trace publishing to `nova.logs.<agent>`.
- Safe systemd template: `systemd/nova-hermes-nats-bridge@.service`.
- `.gitignore` excludes Cargo `target/`.

## L6 NATS Pattern Cleanup

Updated local L6 NATS example files so the helper accepts runtime `NatsConfig` instead of hardcoded NATS credentials:

- `/adapt/platform/novaops/toolops/memory/l6-store-host/src/nats.rs`
- `/adapt/platform/novaops/toolops/memory/l6-store-host/src/lib.rs`
- `/adapt/platform/novaops/toolops/memory/l6-store-host/src/main.rs`

Important: `l6-store-host` is currently an untracked directory inside the nested `/adapt/platform/novaops/toolops/memory` repository, so that cleanup is a local workspace fix unless that repo later starts tracking the L6 host package.

## Verification

Commands run:

- `cargo check`
- `cargo clippy -- -D warnings`
- `cargo build --release`
- `cargo test`

Isolated NATS smoke used `/bin/echo` as `--hermes-bin` to avoid model spend and avoid touching the live Echo route.

Smoke subjects:

- direct: `nova.echo.native.test`
- meet: `nova.echo.native.test.meet`
- ping: `nova.echo.native.test.ping`

Smoke evidence:

- ping response: `pong:echo:rust`
- direct event id: `rust-bridge-smoke-3dbcec33`
- direct reply returned through `reply_to` and contained the Rust bridge prompt marker.

The temporary smoke bridge process was stopped after verification.

## Promotion Path

1. Build release binary:
   ```bash
   cargo build --release
   ```
2. Install or symlink `systemd/nova-hermes-nats-bridge@.service` into the user systemd unit path.
3. Start Echo in native test mode first:
   ```bash
   systemctl --user start nova-hermes-nats-bridge@echo.service
   ```
4. Verify:
   - `nova.echo.native.ping`
   - `nova.echo.native`
   - `reply_to` chunks
   - `nova.logs.echo`
5. Promote only after proof:
   - stop `echo-tui-nats-bridge.service`;
   - set `NOVA_DIRECT_SUBJECT=nova.echo.direct`;
   - set `NOVA_PING_SUBJECT=nova.echo.ping`;
   - restart the Rust bridge;
   - verify one-owner route state.

## Rollback

```bash
systemctl --user stop nova-hermes-nats-bridge@echo.service
systemctl --user restart echo-tui-nats-bridge.service
```

Then verify:

```text
nova.echo.ping -> pong:echo:tui
```

**— SIGNED_BY_AGENT**
