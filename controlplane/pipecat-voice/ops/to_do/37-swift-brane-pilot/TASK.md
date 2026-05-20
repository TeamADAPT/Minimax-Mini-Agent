# 37 Swift Brane Pilot — UPDATED by Skipper

## Objective

Implement the first wasm64-native tool proxy: a `file_read` binary that any nova can call via the Swift Brane registry instead of a Python subprocess.

## Owner

Forge

## Dependencies

None; isolated pilot. Task 35 (crew online) needed only for distributed invocation demo.

## Status: PARTIAL — Skipper scaffolded in session 029f788/4c27312

Scaffold completed by Skipper:
- `swift-brane/` Rust workspace
- `swift-brane/Cargo.toml` (cdylib, panic=abort)
- `swift-brane/crates/file-read/` — no_std wasm64 lib.rs
- `swift-brane/README.md` — build docs

**Verified build command** (requires `rustup component add rust-src --toolchain nightly`):
```bash
cargo +nightly build -Zbuild-std=core,alloc,panic_abort \
  --target wasm64-unknown-unknown --release
# Output: libswift_brane_file_read.rlib (ar archive, 5KB)
```

## Remaining Work (Forge)

1. Write Swift Brane host shim to load and invoke the wasm64 module (FFI or wasmtime)
2. Build Swift Brane registry: `scripts/swift_registry.json` listing available tools
3. Register tool via NATS `nova.crew.swift.invoke` subject
4. Verify zero Python subprocess in happy path (direct FFI call)
5. Document proof id in `ops/operations_history.md`

## Acceptance

`cargo build --target wasm64-unknown-unknown --release` passes; NATS invoke returns file content without spawning python; proof id recorded in ops/.

## Rollback

Remove swift-brane/ directory and registry; no host changes, no live services.