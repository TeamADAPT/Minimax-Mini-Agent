# 32 Pipecat Direct NATS Session Hook

## Objective

Design and implement the first safe hook for routing pipecat voice turns directly into active NATS-backed sessions.

## Owner

- Primary: `Latch`
- Support: `Vox`, `Echo`

## Dependencies

- Task `20`
- Task `21`
- Task `24`
- Current pipecat gateway service state

## Steps

1. Trace the current STT to chat-completions to NATS to reply path.
2. Define the direct-session routing contract and failure classes.
3. Add a read-only or guarded first hook that exposes selected route/session targets without changing default voice behavior.
4. Verify with dry-run or non-audio route tests before any live voice turn.

## Acceptance

- A guarded pipecat-to-NATS session hook exists or has a precise implementation report.
- Default voice behavior is preserved until Task `22` validates end-to-end turns.

## Rollback

- Disable the hook by config flag and preserve the current gateway route.
