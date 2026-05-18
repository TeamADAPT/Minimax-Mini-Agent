# Native Hermes NATS Adapter Spike

## Status

to_do

## Objective

Replace the temporary X11 visible bridge with a native Hermes gateway platform adapter for NATS.

## Files To Inspect

- `/data/vast/home/x/.hermes/hermes-agent/gateway/platforms/`
- `/data/vast/home/x/.hermes/hermes-agent/gateway/run.py`
- `/data/vast/home/x/.hermes/hermes-agent/gateway/config.py`
- `/data/vast/home/x/.hermes/hermes-agent/gateway/platforms/ADDING_A_PLATFORM.md`
- Echo profile config under `/home/x/.hermes/profiles/echo/config.yaml`

## Steps

1. Move this folder to `ops/in_progress/`.
2. Inspect existing Hermes platform adapter patterns.
3. Write a short design note for `gateway/platforms/nats.py`.
4. Implement minimal NATS subscribe/connect loop.
5. Convert structured NATS envelopes into Hermes message events.
6. Preserve `reply_to`, sender, subject, event id, and channel metadata.
7. Publish final replies to `reply_to`.
8. Publish trace events to `nova.logs.echo`.
9. Run with Echo only.
10. Prove no duplicate responder owns `nova.echo.direct`.
11. Write `completion_report.md`.
12. Move this folder to `ops/completed/`.
13. Commit and push.

## Acceptance

- Echo gateway can own `nova.echo.direct` natively.
- A NATS request receives actual answer text.
- No X11 input is required for the native path.
- Temporary bridge remains available as rollback.

## Revert

Disable `platforms.nats` in Echo config, stop/restart Echo gateway, and restore `echo-tui-nats-bridge.service` as subject owner.

