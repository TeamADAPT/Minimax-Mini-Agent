# 23 Skipper Orchestration Contract

## Objective

Define the exact delegation format `Skipper` will use to orchestrate work across the crew.

## Owner

- Primary: `Skipper`
- Support: `Latch`

## Dependencies

- None beyond current NATS collaboration routes

## Steps

1. Define a standard task envelope: objective, owner, acceptance, proof, checkback route.
2. Define escalation rules and stale-task handling.
3. Define how Skipper hands work to Echo, Testova, and Latch.

## Acceptance

- Every task issued by Skipper has a clean owner, proof contract, and return route.

## Rollback

- Continue manual orchestration if the contract draft blocks work.
