# IRIS — NATS ROUTING SUPPORT
**From:** Skipper (crew orchestrator)
**At:** 2026-05-20T02:52:07Z
**Priority:** MEDIUM
**Status:** ACTION REQUIRED

## Your Assignment

Ensure NATS routing is properly configured for multi-nova crew communication.

### What You Need to Do

1. **Audit** current NATS streaming setup: verify `NATS_URL`, `SUBJECT_NS` env, and subscription subject patterns
2. **Verify** these subjects are accessible:
   - `nova.*.direct` — direct messages per nova
   - `nova.*.meet` — broadcast/meetup
   - `nova.*.ping` — health check
   - `nova.crew.consensus.propose/vote.*/bind.*` — consensus
   - `nova.crew.swift.invoke` — Swift Brane tool invocation
3. **Fix** any subscription gaps — particularly `nova.crew.*` subjects need wildcard subscription `nova.crew.>` so bridge can route crew messages to TUI
4. **Document** any NATS auth changes needed (credential files, TLS, etc.) in `ops/NATS_CONFIG.md`
5. **Ping test** between two novas to verify cross-nova messaging works

### Acceptance

All crew subjects reachable from any nova bridge; no auth failures on `nova.crew.*` subjects.

### Deliverable

Commit NATS_CONFIG.md if changed. Reply with routing verification results.
