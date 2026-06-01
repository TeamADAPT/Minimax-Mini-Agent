# Swift Brane Pilot

Wasm64-native tool registry pilot for Nova crew.

## Architecture

- **Host**: loads .wasm modules at runtime via FFI or wasmtime
- **Tool**: static wasm64 module with well-known exports
- **Pilot**: file_read tool (noop → 42, validates UTF-8 path)

## Build

Requires: `rustup component add rust-src --toolchain nightly`

```bash
cargo +nightly build -Zbuild-std=core,alloc,panic_abort \
  --target wasm64-unknown-unknown --release
```

Output: `target/wasm64-unknown-unknown/release/libswift_brane_file_read.rlib`

Note: cdylib on wasm64-unknown-unknown produces .rlib (ar archive of wasm bytecode)
rather than a standalone .wasm. Link via host shim (e.g., wasm-bindgen or custom FFI).

## Tool Interface

```c
// file_read(path_ptr, path_len) -> i32
// Returns 0 on success, -1 on error. Host handles actual file I/O.
```

## NATS Listener

`swift-brane-agent` can serve request/reply traffic directly from Rust:

```bash
source /adapt/secrets/db.env
swift-brane-agent --listen
```

Defaults:

- Subject: `nova.crew.swift.invoke`
- Queue group: `swift-brane-workers`
- NATS URL: `NATS_URL` from the environment, falling back to local unauthenticated
  `nats://127.0.0.1:18020`
- Sandbox root: `SWIFT_BRANE_ROOT`, defaulting to the process working directory.

Request envelope:

```json
{"envelope_version":1,"request_id":"proof-1","payload":{"path":"README.md"}}
```

The listener returns the same ADR-002 response envelope as CLI mode and never
prints the full NATS URL.

## Systemd

The live service is `swift-brane-agent.service`:

```bash
sudo systemctl status swift-brane-agent.service
```

The unit sets `SWIFT_BRANE_ROOT` to the pipecat voice repo root so repo-local
file reads work while `/adapt/secrets` and traversal attempts are denied.

## Next Steps

1. Add `file_stat` before any write-capable tool.
2. Add registry-driven dispatch when the second tool lands.
