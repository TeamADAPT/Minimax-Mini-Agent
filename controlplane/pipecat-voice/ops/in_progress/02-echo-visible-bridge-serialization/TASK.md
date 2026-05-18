# Echo Visible Bridge Serialization

## Status

in_progress

## Objective

Prevent phone/NATS messages from interrupting Echo while she is already waiting on a model response.

## Files

- Modify: `scripts/echo_tui_nats_bridge.py`
- May modify: `/home/x/.config/systemd/user/echo-tui-nats-bridge.service`
- Create or modify: `tests/` or `scripts/` smoke helper
- Update: `ops/operations_history.md`
- Update: `ops/decisions.log`

## Steps

1. Move this folder to `ops/in_progress/`.
2. Read `scripts/echo_tui_nats_bridge.py`.
3. Identify the current lock/ack flow.
4. Add explicit busy state around visible delivery and model wait.
5. While busy, either queue messages FIFO or publish a structured busy response. Prefer FIFO if simple and bounded.
6. Emit `nova.logs.echo` events for `inbound`, `queued`, `typed`, `completed`, `busy_rejected`, and `timeout`.
7. Add a smoke helper that sends two messages quickly and proves the second does not interrupt the first.
8. Restart `echo-tui-nats-bridge.service`.
9. Run smoke proof and screenshot Echo CLI.
10. Write `completion_report.md`.
11. Move this folder to `ops/completed/`.
12. Commit and push.

## Acceptance

- Two quick phone/NATS sends do not show `Interrupted during API call`.
- Echo answers the first turn before the second is delivered, or the second gets a clear busy response.
- Bridge logs show deterministic state transitions.

## Revert

Restore the previous bridge file from git or from a timestamped backup, then:

```bash
python3 -m py_compile scripts/echo_tui_nats_bridge.py
systemctl --user restart echo-tui-nats-bridge.service
```
