# Swift Brane Pilot

## 2026-05-31 17:21:48 — SIGNED_BY_AGENT

Task 37 is complete as a Rust/no-Python NATS tool invocation path.

## Service

- Workspace: `swift-brane`
- Agent binary: `/usr/local/bin/swift-brane-agent`
- Host binary: `/usr/local/bin/swift-brane-host`
- Unit: `swift-brane-agent.service`
- Subject: `nova.crew.swift.invoke`
- Queue group: `swift-brane-workers`
- Sandbox root: `/adapt/platform/novaops/controlplane/pipecat-voice`

## Tool

- Tool name: `file_read`
- Tool crate: `swift-brane/crates/file-read`
- Target: `wasm64-unknown-unknown`
- Artifact: `swift-brane/target/wasm64-unknown-unknown/release/swift_brane_file_read.wasm`
- Host I/O gate: `swift-brane-agent` host function layer

## Verification

- `cargo fmt --check`
- `cargo check`
- `cargo test`
- `cargo clippy -- -D warnings`
- `cargo +nightly build -Zbuild-std=core,alloc,panic_abort --target wasm64-unknown-unknown --release -p swift-brane-file-read`
- `cargo build --release`
- CLI proof: `cli-proof-001` returned `swift-brane/README.md`.
- NATS proof with foreground agent: `nats-proof-001` returned `swift-brane/README.md`.
- Systemd proof: `systemd-proof-002` returned `swift-brane/README.md`.
- Sandbox denial proof: `systemd-deny-secret-001` denied `/adapt/secrets/db.env`.
- Sandbox traversal proof: `systemd-deny-traversal-001` denied `../secrets/db.env`.

## Rollback

```bash
sudo systemctl disable --now swift-brane-agent.service
```

The service is stateless. Removing the unit stops tool invocation without
touching NATS or the voice gateway.
