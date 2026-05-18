# Hermes UI Design Pattern Inventory

## 2026-05-18 15:36:11 — SIGNED_BY_AGENT

This inventory extracts reusable product and interaction patterns from local Hermes UI candidates and installed design-collaboration tools. It is intentionally a rebuild/adapt guide, not a code-copy plan.

## Source Inventory

### nesquena/hermes-webui

- Path: `/adapt/repos/gui/hermes/nesquena__hermes-webui`
- Local shape: Python server, vanilla JavaScript client, no build step, no frontend framework.
- Launch command: `./ctl.sh start` or `./start.sh`; previous local run was tracked as `http://127.0.0.1:28203/`.
- Useful references: `README.md`, `DESIGN.md`, `docs/UIUX-GUIDE.md`, `static/sessions.js`, `static/messages.js`, `static/workspace.js`, `static/terminal.js`, `static/commands.js`, `server.py`.
- Adaptable patterns:
  - Three-panel workbench: sessions/nav left, transcript center, workspace/files right.
  - Composer footer as command surface: model, profile, workspace, attachments, context usage, stop, send.
  - Context ring for at-a-glance token pressure.
  - Calm transcript hierarchy where assistant prose is primary and tool activity collapses into quieter metadata.
  - Workspace file browser with inline preview tied to the active session.
  - CLI parity through slash commands, queue/interrupt/steer semantics, session lifecycle, and terminal handoff.
  - Structured request logging and session recovery at server startup.

### EKKOLearnAI/hermes-web-ui

- Path: `/adapt/repos/gui/hermes/EKKOLearnAI__hermes-web-ui`
- Local shape: Vue 3, TypeScript, Koa BFF, Socket.IO, SQLite, node-pty, xterm, Naive UI.
- Launch command: `npm run start` defaults to Vite port `8648`; previous local run was tracked as `http://127.0.0.1:28204/`.
- Useful references: `README.md`, `docs/cli-chat-sessions.md`, `scripts/generate-openapi.mjs`, `packages/server/src/services/hermes/run-chat`, `packages/client/src/components/hermes`, `tests/server/usage-analytics-db.test.ts`, `tests/e2e/terminal.spec.ts`.
- Adaptable patterns:
  - Unified `/chat-run` stream protocol with per-session queue, abort, resume, approval, and usage events.
  - Session grouping by source, live active-session indicator, session search, model badge, and context usage.
  - Analytics pages for token input/output, session count, estimated cost, cache hit rate, model distribution, and time trends.
  - Logs page with agent/gateway/error source filters, level filters, keyword search, and structured HTTP log highlighting.
  - Integrated terminal via PTY/WebSocket with multiple named terminal sessions and resize support.
  - Gateway/profile management: profile clone/import/export, gateway start/stop/status, provider/model grouping.
  - Multi-agent chat rooms with invites, mentions, typing/progress, compression, and local persistence.

### Design-Collaboration Tooling

- Penpot desktop wrapper: installed as a desktop client, not a local self-hosted Penpot server.
- Excalidraw: `/adapt/repos/gui/collab-tools/excalidraw`; launch with `yarn start` from the repo when needed.
- Excalidraw room: `/adapt/repos/gui/collab-tools/excalidraw-room`; build with `yarn build`, run with `yarn start`, or develop with `yarn start:dev`.
- CryptPad: `/adapt/repos/gui/collab-tools/cryptpad`; launch with `npm start` or `npm run dev` when systemd packaging is created.
- OpenPencil/Pencil: local desktop install under `.local/share/net.dannote.open-pencil`; use for quick wireframes.
- Installed skills to keep in the design loop:
  - `design-md`: shared design-spec artifact.
  - `architecture-diagram`: clean infra/system diagrams.
  - `popular-web-designs`: reference patterns before inventing UI.
  - `dogfood`: structured UX QA after a prototype is live.
  - `sketch`: throwaway mockups before committing code.

## Adapted Platform Direction

### Chat And Session Console

Build from the Nesquena interaction model because it matches this environment's preference for low-friction ops surfaces: no frontend framework requirement, clear panels, and strong CLI parity. The platform variant should add fleet-specific state:

- left rail: nova roster, active routes, task board state, room/direct filters;
- center rail: Echo/NATS-visible transcript with collapsed activity groups and reply proof metadata;
- right rail: workspace/task/docs/file panel, including active task folder, completion report, and Paperclip links;
- composer controls: target nova, subject type, model/profile, queue/interrupt/steer mode, timeout, reply capture status;
- visible terminal handoff: open/focus Echo CLI, show cwd, PID, active session id, and last NATS event id.

### Analytics And Logs

Use EKKO as the feature inventory but implement the platform surface around our bus and systemd reality:

- NATS traces: inbound, queued, typed, completed, reply captured, timeout, error;
- service status: `nats-server`, `pipecat-voice`, `pipecat-hermes-agents`, `echo-tui-nats-bridge`, Switch;
- subject ownership matrix: one owner per `nova.<name>.direct`, ping result, source process, cwd;
- response health: duration, retries, provider/model, timeout, fallback, token/cost when available;
- log reader: journal units, `nova.logs.<name>`, gateway errors, task-operation entries, with redaction by default.

### Collaboration Workbench

Keep collaboration tools as complementary artifacts rather than a second control plane:

- `DESIGN.md` holds durable UI contracts and tokens.
- Excalidraw/architecture diagrams capture topology, routing, and state transitions.
- Penpot desktop/OpenPencil are for exploratory mockups before coding.
- CryptPad can host multi-person notes/spec drafting only after systemd service packaging and auth review.
- Dogfood reports become repeatable QA artifacts with screenshots, viewport notes, and task links.

## Non-Copy Boundary

- Do not port Vue/Naive UI, Koa route code, or Nesquena static modules directly into NovaOps.
- Do not copy auth, token storage, or credential display behavior from either candidate.
- Reuse only product concepts, state contracts, acceptance tests, and interaction patterns.
- Platform implementation should follow the current repo rules: systemd-managed services, no Docker, no venv, secrets from `/adapt/secrets/*.env`, and runtime artifacts gitignored.

## Decomposed Implementation Tasks

Created task folders:

- `ops/to_do/10-ops-ui-chat-session-console`
- `ops/to_do/11-ops-ui-analytics-logs`
- `ops/to_do/12-design-collaboration-workbench`

Each task is scoped as an implementable spec/plan artifact so it can be picked up independently without importing external app code.

**— SIGNED_BY_AGENT**
