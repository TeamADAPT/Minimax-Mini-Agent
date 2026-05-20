# Task Queue Enforcement

## 2026-05-19 21:28:48 — SIGNED_BY_AGENT

This note defines the active queue rule for NovaOps work under `ops/`.

## Required Workflow

Every executable unit of work must be represented by exactly one task directory:

```text
ops/to_do/<task-slug>/TASK.md
ops/in_progress/<task-slug>/TASK.md
ops/completed/<task-slug>/TASK.md
```

Required task fields:

- objective;
- owner;
- dependencies, or `none`;
- concrete steps;
- acceptance criteria;
- rollback or stop condition.

## Movement Rules

- Move a task from `ops/to_do/` to `ops/in_progress/` before execution starts.
- Write progress notes inside the task directory when a task is paused, held, or blocked.
- Write `completion_report.md` before moving a task into `ops/completed/`.
- Do not leave umbrella tasks in `ops/in_progress/` after their executable slices have their own task folders.
- Keep strategy/directive documents under `ops/directives/` or a named planning artifact; do not treat them as active executable tasks.

## Active Queue Audit

Current non-completed tasks after this pass:

| Task | State | Owner | Status |
| --- | --- | --- | --- |
| `17-testova-visible-session-hardening` | `in_progress` | Latch/Testova | Held by operator; has progress note and completion path. |
| `22-voice-path-validation` | `to_do` | Echo/Latch | Executable but deferred until voice path testing resumes. |
| `25-skipper-testova-validation-lane` | `to_do` | Skipper/Testova | Blocked by Testova hold; not started. |
| `28-pea-bootstrap-execution-queue` | `to_do` | Skipper/Latch/Echo/Testova | Next decomposition task. |

Task `14-fleet-hardening-next-steps` was closed as umbrella audit debt because its executable slices have been split and completed through later task folders and commits.
Task `27-task-decomposition-enforcement` is closed by this audit after the active queue check passes.

## Enforcement Checklist

Before starting work:

- [ ] Is there a task directory for this unit?
- [ ] Is the task narrow enough for one owner to close?
- [ ] Are dependencies explicit?
- [ ] Is acceptance observable?
- [ ] Is rollback or stop behavior written down?

Before completion:

- [ ] `completion_report.md` exists.
- [ ] Ops history and decisions are updated.
- [ ] Verification evidence is named.
- [ ] The task directory is moved to `ops/completed/`.
- [ ] Exact files are staged; broad `git add .` is avoided in dirty trees.

**— SIGNED_BY_AGENT**
