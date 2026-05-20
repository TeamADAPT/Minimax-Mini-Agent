# 24 Skipper Echo Execution Lane

## Objective

Establish a clean execution cadence between `Skipper` and `Echo`.

## Owner

- Primary: `Skipper`
- Executor: `Echo`

## Dependencies

- Task `23`
- Stable Echo route

## Steps

1. Define assignment cadence and checkback rules.
2. Give Echo bounded execution tasks with explicit proofs.
3. Confirm that completions return cleanly to Skipper.

## Acceptance

- Echo completes three consecutive bounded tasks under Skipper direction.

## Rollback

- Route work through Latch until the cadence is clean.
