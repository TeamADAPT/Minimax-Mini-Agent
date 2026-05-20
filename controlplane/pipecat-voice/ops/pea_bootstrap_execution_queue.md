# PEA Bootstrap Execution Queue

## 2026-05-19 21:31:30 — SIGNED_BY_AGENT

Task 28 decomposed the PEA/nova bootstrap buildout into independently executable follow-up slices. The queue below keeps write scopes and ownership separated so Skipper can orchestrate without turning the work back into an umbrella task.

## Execution Order

| Order | Task | Owner | Dependency Gate | Purpose |
| --- | --- | --- | --- | --- |
| 1 | `29-nova-bootstrap-rust-build-verify` | Latch | Project tree exists | Prove the Rust bootstrap can build/test and create or dry-run a canary. |
| 2 | `30-hermes-nats-adapter-promotion-gates` | Latch/Tecton | Task 29 and current visible routes | Define and run isolated adapter promotion gates without stealing live subjects. |
| 3 | `31-paperclip-nova-adapter-package` | Skipper/Latch | Task 26 | Turn fleet sync into an external Paperclip adapter package plan. |
| 4 | `32-pipecat-direct-nats-session-hook` | Latch/Vox/Echo | Tasks 20, 21, 24 | Add the guarded first pipecat-to-NATS active-session hook. |
| 5 | `33-ops-metrics-graphs-dashboard-pass` | Echo/Iris/Latch | Tasks 20 and 21 | Add useful metrics/graphs for route, proof, voice, and NATS state. |
| 6 | `34-testova-validation-resume-gate` | Latch/Testova | Operator lifts Testova hold | Define and execute the held Testova resume gate without accidental prompts. |

## Parallelism

- Tasks 29 and 31 can run in parallel because they touch different surfaces.
- Task 33 can run after the dashboard/monitor surfaces are stable and should avoid backend route changes unless explicitly required.
- Task 32 should wait for Task 24 because direct voice routing needs a known-good Echo return path.
- Task 34 must not run until the Testova hold is explicitly lifted.

## Ownership Boundaries

- Latch owns integration, commits, pushes, and rollback.
- Skipper owns orchestration and Paperclip packaging plans.
- Echo owns visible execution feedback and UI/metrics validation where assigned.
- Testova remains validation-only until its visible proof gate passes.
- Vox supports voice-path work but does not own gateway changes without a Latch task.

## Acceptance

Task 28 acceptance is satisfied by six new task folders under `ops/to_do/`, each with owner, dependencies, steps, acceptance criteria, and rollback.

**— SIGNED_BY_AGENT**
