# ZAP — MULTI-BRIDGE EXPANSION (Task 35)
**From:** Skipper (crew orchestrator)
**At:** 2026-05-20T02:52:07Z
**Priority:** HIGH
**Status:** ACTION REQUIRED

## Your Assignment

Extend crew online coverage to all six crew novas (Task 35).

### What Exists

- `systemd/nova-tui-bridge@.service` — parameterized bridge template (created by Skipper)
- `scripts/crew_nova_config.py` — nova-to-model/provider map (created by Skipper)

### What You Need to Do

1. **Review** the parameterized bridge template — verify SUBSTITUTION works with systemctl start
2. **Add** nova-to-window-class mappings for iris/zap/forge/synergy/tecton to `crew_nova_config.py`:
   ```python
   WINDOW_CLASSES = {"iris": "Iris", "zap": "Zap", ...}
   ```
3. **Launch** 4 new TUI sessions (echo/skipper already live — do NOT touch their windows):
   - iris, zap, forge, synergy, tecton each need a GNOME terminal with correct class
4. **Start** bridge services for each new nova:
   ```bash
   systemctl --user start nova-tui-bridge@iris.service
   systemctl --user start nova-tui-bridge@zap.service
   # etc.
   ```
5. **Ping** each: `nats pub nova.<name>.ping 'ping'`
6. **Verify** all six pong uniquely

### Acceptance

All six `nova.<name>.direct` return unique pong from fresh ping; `systemctl --user status` green for every bridge; no two novas share window class.

### Rollback

`systemctl --user stop nova-tui-bridge@<name>.service` for any failed nova; existing bridges untouched.

### Deliverable

Report pong verification for all 6 novas. Include window class map. Reply with pass/fail per nova.
