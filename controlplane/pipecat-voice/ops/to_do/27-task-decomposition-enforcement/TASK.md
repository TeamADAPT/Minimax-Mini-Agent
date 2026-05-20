# 27 Task Decomposition Enforcement

## Objective

Enforce the task-folder workflow so each active slice is ownable and closable.

## Owner

- Primary: `Skipper`
- Support: `Latch`

## Dependencies

- Existing `ops/to_do`, `ops/in_progress`, and `ops/completed` workflow

## Steps

1. Require one task directory per unit of work.
2. Require moves from `to_do` to `in_progress` before execution.
3. Require `completion_report.md` before moving to `completed`.
4. Keep umbrella planning separate from executable tasks.

## Acceptance

- No vague umbrella tasks remain in the active queue.
- Every in-flight task has a directory, owner, and completion path.

## Rollback

- Use manual tracking temporarily if a critical incident bypasses the task queue.
