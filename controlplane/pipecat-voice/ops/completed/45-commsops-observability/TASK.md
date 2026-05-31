# CommsOps Observability

## Status

completed

## Objective

Build an operator-grade activity page showing CommsOps health from high level
fleet status down to per-turn route, provider, transcript, and latency detail.

## Owner

CommsOps.

## Dependencies

- Existing dashboard and activity pages.
- NATS monitor websocket.
- Session-state API.
- Transcript event schema from Task 44.

## Steps

1. Define high-level health cards: gateway, NATS, route owners, agents, voice
   providers, transcript pipeline.
2. Add time-series charts for turns, latency, error classes, and provider usage.
3. Add drill-down tables for per-agent route status and recent failures.
4. Add mobile-safe views for phone operation.
5. Verify desktop and mobile with Playwright screenshots.

## Acceptance

- The page answers whether CommsOps is healthy in under ten seconds.
- Operators can drill from fleet health to a single failed turn.
- Graphs are backed by live or clearly labeled derived data.
- Mobile layout is usable from the phone control surface.
- No secrets appear in browser payloads.

## Rollback

Hide the new activity page route and keep existing dashboard surfaces unchanged.
