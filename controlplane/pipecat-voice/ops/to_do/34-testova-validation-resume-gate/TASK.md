# 34 Testova Validation Resume Gate

## Objective

Prepare the exact gate for resuming Testova validation work when the operator lifts the current hold.

## Owner

- Primary: `Latch`
- Support: `Testova`

## Dependencies

- Task `17`
- Operator explicitly lifts Testova hold

## Steps

1. Re-check Testova window, cwd, profile binding, and bridge service state.
2. Run the held three-turn visible-only NATS proof only after operator approval.
3. If the proof passes, unlock Task `25`.
4. If the proof fails, record the root cause and keep Testova validation-only or offline.

## Acceptance

- Testova has a clear resume procedure with pass/fail gates and no ambiguity about when prompts may be sent.

## Rollback

- Do not send Testova prompts; keep Task `17` held and preserve the current service state.
