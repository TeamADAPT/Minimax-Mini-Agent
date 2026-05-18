# Ops UI Analytics And Logs

## Status

completed

## Objective

Write an implementable platform spec for analytics and log inspection adapted from Hermes Web UI references and the current NovaOps NATS/systemd runtime.

## Inputs

- `ops/hermes_ui_design_patterns.md`
- `ops/fleet_subject_matrix.md`
- `ops/native_nats_adapter_spike.md`
- `scripts/echo_tui_nats_bridge.py`
- systemd unit names recorded in ops docs

## Steps

1. Move this folder to `ops/in_progress/`.
2. Define the analytics data sources and redaction rules.
3. Define NATS trace/log timelines and service health widgets.
4. Define model/provider latency, retry, timeout, and fallback fields.
5. Define acceptance tests and log fixtures.
6. Write `ops/ui_analytics_logs_spec.md`.
7. Write `completion_report.md`.
8. Move this folder to `ops/completed/`.
9. Commit and push.

## Acceptance

- Spec exists and maps each surface to a live data source.
- Spec includes redaction requirements.
- Spec includes test/QA requirements.
- Spec does not depend on copying external UI code.
