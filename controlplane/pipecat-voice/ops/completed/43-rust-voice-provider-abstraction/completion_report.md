# Completion Report

## 2026-05-31 16:54:47 — SIGNED_BY_AGENT

Implemented the Rust-owned voice provider abstraction milestone.

Delivered:

- `rust/nova-voice-provider-core` provider contract crate.
- Deepgram default provider config for the current CX Pipe voice path.
- xAI provider config guarded behind explicit experimental opt-in.
- `voice_provider_plan` CLI that returns route-safe JSON without printing
  credentials.
- `voice_provider_tts_probe` CLI for guarded xAI TTS probing without printing
  credentials.
- `/api/voice/provider-plan` gateway endpoint backed by the release Rust
  planner.
- Installed planner/probe binaries under `/usr/local/bin`.
- Provider docs in `ops/rust_voice_provider_abstraction.md`.

Verification:

- `python3 -m py_compile gateway.py`
- `pytest -q tests/test_gateway.py tests/test_turn_events.py tests/test_tui_mirror.py`
- `cargo fmt --check`
- `cargo check`
- `cargo test`
- `cargo clippy -- -D warnings`
- `cargo build --release --bin voice_provider_plan --bin voice_provider_tts_probe`
- Live Deepgram provider-plan endpoint returned HTTP 200.
- Live xAI provider-plan endpoint returned HTTP 400 without
  `allow_experimental`.
- Live xAI provider-plan endpoint returned HTTP 200 with
  `allow_experimental=true`.
- xAI TTS probe guard rejected execution without `--allow-experimental`.

Rollback:

Remove `/api/voice/provider-plan` from the gateway and ignore
`rust/nova-voice-provider-core`. The current `/ws/voice` Deepgram path remains
unchanged.
