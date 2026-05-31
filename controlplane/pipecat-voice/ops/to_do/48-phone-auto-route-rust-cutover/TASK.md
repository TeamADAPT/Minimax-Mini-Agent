# Phone Auto Route Rust Cutover

## Status

to_do

## Objective

Move the phone/browser `auto` route for repaired agents from visible-terminal
or legacy daemon paths onto the proven runtime-scoped Rust API-session route.

## Owner

CommsOps.

## Context

Task 42 proved native Rust API-session delivery for `commscanary`, Iris, Echo,
and Tecton. Task 47 repaired Iris, Echo, and Tecton provider/model routes.

The next change should update the phone/browser control path deliberately,
without hiding the route switch inside transport repair.

## Steps

1. Inspect gateway route selection for solo and room sends.
2. Identify where `auto` chooses `tui`, `hermes`, `fresh`, or `rust`.
3. Change only repaired agents to prefer `rust`.
4. Preserve explicit runtime override buttons.
5. Run phone/API send proofs for Iris, Echo, and Tecton.
6. Verify transcripts and route metadata are visible in activity surfaces.
7. Document rollback.

## Acceptance

- Phone/browser send to Iris, Echo, and Tecton uses `nova.<agent>.rust.direct`
  when `auto` is selected.
- Explicit non-rust runtime overrides still work.
- Route metadata is visible to the caller or activity stream.
- Voice/TTS receives denoised text.
- Rollback to prior `auto` behavior is documented.

## Rollback

Restore the previous route selection map and restart `pipecat-voice.service`.
