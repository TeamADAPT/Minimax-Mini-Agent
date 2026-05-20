# 16 Skipper Visible Session Hardening

## Objective

Make `Skipper` answer through the intended visible CLI session without relying on hidden CLI fallback.

## Owner

- Primary: `Latch`
- Support: `Skipper`

## Dependencies

- Existing `skipper-tui-nats-bridge.service`
- Current route-state and heartbeat snapshots

## Steps

1. Inspect Skipper terminal launch path, window targeting, cwd, and profile binding.
2. Distinguish terminal absence from Hermes session persistence failure.
3. Tighten bridge diagnostics around visible-window detection and persisted-turn capture.
4. Relaunch Skipper path and run repeated direct NATS proofs.

## Acceptance

- Five consecutive `nova.skipper.direct` prompts land in the intended visible CLI session.
- No fallback is required during the proof set.
- Route-state snapshot reports `visible-ready` or equivalent steady visible mode.

## Rollback

- Keep fallback enabled in the existing bridge service.
- Revert to current mixed visible/fallback posture if the visible path regresses.
