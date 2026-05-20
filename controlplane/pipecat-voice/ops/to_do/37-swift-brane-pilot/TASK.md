#Swift Brane Pilot

## Objective

Implement the first wasm64-native tool proxy: a `file_read` binary that any nova can call via the Swift Brane registry instead of a Python subprocess.

## Owner

Forge

## Dependencies

None; isolated pilot. Task 35 needed only for distributed invocation demo.

## Steps

1. Scaffold swift-brane/ Rust workspace under pipecat-voice/
2. Implement wasm64-unknown-unknown file_read tool
3. Write Swift Brane registry (JSON or tiny db)
4. Register and invoke via NATS `nova.crew.swift.invoke`
5. Verify zero Python subprocess in the happy path

## Acceptance

`cargo build --target wasm64-unknown-unknown` passes; NATS invoke returns file content without spawning python; proof id recorded in ops/.

## Rollback

Remove swift-brane/ directory and registry; no host changes, no live services.
