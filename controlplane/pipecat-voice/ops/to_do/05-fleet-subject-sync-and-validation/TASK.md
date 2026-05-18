# Fleet Subject Sync And Validation

## Status

to_do

## Objective

Synchronize the Nova fleet's NATS subjects, active profile directories, and bridge ownership so every nova has one clear runtime path.

## Files And Systems

- Read: `/home/x/.hermes/profiles/*/config.yaml`
- Read: `/adapt/novas/active/<name>`
- Read/modify: `scripts/hermes_nats_agents.py`
- Read/modify: `roster.json`
- Read/modify: systemd user services if needed
- Update: `ops/operations_history.md`
- Update: `ops/decisions.log`

## Steps

1. Move this folder to `ops/in_progress/`.
2. Inventory fleet profiles: Echo, Tecton, Herald, Iris, Vaeris, Synergy, Cosmos, Pathfinder, Zap, Oracle, Vox, Skipper.
3. For each, verify active directory and profile config.
4. For each, verify NATS ping response or document why absent.
5. Check duplicate subscriptions and hidden bridge ownership.
6. Ensure runtime cwd resolves to `/adapt/novas/active/<name>` where possible.
7. Produce a fleet matrix with subject owner, cwd, model/provider, and service path.
8. Fix low-risk mismatches.
9. Create task folders for high-risk fixes instead of changing them inline.
10. Write `completion_report.md`.
11. Move this folder to `ops/completed/`.
12. Commit and push.

## Acceptance

- Fleet matrix exists.
- Every active NATS subject has one owner.
- Any dangerous fix is decomposed into its own task folder.

