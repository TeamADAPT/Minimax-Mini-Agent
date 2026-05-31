# Completion Report

## 2026-05-31 09:01:31 — SIGNED_BY_AGENT

Completed `46-commsops-provider-health-gate`.

## Result

- Created non-user-facing Hermes profile `commscanary`.
- Configured `commscanary` for NVIDIA NIM
  `qwen/qwen3.5-397b-a17b` with a 262144-token context override.
- Added local user systemd gateway service
  `hermes-gateway-commscanary.service` with a drop-in override that sources
  shared model credentials without committing secrets.
- Verified the gateway listens on `127.0.0.1:8675`.

## Proofs

- Direct provider probes:
  - Groq `llama-3.1-8b-instant`: passed direct HTTP canary in 0.22s but was not
    selected for Hermes because the standard Hermes payload exceeded route
    limits.
  - NVIDIA `meta/llama-3.1-8b-instruct`: passed direct HTTP canary in 0.35s.
  - NVIDIA `qwen/qwen3.5-397b-a17b`: passed direct HTTP canary and was selected
    for the large-context Hermes canary lane.
- Hermes CLI proof:
  - `commscanary` returned `COMMSCANARY OK` through Hermes with
    `--max-turns 1`.
- API sync proof:
  - `POST /api/sessions/commsops_canary_sync_20260531/chat` returned
    `API SYNC OK` in 3.29s.
- API stream proof:
  - `POST /api/sessions/commsops_canary_stream_20260531/chat/stream` emitted
    assistant content in 11.05s.
- Persistence proof:
  - Sync session contains user and assistant rows.
  - Stream session contains user and assistant rows.

## Provider Findings

- DeepSeek is blocked by insufficient balance.
- OpenRouter is blocked by insufficient credits.
- Gemini is blocked by quota.
- xAI-backed user-facing profiles remain blocked by account/credit
  authorization state.
- Cerebras key path reached the API, but the tested model name was unavailable.
- NVIDIA Qwen is the current promotable CommsOps provider lane.

## Follow-Up

- Feed `commscanary` into Task 42 and run the Rust bridge API-session path
  against the proven lane before promoting native session delivery.
