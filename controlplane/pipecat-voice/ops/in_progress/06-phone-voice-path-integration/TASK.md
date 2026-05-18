# Phone Voice Path Integration

## Status

in_progress

## Objective

Make the phone app path to Echo deterministic and non-interrupting.

## Files

- Read/modify: `gateway.py`
- Read/modify: `.env`
- Read/modify: `roster.json`
- Read/modify: `ops/cx-pipe/`
- Update: `ops/operations_history.md`
- Update: `ops/decisions.log`

## Steps

1. Move this folder to `ops/in_progress/`.
2. Trace phone app request path into `gateway.py`.
3. Confirm Echo routes to `nova.echo.direct`.
4. Confirm the timeout is long enough for `gpt-5.4-mini`.
5. Ensure the UI/voice caller receives either actual Echo answer text or a truthful delivery/busy status.
6. Test from phone app.
7. Capture logs and screenshots.
8. Write `completion_report.md`.
9. Move this folder to `ops/completed/`.
10. Commit and push.

## Acceptance

- Phone app to Echo does not interrupt active Echo model calls.
- Phone app receives truthful status or actual answer.
- The visible Echo CLI proof aligns with NATS logs.
