# 15 Overnight Crew Control Loops

## Objective

Install low-cost overnight control loops for the active crew so the control plane keeps collecting state, restarting drifted services, and exposing a current snapshot without burning model quota.

## Scope

- Add fleet heartbeat snapshots for `echo`, `skipper`, `testova`, and `latch`
- Add route-state snapshots for visible TUI and fallback posture
- Add pipecat/NATS/service health snapshots
- Add a watchdog that restarts timers and bridge services when they stop
- Manage everything through `systemd --user`

## Acceptance

- Snapshot scripts run successfully by hand
- User timers are enabled and started
- Runtime JSON snapshots land under `ops/runtime/`
- Watchdog can restart an inactive loop service or timer
