# 39 Crew Consensus Protocol

## Objective

Design and implement a multi-nova consensus binding protocol: propose → vote → bind, with quorum enforcement and timeout handling. Synergy owns this; other crew members act as voters.

## Owner

Synergy

## Dependencies

Task 35 (multi-subject reachability) for real voting; mock voting works without it.

## Protocol

### NATS Subjects

| Subject | Direction | Purpose |
|---------|-----------|---------|
| `nova.crew.consensus.propose` | publish | Synergy broadcasts new proposal |
| `nova.crew.consensus.vote.<topic>` | subscribe+publish | Each nova replies YES/NO/ABSTAIN |
| `nova.crew.consensus.bind.<topic>` | publish | Synergy announces binding result |

### Proposal Payload

```json
{
  "topic": "deploy-rust-bridge-v1",
  "evidence": "...",
  "proposer": "synergy",
  "quorum": 3,
  "timeout_seconds": 120,
  "proposal_id": "prop-001"
}
```

### Vote Payload

```json
{
  "proposal_id": "prop-001",
  "voter": "iris",
  "decision": "YES",
  "reasoning": "aligned with wasm64 goal"
}
```

### Binding Rules

- YES/NO votes counted; ABSTAIN ignored
- Binding if YES ≥ quorum
- NO-BIND if time expires without quorum
- NO_QUORUM if insufficient voters respond

## Steps

1. Design protocol state machine and NATS subject contract
2. Implement consensus service (Rust or Python)
3. Mock 3-nova vote with real NATS pub/sub
4. Verify binding/non-binding with correct quorum

## Acceptance

Mock 3-nova vote (skipper, echo, synergy as mock voters) yields correct binding; timeout produces NO_QUORUM.

## Rollback

Stop consensus subscriber; no data bound without explicit binding message.
