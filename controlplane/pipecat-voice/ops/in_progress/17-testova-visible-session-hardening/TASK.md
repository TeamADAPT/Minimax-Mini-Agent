# 17 Testova Visible Session Hardening

## Objective

Make `Testova` reliably answer through the intended visible CLI session or formally confirm it should remain validation-only on fallback.

## Owner

- Primary: `Latch`
- Support: `Testova`

## Dependencies

- Existing `testova-tui-nats-bridge.service`
- Current route-state and heartbeat snapshots

## Steps

1. Inspect Testova terminal launch path, window targeting, cwd, and profile binding.
2. Determine whether failure is terminal launch, `xdotool` targeting, or Hermes session persistence.
3. Tighten diagnostics and relaunch the visible path.
4. Run repeated direct NATS proofs and compare visible vs fallback behavior.

## Acceptance

- Three consecutive `nova.testova.direct` prompts land in the intended visible CLI session.
- If not possible, document the blocker and lock Testova into validation-only fallback posture.

## Rollback

- Preserve the current fallback path for continuity.
- Do not assign Testova primary execution tasks until visible proof is clean.
