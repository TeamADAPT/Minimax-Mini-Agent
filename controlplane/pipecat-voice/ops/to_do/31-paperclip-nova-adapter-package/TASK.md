# 31 Paperclip Nova Adapter Package

## Objective

Turn the refreshed Paperclip fleet notes into a concrete external-adapter package plan for Nova/Hermes routes.

## Owner

- Primary: `Skipper`
- Support: `Latch`

## Dependencies

- Task `23`
- Task `26`
- Paperclip external adapter/plugin constraints

## Steps

1. Review Paperclip adapter/plugin expectations and current Nova fleet notes.
2. Define the redacted adapter config schema for Nova route targets.
3. Define the UI fields Paperclip should show for route posture, owner, latest proof, and blocker.
4. Produce an implementation plan with files, owners, and verification commands.

## Acceptance

- A Paperclip adapter package plan exists with config schema, UI fields, data boundaries, and verification gates.

## Rollback

- Keep the Nova fleet as documentation-only in Paperclip until the adapter package plan is accepted.
