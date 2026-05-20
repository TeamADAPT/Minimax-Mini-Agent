# Paperclip Nova Adapter Package Plan

## 2026-05-19 22:25:51 — SIGNED_BY_AGENT

## Purpose

Package the Adapt Nova/Hermes route surface as a Paperclip external adapter
without moving live subject ownership away from the current NovaOps bridges.
Paperclip should get a redacted, operable adapter surface for route selection,
run execution, transcript rendering, and health checks while NovaOps remains the
source of truth for services, secrets, route ownership, and rollback.

## Source Constraints

This plan is based on:

- Paperclip external adapter docs:
  `/adapt/platform/novaops/controlplane/paperclip/docs/adapters/external-adapters.md`
- Paperclip adapter authoring docs:
  `/adapt/platform/novaops/controlplane/paperclip/docs/adapters/creating-an-adapter.md`
- Paperclip UI parser contract:
  `/adapt/platform/novaops/controlplane/paperclip/docs/adapters/adapter-ui-parser.md`
- Current Nova fleet notes:
  `/adapt/platform/novaops/controlplane/paperclip/docs/adapters/nova-fleet-ops.md`
- NovaOps source-of-truth snapshot:
  `/adapt/platform/novaops/controlplane/pipecat-voice/ops/runtime/crew_route_state.json`
- Skipper orchestration contract:
  `/adapt/platform/novaops/controlplane/pipecat-voice/ops/skipper_orchestration_contract.md`
- Task 30 adapter gate result:
  `/adapt/novas/active/projects/nats-adapter/PROMOTION_GATES.md`

## Package Shape

Package name: `@adaptnova/paperclip-adapter-nova-nats`

Adapter type: `nova_nats`

Recommended structure:

```text
paperclip-adapter-nova-nats/
  package.json
  tsconfig.json
  src/
    index.ts
    server/
      index.ts
      execute.ts
      nats-client.ts
      route-state.ts
      test.ts
    ui-parser.ts
```

Required exports:

```json
{
  "type": "module",
  "paperclip": {
    "adapterUiParser": "1.0.0"
  },
  "exports": {
    ".": "./dist/index.js",
    "./server": "./dist/server/index.js",
    "./ui-parser": "./dist/ui-parser.js"
  }
}
```

The package should be installed as an external adapter by npm package name or
absolute local path. It should not require a Paperclip source-tree change.

## Adapter Config Schema

Paperclip may store only redacted operational metadata:

```json
{
  "routeName": "echo",
  "role": "execution",
  "subject": "nova.echo.direct",
  "pingSubject": "nova.echo.ping",
  "logsSubject": "nova.logs.echo",
  "routeOwner": "echo-tui-nats-bridge.service",
  "routePosture": "visible-ready",
  "modelLabel": "qwen/qwen3.5-397b-a17b",
  "providerLabel": "nvidia",
  "activeDir": "/adapt/novas/active/echo",
  "replyTimeoutSec": 240,
  "promptTemplate": "{{taskTitle}}\n\n{{taskBody}}",
  "allowDirectExecution": true,
  "allowFallbackRoute": false
}
```

Do not store:

- auth JSON
- OAuth tokens
- API keys
- full NATS URLs with credentials
- profile `.env` values
- raw Hermes profile config
- raw NATS payload logs by default

Credential resolution must happen at runtime from the host environment or a
NovaOps-owned secret source, not from Paperclip agent config.

## Execution Contract

`execute(ctx)` should:

1. Read redacted adapter config with strict validation.
2. Build a stable event id from the Paperclip run id.
3. Render the prompt from Paperclip task context and `promptTemplate`.
4. Publish a structured JSON envelope to `subject` with `reply_to`.
5. Stream reply chunks into `ctx.onLog("stdout", chunk)`.
6. Emit metadata for route owner, proof id, provider, model, and route posture.
7. Return session params containing only redacted route/session identifiers.
8. Fail closed on timeout with a clear `errorMessage`.

Envelope shape:

```json
{
  "id": "paperclip-<run-id>",
  "from": "paperclip",
  "to": "echo",
  "message": "rendered task prompt",
  "reply_to": "_INBOX...",
  "timestamp": 1779140000
}
```

