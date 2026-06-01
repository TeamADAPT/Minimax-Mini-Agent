# Crew Online Six-Way Status

## 2026-05-31 17:39:07 — SIGNED_BY_AGENT

Task 35 is partially advanced and remains open.

## Completed

- Replaced ad hoc crew bridge ownership with user-systemd template instances:
  - `nova-tui-bridge@echo.service`
  - `nova-tui-bridge@skipper.service`
  - `nova-tui-bridge@iris.service`
  - `nova-tui-bridge@zap.service`
  - `nova-tui-bridge@forge.service`
  - `nova-tui-bridge@synergy.service`
  - `nova-tui-bridge@tecton.service`
- Updated `systemd/nova-tui-bridge@.service` to source shared env files, use
  `BRIDGE_RUNTIME=tui`, and enable legacy `nova.<agent>.*` subjects.
- Updated `scripts/crew_nova_config.py` with crew order, model/provider posture,
  and expected window names.
- Created missing `/adapt/novas/active/zap` working directory.

## Proof

All seven bridge instances are active.

Both legacy and runtime ping subjects return unique pongs:

```text
echo legacy=pong:echo:tui runtime=pong:echo:tui
skipper legacy=pong:skipper:tui runtime=pong:skipper:tui
iris legacy=pong:iris:tui runtime=pong:iris:tui
zap legacy=pong:zap:tui runtime=pong:zap:tui
forge legacy=pong:forge:tui runtime=pong:forge:tui
synergy legacy=pong:synergy:tui runtime=pong:synergy:tui
tecton legacy=pong:tecton:tui runtime=pong:tecton:tui
```

## Open Blocker

Fresh visible Hermes CLI sessions launched in GNOME Terminal and xterm, but the
new Hermes processes exited after startup on this desktop. Adding
`TERM=xterm-256color` allowed a longer startup window but did not keep the new
sessions alive past the verification gate. The pre-existing Tecton visible CLI
process remains active with cwd `/adapt/novas/active/tecton`.

Task 35 should not be marked complete until durable visible windows are proven
for the crew, not just bridge ping coverage.
