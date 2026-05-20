# Synergy Task: Consensus Protocol Design

## Objective
Design the crew consensus mechanism for multi-nova coordination.

## Context
- Crew has 6 members: Iris, Zap, Forge, Synergy, Tecton + Skipper (you)
- NATS is the messaging backbone
- Need: propose → vote → bind cycle for crew-wide decisions

## Steps
1. Read ops/crew-comms/references/consensus-service.md (template)
2. Design a minimal consensus service using NATS as transport
3. Decide: ephemeral (no persistence) vs persistent (fjall/redb)
4. Propose subject: `nova.crew.consensus`
5. Output design doc to ops/crew-coordination-architecture.md section "Consensus Protocol"

## Acceptance
- Section in ops/crew-coordination-architecture.md covering: message types, quorum rules, failure handling
