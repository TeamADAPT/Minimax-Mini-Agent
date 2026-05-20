# Zap Task: TUI-NATS Bridge Verification

## Objective
Verify all tui-nats-bridge systemd services are healthy and routing correctly.

## Steps
1. Run `systemctl --user list-units --all "*tui-nats*"`
2. For each service, check: Active, Sub, and last 10 log lines
3. Identify any degraded or inactive bridges
4. Output health report to ops/BRIDGE_STATUS.md

## Acceptance
- ops/BRIDGE_STATUS.md with one line per service: name | active | status | notes
- Blockers: any FAILED services
