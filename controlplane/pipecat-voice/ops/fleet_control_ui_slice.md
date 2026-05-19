# Fleet Control UI Slice

## 2026-05-18 21:41:12 — SIGNED_BY_AGENT

Added `client/fleet-control.html` as a static first slice served by the existing
gateway under `/static/fleet-control.html`.

Capabilities:

- Fetches `/healthz`, `/api/roster`, `/api/presence`, and `/api/ops/status`.
- Renders roster count, online ping count, direct route count, and service count.
- Shows a route matrix for `nova.<name>.direct` ownership.
- Sends a test prompt through `/v1/chat/completions` for selected nova/channel.

Boundaries:

- No backend route changes.
- No replacement for the existing Ops, Observatory, Canvas, or Kanban pages.
- Subject owner labels are static hints until the backend exposes a first-class
  owner map.

— SIGNED_BY_AGENT
