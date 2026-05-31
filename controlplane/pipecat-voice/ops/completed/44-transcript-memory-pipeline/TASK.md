# Transcript Memory Pipeline

## Status

completed

## Objective

Create a canonical transcript event schema and durable handoff path so CommsOps
turns are available to memory, analytics, and audit consumers.

## Owner

CommsOps with MemOps handoff.

## Dependencies

- Hermes session stores.
- CX Pipe room history.
- NATS/RedPanda/Temporal availability.
- Memory database ingestion owner.

## Steps

1. Inventory current transcript sources and duplicate/conflicting schemas.
2. Define `TurnEvent` with route, session, actor, room, provider, latency, text,
   and audio metadata.
3. Emit events from the gateway/bridge path without blocking hot voice turns.
4. Add durable workflow handoff for ingestion and backfill.
5. Validate replay, dedupe, and redaction behavior.

## Acceptance

- Every spoken or typed CommsOps turn has a canonical event.
- Event payloads contain enough metadata for route debugging and memory ingest.
- Secrets and provider credentials are never serialized.
- Failed turns are recorded with failure class and component.
- Memory ingestion can consume events without scraping UI text.

## Rollback

Disable transcript event emission and keep existing room/session history paths
unchanged.
