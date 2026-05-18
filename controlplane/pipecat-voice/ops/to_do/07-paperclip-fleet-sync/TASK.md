# Paperclip Fleet Sync

## Status

to_do

## Suggested Owner

Skipper

## Objective

Synchronize Nova fleet docs, configs, operational conventions, and current NATS/Hermes bridge state into `/adapt/platform/novaops/controlplane/paperclip`.

## Files And Sources

- Source: `/adapt/platform/novaops/controlplane/pipecat-voice/ops/`
- Source: `/adapt/novas/active/skills_master/autonomous-ai-agents/hermes-agent-ops/SKILL.md`
- Source: `/adapt/novas/active/skills_master/devops/nova-nats-ops/SKILL.md`
- Source: `/home/x/.hermes/profiles/<name>/config.yaml` metadata only, no secrets
- Target: `/adapt/platform/novaops/controlplane/paperclip`

## Instructions For Skipper

Skipper: build a Paperclip-facing fleet sync package. Do not copy secrets. Redact tokens and auth values. Preserve exact paths, service names, subject names, and workflow rules. Create a concise docs/config inventory that another agent can use to operate the Nova fleet without rediscovery.

## Steps

1. Move this folder to `ops/in_progress/`.
2. Inspect Paperclip repo structure and existing docs conventions.
3. Create a fleet sync destination under Paperclip, following existing repo style.
4. Copy or summarize:
   - NATS subject map
   - service map
   - profile/active-directory map
   - current Echo bridge state
   - ops workflow
   - new skills and how to use them
5. Redact all secrets.
6. Add a validation checklist.
7. Write `completion_report.md`.
8. Move this folder to `ops/completed/`.
9. Commit and push.

## Acceptance

- Paperclip contains a usable fleet operations package.
- No secrets are copied.
- Skipper can maintain it going forward.

## Revert

Remove only the new Paperclip sync docs/package and restore previous Paperclip state from git.

