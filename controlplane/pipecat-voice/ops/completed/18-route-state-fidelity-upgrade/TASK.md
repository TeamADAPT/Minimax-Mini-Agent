# 18 Route State Fidelity Upgrade

## Objective

Upgrade `crew_route_state.json` so it explains real routing posture without manual journal inspection.

## Owner

- Primary: `Latch`

## Dependencies

- Tasks `16` and `17`
- Existing route-state snapshot writer

## Steps

1. Add explicit route modes such as `visible-ready`, `visible-missing`, `fallback-active`, and `bridge-down`.
2. Include latest proof timestamp, latest reply mode, and relevant bridge service state.
3. Make the snapshot stable enough for UI consumption.

## Acceptance

- Route-state output explains why an agent is healthy, degraded, or on fallback.
- UI/backend consumers can read the snapshot without additional journal lookups.

## Rollback

- Keep the current route-state schema if the expanded schema breaks downstream consumers.
