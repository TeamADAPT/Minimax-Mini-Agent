# 20 Dashboard Session Voice Observability

## Objective

Add session, route, and voice health visibility to the existing pipecat dashboard.

## Owner

- Primary: `Latch`
- Support: `Echo`

## Dependencies

- Task `19`
- Existing dashboard and status websocket surfaces

## Steps

1. Add agent cards for `echo`, `skipper`, `testova`, and `latch`.
2. Add route-mode indicators, last-proof timestamps, and voice/gateway/NATS health strips.
3. Remove or demote noisy panels that do not help operations.
4. Verify the page is useful on desktop and mobile.

## Acceptance

- Loading the dashboard gives actionable route and voice state within thirty seconds.
- Operators can identify visible vs fallback posture immediately.

## Rollback

- Keep the old dashboard available until the new surface proves more useful.
