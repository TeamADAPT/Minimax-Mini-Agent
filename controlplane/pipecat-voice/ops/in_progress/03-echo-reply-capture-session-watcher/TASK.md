# Echo Reply Capture Session Watcher

## Status

in_progress

## Objective

Make NATS callers receive Echo's actual answer text instead of only a delivery/completion acknowledgement.

## Files

- Modify: `scripts/echo_tui_nats_bridge.py`
- Read: `/home/x/.hermes/profiles/echo/state.db`
- Create or modify: smoke test helper under `scripts/`
- Update: `ops/operations_history.md`
- Update: `ops/decisions.log`

## Steps

1. Move this folder to `ops/in_progress/`.
2. Inspect Echo session DB schema.
3. Identify how user and assistant messages are stored for active CLI sessions.
4. Stamp each NATS event id in the visible prompt.
5. Record session id and message count before delivery.
6. Wait for the new assistant message after the stamped user prompt.
7. Extract assistant response text.
8. Publish that response text to the incoming `reply_to`.
9. Publish trace events to `nova.logs.echo`.
10. Run one short proof and one long proof.
11. Write `completion_report.md`.
12. Move this folder to `ops/completed/`.
13. Commit and push.

## Acceptance

- NATS reply inbox receives Echo's actual answer text.
- The returned text matches the visible CLI answer.
- A timeout or provider failure returns a structured error, not a false success.

## Revert

Disable reply extraction and fall back to delivery/completion ack. Keep visible delivery working.
