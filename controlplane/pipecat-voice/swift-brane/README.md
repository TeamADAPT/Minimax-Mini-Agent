# Swift Brane Pilot

Wasm64-native tool registry pilot for Nova crew.

## Architecture
- Host: loads .wasm modules at runtime
- Tool: static wasm64 module with well-known exports
- Pilot: file_read tool (noop → 42)

## Build
```
cargo +nightly build --target wasm64-unknown-unknown
```
