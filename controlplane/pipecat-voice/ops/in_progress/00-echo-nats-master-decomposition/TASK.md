# Echo NATS Master Decomposition

## Status

in_progress

## Goal

Convert the current Echo visible-NATS proof into a reliable Nova fleet transport path, then use that stable path to coordinate Paperclip fleet sync and UI/design extraction work.

## Workflow

1. Pick one task folder from `ops/to_do/`.
2. Move it to `ops/in_progress/` before changing code or services.
3. Do the work directly at system level.
4. Log every operational action in:
   - `ops/operations_history.md`
   - `ops/decisions.log`
5. On completion, write `completion_report.md` inside the task folder.
6. Move the task folder to `ops/completed/`.
7. Commit and push the exact work scope.
8. Pick the next task folder.

## Current Known-Good State

- Echo visible CLI runs from `/adapt/novas/active/echo`.
- Echo uses `openai-codex/gpt-5.4-mini`.
- Echo's fresh Codex token is in `/home/x/.hermes/profiles/echo/config.yaml` under `model.api_key`.
- Echo profile auth state is synchronized in `/home/x/.hermes/profiles/echo/auth.json`.
- `echo-tui-nats-bridge.service` owns:
  - `nova.echo.direct`
  - `nova.echo.meet`
  - `nova.echo.ping`
- `pipecat-hermes-agents.service` excludes Echo and owns the other profile-backed agents.
- Phone app messages can reach Echo through NATS and appear in the visible CLI.
- Current blocker: a new phone/NATS message can interrupt Echo while she is already waiting on a model response.

## Task Graph

Start with these in order:

1. `01-lock-current-state`
2. `02-echo-visible-bridge-serialization`
3. `03-echo-reply-capture-session-watcher`
4. `04-native-hermes-nats-adapter-spike`
5. `05-fleet-subject-sync-and-validation`
6. `06-phone-voice-path-integration`

Parallel or later:

- `07-paperclip-fleet-sync` can run after `01-lock-current-state`.
- `08-hermes-ui-design-extraction` can run after `01-lock-current-state`.
- `09-team-delegation-protocol` can run any time and should guide Vaeris, Tecton, Echo, Iris, and Skipper assignments.

## Revert Plan

If Echo transport breaks:

1. Stop native/experimental Echo adapters.
2. Ensure Echo remains excluded from `pipecat-hermes-agents.service`.
3. Restart the known temporary visible bridge:
   ```bash
   systemctl --user restart echo-tui-nats-bridge.service
   ```
4. Relaunch Echo visible CLI:
   ```bash
   DISPLAY=:0 gnome-terminal --title='Echo CLI' --working-directory=/adapt/novas/active/echo -- bash -lc 'exec /home/x/.local/bin/hermes -p echo --yolo -c'
   ```
5. Send one structured `nova.echo.direct` proof.
6. If model auth fails, verify:
   ```bash
   /home/x/.local/bin/hermes -p echo auth status openai-codex
   ```
7. Restore profile config/auth backups from `/home/x/.hermes/profiles/echo/*.bak.*` if needed.

## Completion Criteria

- Echo receives serialized NATS messages without interrupting active turns.
- NATS callers receive Echo's actual answer text, not only a delivery ack.
- Fleet NATS subjects have one owner each.
- Paperclip contains synced fleet docs/config inventory.
- UI/design extraction backlog exists as concrete task folders.
