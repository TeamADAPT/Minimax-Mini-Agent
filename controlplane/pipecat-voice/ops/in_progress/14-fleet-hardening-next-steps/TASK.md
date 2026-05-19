# Fleet Hardening Next Steps

## 2026-05-18 21:28:19 — SIGNED_BY_AGENT

Status: in_progress

Objective: execute the first post-Skipper hardening slice for the NovaOps fleet.

Scope:

- Give Skipper a bounded read-only NATS task and capture the result.
- Run the Rust NATS bridge against a real Hermes Echo session on an isolated native subject.
- Add a tracked secret guardrail so scrubbed branches stay clean.
- Refresh Paperclip fleet docs with Skipper, Rust bridge, and scrub status.
- Add a minimal fleet-control UI slice for health, route matrix, and test prompts.

Acceptance:

- Skipper responds over `nova.skipper.direct` with a useful structured report.
- Rust bridge proof uses a real Hermes process and does not steal `nova.echo.direct`.
- Secret scanner runs against tracked files without revealing secret values.
- Paperclip has current fleet sync notes.
- UI slice can be served by the existing gateway static client path.

— SIGNED_BY_AGENT
