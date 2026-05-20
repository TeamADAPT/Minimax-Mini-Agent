# 26 Paperclip Fleet Sync Refresh

## Objective

Refresh the Paperclip-facing fleet package so it reflects current roles, routes, and constraints.

## Owner

- Primary: `Latch`
- Support: `Skipper`

## Dependencies

- Current route-state, heartbeat, and orchestration contract

## Steps

1. Review current Paperclip-facing docs and adapters.
2. Sync active roles, real route posture, and current constraints.
3. Remove stale assumptions about inactive or superseded paths.

## Acceptance

- Paperclip reflects the actual fleet instead of historical assumptions.

## Rollback

- Preserve previous docs until the refreshed package is verified.
