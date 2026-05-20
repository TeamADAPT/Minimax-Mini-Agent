# Iris Task: NATS Routing Audit

## Objective
Audit all NATS routing patterns in the pipecat-voice workspace. Document subject namespaces, bridge patterns, and any anomalies.

## Steps
1. Read ops/crew-comms/references/nats-dispatch-patterns.md
2. Run `nats context list` and `nats server report connections`
3. Document all `nova.<name>.direct` subjects in use
4. Check for routing gaps (agents without direct bridges)
5. Output to ops/NATS_CONFIG.md with format: subject | owner | status | notes

## Acceptance
- ops/NATS_CONFIG.md exists with complete routing table
- Any orphaned or missing bridges flagged as BLOCKER
