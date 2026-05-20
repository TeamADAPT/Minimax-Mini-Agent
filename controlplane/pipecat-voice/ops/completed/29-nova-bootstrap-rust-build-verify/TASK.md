# 29 Nova Bootstrap Rust Build Verify

## Objective

Build and verify the Rust nova bootstrap implementation so it can create a canary nova from the current project tree.

## Owner

- Primary: `Latch`
- Support: `Skipper`

## Dependencies

- Task `28`
- `/adapt/novas/active/projects/nova-bootstrap-rs`

## Steps

1. Inspect the current Rust bootstrap project layout and documented commands.
2. Run format, clippy, tests, and release build where available.
3. Create or dry-run one canary nova generation without touching live production profiles.
4. Record exact commands, outputs, generated paths, and blockers.

## Acceptance

- Rust bootstrap verification has a pass/fail report with exact command evidence.
- Any generated canary artifacts are named and either preserved intentionally or cleaned up.

## Rollback

- Remove generated canary artifacts and leave the Rust project unchanged if verification fails.
