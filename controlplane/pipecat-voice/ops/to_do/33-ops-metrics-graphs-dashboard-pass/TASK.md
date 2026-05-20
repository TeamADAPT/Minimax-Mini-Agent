# 33 Ops Metrics Graphs Dashboard Pass

## Objective

Add the next operator-facing metrics and graph slice for route health, proof latency, voice gateway state, and NATS traffic.

## Owner

- Primary: `Echo`
- Support: `Iris`, `Latch`

## Dependencies

- Task `20`
- Task `21`
- Current `/api/session-state` and `/ws/monitor` surfaces

## Steps

1. Identify the highest-value metrics from existing runtime snapshots and monitor events.
2. Add compact graphs or counters without adding noisy panels.
3. Verify desktop and mobile layout with screenshots.
4. Record which metrics are real, derived, or placeholders.

## Acceptance

- Dashboard or monitor shows actionable route/voice/NATS metrics without raw JSON hunting.
- Screenshots and console checks prove the UI is usable on desktop and mobile.

## Rollback

- Remove the metrics slice and preserve the current dashboard/monitor pages.
