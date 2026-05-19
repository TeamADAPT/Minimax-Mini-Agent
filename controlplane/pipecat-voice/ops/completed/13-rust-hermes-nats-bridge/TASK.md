# Rust Hermes NATS Bridge

## Status

completed

## Objective

Build the first Rust-native Nova Hermes NATS bridge path and remove the hardcoded NATS credential pattern from the L6 NATS example before promoting any Rust bridge into live Echo ownership.

## Steps

1. Move this folder to `ops/in_progress/`.
2. Patch the L6 NATS helper to accept runtime config instead of hardcoded credentials.
3. Scaffold `nova-hermes-nats-bridge` in Rust.
4. Implement NATS direct/meet/ping subjects, reply inbox streaming, bounded per-agent serialization, trace logs, and Hermes CLI invocation.
5. Add systemd and env examples that source `/adapt/secrets/db.env` without committing secrets.
6. Verify Rust formatting/build/tests where practical.
7. Write `completion_report.md`.
8. Move this folder to `ops/completed/`.
9. Commit and push.

## Acceptance

- No hardcoded NATS password remains in the L6 NATS helper.
- Rust bridge crate builds.
- Rust bridge has a safe test-subject path for Echo that does not take over `nova.echo.direct`.
- Ops docs explain rollback and promotion path.
