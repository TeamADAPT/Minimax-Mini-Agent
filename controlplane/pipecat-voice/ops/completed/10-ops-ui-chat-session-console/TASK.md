# Ops UI Chat Session Console

## Status

completed

## Objective

Write an implementable platform spec for a NovaOps chat/session console adapted from the Hermes UI pattern inventory without copying source code from external candidates.

## Inputs

- `ops/hermes_ui_design_patterns.md`
- `ops/fleet_subject_matrix.md`
- `scripts/echo_tui_nats_bridge.py`
- `gateway.py`
- `ops/cx-pipe/ADMIN_GUIDE.md`

## Steps

1. Move this folder to `ops/in_progress/`.
2. Define the console information architecture.
3. Define the NATS send/reply state model and visible Echo session proof fields.
4. Define terminal handoff requirements for Echo and future novas.
5. Define acceptance tests and dogfood evidence.
6. Write `ops/ui_chat_session_console_spec.md`.
7. Write `completion_report.md`.
8. Move this folder to `ops/completed/`.
9. Commit and push.

## Acceptance

- Spec exists and references source patterns.
- Spec has actionable implementation slices.
- Spec rejects straight source copying.
- Spec includes test/QA requirements.
