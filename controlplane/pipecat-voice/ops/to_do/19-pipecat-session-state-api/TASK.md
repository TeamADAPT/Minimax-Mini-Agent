# 19 Pipecat Session State API

## Objective

Expose agent session, route, and proof state through a read-only pipecat API surface.

## Owner

- Primary: `Latch`

## Dependencies

- Task `18`
- Existing `gateway.py` status endpoints

## Steps

1. Extend the backend with a session-state summary endpoint or enrich an existing ops endpoint.
2. Include latest session id, route mode, bridge owner, proof freshness, and snapshot summaries.
3. Keep the API lightweight and safe for frequent polling.

## Acceptance

- One API response answers who is live, how they are routed, and what session they are on.
- Response is usable by dashboard and monitor surfaces.

## Rollback

- Leave the existing ops endpoints intact and gate the new endpoint behind a separate route if needed.
