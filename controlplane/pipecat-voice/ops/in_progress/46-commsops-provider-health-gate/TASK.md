# CommsOps Provider Health Gate

## Status

in_progress

## Objective

Establish one known-good, low-cost provider/model lane for CommsOps route
promotion proofs before native Hermes session push is promoted.

## Owner

CommsOps.

## Context

Task 42 proved Hermes API session endpoints are reachable and that the Rust
bridge can call them, but every tested profile failed before assistant
persistence because of provider/model/account state:

- Echo: invalid `grok-4.3` fallback route through NVIDIA after xAI OAuth was
  unavailable.
- Iris/Tecton: xAI authorization or credit failure.
- Vox: configured Nous model was not found upstream.
- Zap: DeepSeek insufficient balance.
- Direct NIM canary with `z-ai/glm-5.1` did not complete inside the bounded
  proof timeout.

## Steps

1. Inventory current active gateway provider/model pairs without exposing keys.
2. Select or create one CommsOps canary profile that is not user-facing.
3. Configure the canary to a verified low-cost provider/model.
4. Run a one-turn CLI proof with `--max-turns 1`.
5. Run API session sync proof.
6. Run API session stream proof.
7. Verify `state.db` contains user and assistant rows.
8. Feed the canary back into Task 42.

## Acceptance

- One canary profile returns a one-turn answer in under 60 seconds.
- `/api/sessions/{id}/chat` returns non-empty assistant content.
- `/api/sessions/{id}/chat/stream` emits assistant content.
- Session messages contain both user and assistant rows.
- No provider key, token, or account secret is printed or committed.

## Rollback

Disable or stop the canary gateway service and leave existing profile routes
unchanged.
