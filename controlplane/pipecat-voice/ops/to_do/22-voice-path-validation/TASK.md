# 22 Voice Path Validation

## Objective

Verify end-to-end voice turns through pipecat and record exact failure classes when they occur.

## Owner

- Primary: `Echo`
- Support: `Latch`

## Dependencies

- Task `20`
- Live pipecat gateway, STT, TTS, and NATS paths

## Steps

1. Run multiple voice turns through the active peer path.
2. Confirm STT -> NATS -> reply -> TTS behavior.
3. Record latency, failure mode, and recovery notes for each failed path.

## Acceptance

- Three successful end-to-end voice turns.
- Each failing path is documented with a named root cause.

## Rollback

- Preserve the current voice path while capturing diagnostics; do not destabilize the gateway.
