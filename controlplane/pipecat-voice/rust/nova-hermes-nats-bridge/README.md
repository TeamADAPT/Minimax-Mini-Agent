# Nova Hermes NATS Bridge

Rust NATS subject owner for Hermes-backed Nova agents.

## Default Safe Mode

The default Echo subjects are intentionally test-only:

- direct: `nova.echo.native`
- meet: `nova.echo.native.meet`
- ping: `nova.echo.native.ping`
- logs: `nova.logs.echo`

This avoids stealing `nova.echo.direct` from the current visible Echo bridge.

## Run Locally

```bash
set -a
. /adapt/secrets/db.env
set +a
cargo run --release -- \
  --agent echo \
  --direct-subject nova.echo.native \
  --ping-subject nova.echo.native.ping
```

## Promote Echo Later

Only after test-subject proof passes:

1. Stop `echo-tui-nats-bridge.service`.
2. Start this bridge with `NOVA_DIRECT_SUBJECT=nova.echo.direct`.
3. Verify `nova.echo.ping`, `nova.echo.direct`, `reply_to`, and `nova.logs.echo`.
4. Roll back by stopping this bridge and restarting `echo-tui-nats-bridge.service`.

## Secret Boundary

Do not commit NATS credentials. Use `/adapt/secrets/db.env` from systemd or shell environment.
