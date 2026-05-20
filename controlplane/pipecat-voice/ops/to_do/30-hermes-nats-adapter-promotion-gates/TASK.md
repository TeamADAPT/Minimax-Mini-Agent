# 30 Hermes NATS Adapter Promotion Gates

## Objective

Define and run the promotion gates for moving the Hermes/NATS adapter from spike or isolated subjects toward a live ownership candidate.

## Owner

- Primary: `Latch`
- Support: `Tecton`

## Dependencies

- Task `24`
- Task `29`
- Existing Rust/NATS adapter project

## Steps

1. Inventory current adapter spike/scaffold state and isolated subjects.
2. Define promotion gates for correlation id, reply inbox, logs, rollback, and duplicate-owner prevention.
3. Run isolated NATS proof without stealing `nova.echo.direct` or `nova.skipper.direct`.
4. Produce a go/no-go report for live-owner promotion.

## Acceptance

- Promotion gates are documented and at least one isolated proof result is recorded.
- Live subject ownership remains unchanged unless an explicit later task approves promotion.

## Rollback

- Keep the adapter on isolated subjects and restart the existing TUI bridge owners if any duplicate ownership appears.
