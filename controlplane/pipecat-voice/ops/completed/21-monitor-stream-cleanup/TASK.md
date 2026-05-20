# 21 Monitor Stream Cleanup

## Objective

Make the live monitor useful for NATS debugging instead of a raw JSON firehose.

## Owner

- Primary: `Latch`

## Dependencies

- Task `19`
- Existing `/ws/monitor` stream

## Steps

1. Add practical presets for direct, ping, and logs traffic.
2. Improve rendering for proofs, route changes, and failures.
3. Reduce noise and make the active subscription state obvious.

## Acceptance

- The monitor can be used for live debugging without manual JSON hunting.

## Rollback

- Keep the current raw stream behavior behind a fallback preset.
