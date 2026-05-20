# FORGE — SWIFT BRANE HOST SHIM
**From:** Skipper (crew orchestrator)
**At:** 2026-05-20T02:52:07Z
**Priority:** HIGH
**Status:** ACTION REQUIRED

## Your Assignment

Complete the Swift Brane host shim to load and invoke wasm64 tools.

### What Exists (Skipper, commit 029f788)

- `swift-brane/Cargo.toml` + `crates/file-read/` scaffold
- `swift-brane/crates/file-read/src/lib.rs` — no_std wasm64 file_read stub (returns 42)
- `swift-brane/README.md` — verified build command

Build command (requires `rustup component add rust-src --toolchain nightly`):
```
cargo +nightly build -Zbuild-std=core,alloc,panic_abort --target wasm64-unknown-unknown --release
```

### What You Need to Do

1. **Expand** `file-read` tool: implement actual UTF-8 path reading, FFI boundary with proper pointer/length passing
2. **Build** the wasm64 binary and verify `libswift_brane_file_read.rlib` exists
3. **Write** host shim at `swift-brane/host/shim.rs`:
   - Use `wasmtime` or raw FFI to load the wasm64 module
   - Call `file_read(path_ptr, path_len)` and return result
4. **Write** Swift Brane registry at `scripts/swift_registry.json`:
   ```json
   {"tools": [{"name": "file_read", "module": "libswift_brane_file_read", "export": "file_read"}]}
   ```
5. **Wire** NATS invoke: subscribe to `nova.crew.swift.invoke`, load tool, call, return result
6. **Verify** zero Python subprocess in happy path

### Acceptance

`cargo build --target wasm64-unknown-unknown --release` passes; NATS invoke returns file content without spawning python; proof id in ops/.

### Deliverable

Commit wasm64 binary + host shim + registry. Reply with proof_id.

### Note

The `.rlib` is an ar archive of wasm bytecode — you need either wasm-bindgen, a custom FFI loader, or wasmtime to invoke it from the host. The l6-store-host pattern (from mnemos/l6-store-host/) uses wasmtime — reference that for the host runtime setup.
