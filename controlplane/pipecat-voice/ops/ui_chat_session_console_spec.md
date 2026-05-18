# UI Chat Session Console Spec

## 2026-05-18 15:38:34 — SIGNED_BY_AGENT

## Purpose

Build a NovaOps chat/session console that exposes the live NATS-to-agent path, visible Echo CLI state, task context, and workspace handoff in one operator surface. The design adapts the three-panel Hermes workbench pattern without copying external UI code.

## Source Patterns

- From `nesquena/hermes-webui`: three-panel layout, composer footer controls, context ring, workspace file preview, quiet tool/activity disclosure, slash-command parity.
- From `EKKOLearnAI/hermes-web-ui`: per-session run queue, abort/resume events, usage updates, bridge/API source split, terminal handoff, profile/gateway awareness.
- From NovaOps runtime: `nova.<name>.direct`, `reply_to` inboxes, Echo visible TUI bridge, task board workflow, Paperclip docs, systemd service ownership.

## Information Architecture

### Left Rail

- Nova roster with status from `nova.<name>.ping`.
- Subject ownership badge: `tui`, `hermes`, `switch`, `unassigned`.
- Filters: direct, meet, fleet, logs, metrics.
- Task board summary: `to_do`, `in_progress`, `completed`, active task folder.

### Center Transcript

- Conversation stream grouped by NATS event id.
- User prompt, typed visible prompt, assistant reply, and reply-capture status shown as one turn.
- Activity row collapsed by default: inbound, queued, typed, completed, reply_captured, timeout/error.
- Long outputs rendered as readable assistant prose with raw payload hidden behind expansion.

### Right Rail

- Active task folder with `TASK.md`, `completion_report.md`, and relevant ops docs.
- Workspace file browser rooted at the current repo or `/adapt/novas/active/<name>`.
- Visible CLI details: window title, PID, cwd, active Hermes session id, last message id.
- Paperclip sync links for docs/config packages.

### Composer Footer

- Target selector: nova name plus subject type.
- Delivery mode: normal, queue, interrupt, steer.
- Timeout and retry display, defaulting to the live platform values.
- Model/profile selector as read-only until credential-safe config editing is implemented.
- Send, stop, focus terminal, open task folder, and attach file actions.

## Data Contracts

### Send Envelope

Required fields:

- `id`: unique event id.
- `from`: operator or agent name.
- `message`: prompt text.
- `reply_to`: NATS inbox for streamed reply chunks.
- `timestamp`: Unix timestamp.

Optional fields:

- `session_id`
- `task_id`
- `workspace`
- `delivery_mode`
- `timeout_seconds`

### Reply Events

The UI should accept chunked reply payloads with:

- `id`
- `chunk`
- `final`
- `error`
- `trace`

The visible Echo bridge trace events are authoritative for delivery state. Assistant content is authoritative only after `reply_captured`.

## Terminal Handoff

Echo starts as the reference implementation:

- focus current Echo CLI window;
- show cwd from `/proc/<pid>/cwd`, not inferred model output;
- display active profile and model without printing secrets;
- surface stale-token/provider errors from logs with credential values redacted;
- support a future "open nova CLI" action that launches from `/adapt/novas/active/<name>`.

## Implementation Slices

1. Read-only roster/status panel backed by NATS pings and service status.
2. NATS send form with reply inbox streaming and trace timeline.
3. Echo visible state card backed by xdotool, process cwd, and session DB metadata.
4. Task/document right rail backed by the ops task directories.
5. Terminal focus/open actions with guardrails and audit logging.

## Tests And QA

- Unit test envelope building, redaction, and trace state transitions.
- Integration smoke sends one Echo prompt and verifies reply text plus trace ordering.
- Playwright desktop and mobile screenshots with long answer, collapsed activity, open right rail, and terminal focus action.
- Dogfood report must include viewport sizes, service state, NATS event id, and screenshot path.

## Boundaries

- Do not copy Nesquena static modules or EKKO Vue components.
- Do not expose profile config or token files in the browser.
- Do not make the UI a subject owner; it sends requests and reads replies/logs.

**— SIGNED_BY_AGENT**
