# Team Delegation Protocol

## Status

to_do

## Objective

Define how Latch should pull Vaeris, Tecton, Echo, Iris, Skipper, and other novas into this project through NATS/Hermes tasks without losing control of ownership, logs, or rollback.

## Suggested Roles

- Latch: owner/integrator, final decisions, task movement, revert plan.
- Skipper: Paperclip fleet sync and docs packaging.
- Vaeris: architecture review, risk analysis, memory/continuity notes.
- Tecton: adapter/runtime implementation and transport hardening.
- Echo: visible CLI/NATS proof target and UX feedback.
- Iris: observability, screenshots, QA, user-facing proof.

## Steps

1. Move this folder to `ops/in_progress/`.
2. Verify which profiles are actually available.
3. Create a team routing table with subject, active dir, profile config, and best role.
4. Define how to send each agent a task through NATS or Hermes CLI.
5. Define how their outputs should become task `completion_report.md` files.
6. Define escalation and rollback rules.
7. Write `completion_report.md`.
8. Move this folder to `ops/completed/`.
9. Commit and push.

## Acceptance

- There is a concrete delegation protocol.
- It names exact agents and exact routes.
- It keeps Latch as project owner and avoids unsupervised destructive work.

