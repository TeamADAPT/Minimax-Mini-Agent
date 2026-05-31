# Completion Report

## 2026-05-31 09:22:19 — SIGNED_BY_AGENT

Completed `47-user-facing-provider-route-repair`.

## Result

- Repaired Iris, Echo, and Tecton by moving their local Hermes default
  provider/model route from xAI/Grok to NVIDIA NIM
  `qwen/qwen3.5-397b-a17b`.
- Created local config backups before modification:
  `config.yaml.bak.commsops47.20260531T161406Z`.
- Added the missing local API-server key entry to Echo by copying the existing
  fleet API-server key from another local profile without printing or
  committing the key.
- Restarted only:
  - `hermes-gateway-iris.service`
  - `hermes-gateway-echo.service`
  - `hermes-gateway-tecton.service`
  - `nova-hermes-nats-bridge.service`
- Added Rust bridge output denoising so signature/CWD/date tails are removed
  from streamed voice chunks while preserving Hermes session persistence.

## Proofs

- CLI provider proofs:
  - Iris returned `IRIS RUST READY`.
  - Echo returned `ECHO RUST READY`.
  - Tecton returned `TECTON RUST READY`.
- API sync proofs:
  - Iris returned `IRIS API OK` in 7.48s.
  - Echo returned `ECHO API OK` in 6.53s.
  - Tecton returned `TECTON API OK` in 7.27s.
- API stream proofs:
  - Iris emitted `IRIS STREAM OK`.
  - Echo emitted `ECHO STREAM OK`.
  - Tecton emitted `TECTON STREAM OK`.
- Live Rust NATS proofs:
  - `proof-commsops47-iris-1780244239`
  - `proof-commsops47-echo-1780244284`
  - `proof-commsops47-tecton-1780244329`
  - `proof-commsops47-iris-clean-1780244463`

## Persistence

- `nats_iris_codex` contains user and assistant rows.
- `nats_echo_codex` contains user and assistant rows.
- `nats_tecton_codex` contains user and assistant rows.

## Denoising

The final Iris clean proof streamed only the spoken reply chunks plus route
metadata. The persisted Hermes session still keeps the agent's full assistant
message, which is useful for audit, while the Rust bridge cleans the voice
payload before it reaches route consumers.

## Rollback

Restore each affected profile from
`config.yaml.bak.commsops47.20260531T161406Z`, restart the matching
`hermes-gateway-<name>.service`, then restart `nova-hermes-nats-bridge.service`.
