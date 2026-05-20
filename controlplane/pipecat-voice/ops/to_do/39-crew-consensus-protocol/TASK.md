#Crew Consensus Protocol

## Objective

Define and prototype a multi-nova consensus binding: propose → vote → bind, with timeout handling and NO_QUORUM fallbacks.

## Owner

Synergy

## Dependencies

Task 35 (multi-subject reachability) for real voting; can mock with just Skipper/Echo for protocol validation.

## Steps

1. Define consensus state machine and NATS subjects (propose, vote, bind)
2. Implement mock voter echo service for testing
3. Run 3-nova mock proposal to binding
4. Implement timeout → NO_QUORUM
5. Document protocol contract in ops/crew_consensus_protocol.md

## Acceptance

Mock 3-nova vote yields correct binding result; timed-out vote returns NO_QUORUM; protocol spec committed.

## Rollback

Stop the proposal subscriber; no data binding without explicit commit.
