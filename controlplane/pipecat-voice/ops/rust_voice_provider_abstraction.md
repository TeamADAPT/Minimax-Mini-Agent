# Rust Voice Provider Abstraction

## 2026-05-31 10:17:03 — SIGNED_BY_AGENT

Task 43 first slice creates a Rust-owned provider contract without changing the
live Deepgram voice path.

## Current Voice Surfaces

- Browser realtime path: `/ws/voice` proxies browser audio to
  `wss://agent.deepgram.com/v1/agent/converse` with the long-lived Deepgram key
  kept server-side.
- Browser token path: `/token` mints a short-lived Deepgram auth grant through
  `https://api.deepgram.com/v1/auth/grant`.
- Think path: Deepgram calls `/v1/chat/completions`, which routes through NATS
  to the selected nova runtime.
- Legacy Pipecat path: `bot.py` still defines Deepgram STT/TTS with Groq and
  ElevenLabs fallbacks, but the active browser gateway is `gateway.py`.

## Rust Contract

Crate:

```text
rust/nova-voice-provider-core
```

The crate defines:

- `ProviderKind`: `deepgram`, `xai`
- `VoiceCapability`: `stt`, `tts`, `realtime`
- `BrowserCredentialPolicy`: server proxy only or ephemeral client secret
- `ProviderConfig`: enabled/experimental gates, required env names, endpoints,
  capability set, default realtime model
- `VoiceProvider` trait and route planning
- Deepgram default config
- Guarded xAI default config
- `voice_provider_plan` CLI for route-safe JSON planning without printing
  credential values

## xAI Guardrail

Official xAI voice docs currently expose:

- Realtime: `wss://api.x.ai/v1/realtime`
- Browser ephemeral secret mint: `/v1/realtime/client_secrets`
- TTS: `/v1/tts`
- STT: `/v1/stt`
- Default realtime model: `grok-voice-latest`

The xAI provider is marked experimental and cannot plan a route unless the
caller sets `allow_experimental=true`.

## Verification

```bash
cargo fmt --check
cargo check
cargo test
cargo clippy -- -D warnings
```

All passed for `rust/nova-voice-provider-core`.

CLI proof:

```bash
DEEPGRAM_API_KEY=dummy cargo run --quiet --bin voice_provider_plan -- \
  --provider deepgram --route-id iris.direct --capability realtime --browser-direct

XAI_API_KEY=dummy cargo run --quiet --bin voice_provider_plan -- \
  --provider xai --route-id room.main --capability realtime --browser-direct \
  --allow-experimental
```

Guard proof: the same xAI command without `--allow-experimental` exits with
`ExperimentalBlocked`.

## 2026-05-31 16:54:47 — SIGNED_BY_AGENT

Gateway integration is live.

Endpoint:

```text
GET /api/voice/provider-plan
```

Query parameters:

- `provider`: `deepgram` or `xai`
- `route_id`: route label such as `iris.direct` or `room.main`
- `capability`: repeatable `stt`, `tts`, or `realtime`; defaults to
  `realtime`
- `browser_direct`: whether the browser will connect directly using an
  ephemeral credential
- `allow_experimental`: required for xAI

Live proofs:

- Deepgram browser realtime plan returned HTTP 200 with ephemeral-client-secret
  policy and no credential value.
- xAI browser realtime plan returned HTTP 400 without `allow_experimental`.
- xAI browser realtime plan returned HTTP 200 with `allow_experimental=true`.
- `voice_provider_tts_probe` refuses xAI TTS unless `--allow-experimental` is
  passed.

The active `/ws/voice` audio path remains Deepgram.

Installed runtime binaries:

- `/usr/local/bin/nova-voice-provider-plan`
- `/usr/local/bin/nova-voice-provider-tts-probe`

`pipecat-voice.service` sets
`VOICE_PROVIDER_PLAN_BIN=/usr/local/bin/nova-voice-provider-plan`.
