# Rust Voice Provider Abstraction

## Status

in_progress

## Objective

Move voice provider control toward a Rust-owned abstraction that can route
Deepgram and xAI voice without exposing browser clients to long-lived provider
credentials.

## Owner

CommsOps.

## Dependencies

- Current CX Pipe Deepgram voice path.
- xAI voice API spike.
- `/adapt/secrets/m2.env` for provider credentials.

## Steps

1. Document current STT/TTS WebSocket and HTTP surfaces.
2. Define a Rust voice provider trait for STT, TTS, and realtime sessions.
3. Add Deepgram as the baseline provider.
4. Add xAI voice as a guarded experimental provider.
5. Use short-lived browser credentials where direct browser WebSocket access is
   required.
6. Preserve Deepgram as fallback until xAI latency and failure behavior pass.

## Acceptance

- No long-lived provider key is sent to the browser.
- Provider choice is explicit per route or room.
- Deepgram behavior is preserved.
- xAI voice can be tested without destabilizing the default route.
- Voice output remains clean and speakable.

## Rollback

Disable the xAI provider flag and leave Deepgram as the default CX Pipe voice
provider.
