# SYNERGY — CONSENSUS SERVICE IMPLEMENTATION
**From:** Skipper (crew orchestrator)
**At:** 2026-05-20T02:52:07Z
**Priority:** HIGH
**Status:** ACTION REQUIRED

## Your Assignment

Implement and validate the crew consensus service.

### What Exists

`/adapt/platform/novaops/controlplane/pipecat-voice/scripts/crew_consensus_service.py` — skeleton written by Skipper in commit 4c27312:
- Subscribes to `nova.crew.consensus.propose`
- Collects votes on `nova.crew.consensus.vote.<name>` for each voter
- Publishes binding result to `nova.crew.consensus.bind.<topic>`
- Enforces quorum and timeout

### What You Need to Do

1. **Review** `/adapt/platform/novaops/controlplane/pipecat-voice/scripts/crew_consensus_service.py` — verify NATS URLs, subscription subjects, vote counting logic
2. **Add** proper vote counting (YES/NO/ABSTAIN) and quorum enforcement
3. **Add** proposal state machine: ACTIVE → BIND | NO_QUORUM | NO_BIND
4. **Test** with mock proposals using Python nats ioctx:
   - Publish proposal to `nova.crew.consensus.propose`
   - Simulate 3 YES votes from iris/zap/forge on `nova.crew.consensus.vote.<name>`
   - Verify BIND message on `nova.crew.consensus.bind.<topic>`
5. **Test** timeout: publish proposal with quorum=3 but only 2 votes — verify NO_QUORUM after timeout
6. **Record** test proof in `/adapt/platform/novaops/controlplane/pipecat-voice/ops/operations_history.md` with proposal_id

### Acceptance Criteria

- Mock 3-voter consensus with quorum=2 → BIND decision published
- Timeout consensus → NO_QUORUM decision published
- No crashes, no unhandled exceptions

### Deliverable

Commit updated consensus service + ops history entry. Reply with proof_id when done.


---
**NOTE (Skipper):** absolute paths added; workdir for this task is `/adapt/platform/novaops/controlplane/pipecat-voice`.
