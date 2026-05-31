# Nova Voice Provider Core

Rust-owned provider contract for CX Pipe voice routing.

This crate does not replace the live Deepgram path yet. It defines the provider
capability model, credential policy, endpoint defaults, and experimental gating
needed before the gateway can route Deepgram and xAI voice through one
configuration surface.

## Providers

- `deepgram`: default provider, server-proxied key, short-lived browser token
  support.
- `xai`: experimental provider, requires explicit experimental opt-in and
  ephemeral client-secret policy for browser realtime sessions.

## Verification

```bash
cargo fmt --check
cargo test
cargo clippy -- -D warnings
```

## CLI Planner

```bash
DEEPGRAM_API_KEY=present cargo run --bin voice_provider_plan -- \
  --provider deepgram --route-id iris.direct --capability realtime --browser-direct

XAI_API_KEY=present cargo run --bin voice_provider_plan -- \
  --provider xai --route-id room.main --capability realtime --browser-direct \
  --allow-experimental
```

The planner prints route-safe JSON and never prints credential values.
