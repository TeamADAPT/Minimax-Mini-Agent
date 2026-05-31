# User-Facing Provider Route Repair

## Status

in_progress

## Objective

Repair provider/model/account routes for user-facing novas so the proven Rust
API-session path can be promoted beyond `commscanary`.

## Owner

CommsOps.

## Context

Task 42 proved the native Rust bridge can deliver NATS turns into Hermes API
sessions and return streamed chunks with route metadata. Task 46 established
`commscanary` on NVIDIA NIM `qwen/qwen3.5-397b-a17b` as the current known-good
provider lane.

User-facing profiles still fail for account/model reasons:

- Echo: xAI/Grok route falls through to an invalid fallback path.
- Iris/Tecton/Vaeris/Veyra: xAI account or credit authorization errors.
- Zap/DeepSeek profiles: insufficient balance.
- Vox/Nous route: configured model not found upstream.
- OpenRouter/Gemini: credit or quota blocked.

## Steps

1. Inventory each user-facing profile provider/model route without printing
   secrets.
2. Select a temporary safe fallback provider per profile, preferring large
   context lanes already proven in Task 46.
3. Update profile config/env/systemd only for profiles selected for repair.
4. Restart one profile at a time.
5. Run CLI proof, API sync proof, API stream proof, and Rust NATS proof.
6. Record route metadata and session persistence proof IDs.
7. Promote repaired profiles into the Rust runtime bridge roster only after
   proof passes.

## Acceptance

- At least Iris, Echo, and Tecton return one Rust runtime NATS turn each.
- Each proof produces streamed chunks.
- Each proof persists user and assistant rows in the expected Hermes session.
- No provider key, token, or account secret is printed or committed.
- Rollback for each profile is documented.

## Rollback

Restore the prior profile provider/model config backup, restart the affected
gateway service, and remove the profile from `nova-hermes-nats-bridge.service`
if the Rust route is not healthy.