The first implementation must not subscribe as a competing owner on
`nova.echo.direct` or `nova.skipper.direct`. It should only request through the
existing owner bridge.

## UI Fields

Default Paperclip surfaces should show compact route status without raw JSON:

| Field | Source | Notes |
| --- | --- | --- |
| Nova | adapter config | Display name such as Echo, Skipper, Testova, Latch. |
| Role | adapter config | `orchestrator`, `execution`, `validation`, or `operator-inbox`. |
| Subject | adapter config | Redacted subject only, no URL. |
| Owner | adapter config plus route snapshot | Example: `echo-tui-nats-bridge.service`. |
| Route posture | `crew_route_state.json` or session API | `visible-ready`, `visible-missing`, `fallback-active`, `bridge-down`, `held`. |
| Latest proof | route snapshot or run metadata | Event id plus timestamp. |
| Blocker | route snapshot or static constraints | Example: Testova held, fallback disabled, duplicate owner risk. |
| Reply timeout | adapter config | Operator-visible, bounded. |
| Provider/model | redacted metadata | Labels only, not credentials. |

Raw `nova.logs.<name>` events should be available behind progressive disclosure
for debugging, not as the default run transcript.

## UI Parser Contract

Ship `src/ui-parser.ts` as a zero-import module under 50 KB. The parser should
recognize adapter-emitted lines:

```text
[nova-route] subject=nova.echo.direct owner=echo-tui-nats-bridge.service posture=visible-ready
[nova-proof] id=paperclip-... latest=task24-...
[nova-error] code=timeout route=nova.echo.direct
```

Map route/proof lines to `system`, answer chunks to `assistant`, and errors to
`stderr` or failed `tool_result` entries. The parser must never throw; fallback
to `stdout` for unknown lines.

## Data Boundaries

Paperclip is allowed to own:

- adapter package metadata
- redacted route configs
- task prompts
- run logs and assistant replies
- latest proof ids and timestamps
- route-posture display fields

NovaOps remains the owner for:

- NATS credentials and connection URLs
- Hermes auth stores
- live systemd service ownership
- active CLI windows
- route-state generation
- operational decisions, rollbacks, and task-folder movement

## Implementation Plan

| Step | Owner | Files | Verification |
| --- | --- | --- | --- |
| Scaffold package | Skipper/Latch | `paperclip-adapter-nova-nats/package.json`, `tsconfig.json`, `src/index.ts` | `pnpm build` |
| Server adapter | Latch | `src/server/index.ts`, `src/server/execute.ts`, `src/server/nats-client.ts` | Unit test request envelope, timeout, config validation |
| Route state reader | Latch | `src/server/route-state.ts` | Fixture test for `visible-ready`, `held`, and missing snapshot |
| Environment test | Latch | `src/server/test.ts` | Diagnostics for missing NATS env, invalid subject, held route |
| UI parser | Echo/Latch | `src/ui-parser.ts` | Parser fixture tests, no runtime imports |
| Paperclip install dry run | Latch | external adapter install command | Local-path install, environment test pass |
| Live non-destructive proof | Skipper/Latch | Paperclip run using Echo route | Reply inbox proof id captured without changing owner |

## Verification Gates

Before acceptance:

```bash
pnpm --filter @adaptnova/paperclip-adapter-nova-nats typecheck
pnpm --filter @adaptnova/paperclip-adapter-nova-nats test
pnpm --filter @adaptnova/paperclip-adapter-nova-nats build
```

Adapter-specific gates:

- config validation rejects secrets and full credentialed URLs
- `testEnvironment` returns `fail` for held or bridge-down routes
- dry-run execution does not publish to live subjects
- live proof uses existing `reply_to` flow and does not start a second owner
- timeout path returns a bounded failure
- UI parser handles route/proof/error lines without throwing
- no raw NATS URL or secret appears in Paperclip logs

## Rollback

Remove or disable the external adapter package from Paperclip and keep the Nova
fleet as documentation-only. Do not stop `echo-tui-nats-bridge.service` or
`skipper-tui-nats-bridge.service` for rollback unless a concrete duplicate-owner
fault is observed.

**— SIGNED_BY_AGENT**
