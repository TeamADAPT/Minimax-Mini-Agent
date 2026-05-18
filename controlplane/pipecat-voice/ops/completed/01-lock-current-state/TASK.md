# Lock Current Echo NATS State

## Status

completed

## Objective

Capture and prove the current known-good Echo visible NATS path before changing bridge behavior.

## Files And Systems

- Read: `/home/x/.hermes/profiles/echo/config.yaml`
- Read: `/home/x/.hermes/profiles/echo/auth.json`
- Read: `/home/x/.config/systemd/user/echo-tui-nats-bridge.service`
- Read: `/home/x/.config/systemd/user/pipecat-hermes-agents.service`
- Update: `ops/operations_history.md`
- Update: `ops/decisions.log`
- Create: `completion_report.md`

## Steps

1. Move this folder to `ops/in_progress/`.
2. Check `nats-server.service`, `pipecat-voice.service`, `pipecat-hermes-agents.service`, and `echo-tui-nats-bridge.service`.
3. Verify Echo visible CLI process and cwd with `/proc/<pid>/cwd`.
4. Send one structured `nova.echo.direct` proof.
5. Capture a screenshot of Echo CLI.
6. Confirm there is no `HTTP 401`, model fallback, or duplicate responder.
7. Write a concise current-state report.
8. Write `completion_report.md`.
9. Move this folder to `ops/completed/`.
10. Commit and push.

## Acceptance

- Echo visible CLI answers one NATS proof on `gpt-5.4-mini`.
- The proof appears in the visible terminal.
- Logs show the bridge delivered to Echo.
- The report names every active service and owner.
