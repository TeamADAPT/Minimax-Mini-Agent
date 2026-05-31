# Native Hermes Session Push

## Status

in_progress

## Objective

Replace visible-terminal injection as the production path by proving and then
promoting native NATS delivery into Hermes internal sessions with realtime reply
streaming.

## Owner

CommsOps.

## Dependencies

- `ops/native_nats_adapter_spike.md`
- `rust/nova-hermes-nats-bridge`
- Hermes gateway/API server routes for Echo, Iris, and Tecton

## Steps

1. Inspect Hermes API server route behavior for session targeting and streaming.
2. Run controlled NATS proofs against agents with active API server gateways.
3. Compare Hermes `state.db` rows for CLI, gateway, API, and native adapter
   delivery.
4. Decide whether to promote API server push or revive the native Hermes NATS
   platform adapter.
5. Implement the Rust-first production route.
6. Add rollback and one-owner-per-subject checks.

## Acceptance

- A NATS turn reaches Hermes without X11/TUI typing.
- The caller receives streamed response chunks.
- The transcript records user and assistant turns with route metadata.
- The selected session behavior is documented with proof IDs.
- Rollback to existing `tui`/`hermes` runtime owners is documented.

## Rollback

Disable the native route owner and return traffic to runtime-scoped bridge
services already installed under `systemd/`.
