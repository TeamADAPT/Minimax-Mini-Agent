# CommsOps Division Activation

## Status

completed

## Objective

Establish CommsOps as the accountable operating division for the Nova voice,
NATS, Hermes session, transcript, and communication control-plane stack.

## Owner

Veyra / Codex acting as CommsOps lead.

## Context

Chase granted T1 authority for CommsOps decisions and execution inside the
communication domain. The stack already includes CX Pipe, Deepgram, NATS,
Hermes gateway/API paths, runtime-specific routing, native NATS adapter proof
work, Paperclip integration notes, and planned Temporal/memory ingestion.

## Steps

1. Document the CommsOps charter and operating authority.
2. Capture the current system posture and target architecture.
3. Seed executable follow-up tasks for native session push, Rust voice provider
   abstraction, transcript-to-memory ingestion, and observability.
4. Update README routing language to match the current runtime subject model.
5. Record actions and decisions in ops logs.

## Acceptance

- `ops/COMMSOPS_CHARTER.md` exists and defines ownership boundaries.
- `ops/COMMSOPS_STATUS.md` exists and names current state, risks, and next
  promotion gates.
- Follow-up task folders exist under `ops/to_do/`.
- README no longer presents the old `adapt.<peer>.<channel>` route as the live
  canonical model.
- Ops logs contain reverse-chronological entries signed by the acting agent.

## Rollback

Remove the CommsOps docs and follow-up tasks if Chase revokes CommsOps ownership
or chooses a different division boundary.
