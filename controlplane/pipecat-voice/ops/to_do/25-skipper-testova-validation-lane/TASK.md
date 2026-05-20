# 25 Skipper Testova Validation Lane

## Objective

Establish a clean validation cadence between `Skipper` and `Testova`.

## Owner

- Primary: `Skipper`
- Executor: `Testova`

## Dependencies

- Task `23`
- Current Testova route posture

## Steps

1. Define validation-only task format for Testova.
2. Require structured outputs: pass/fail, reproduction, confidence, follow-up.
3. Keep Testova off primary execution until route stability improves.

## Acceptance

- Testova returns usable validation outputs without re-interpretation.

## Rollback

- Keep Testova as ad hoc test support if the lane is not yet steady.
