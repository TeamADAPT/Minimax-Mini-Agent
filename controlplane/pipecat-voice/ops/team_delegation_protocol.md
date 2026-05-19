# Team Delegation Protocol

## 2026-05-18 15:42:28 — SIGNED_BY_AGENT

## Ownership Rule

Latch owns this project. Other novas may research, review, test, draft, or implement bounded work, but Latch remains responsible for:

- selecting and moving task folders;
- approving write scopes;
- integrating outputs;
- writing or accepting completion reports;
- logging operations and decisions;
- committing, pushing, and reverting.

No delegated nova should perform destructive actions, edit secrets, change systemd ownership, or move task folders unless the task explicitly grants that authority.

## Live Route Table

Validated pings on 2026-05-18 21:12:26.

| Agent | Route | Owner | Active dir | Best role | Status |
| --- | --- | --- | --- | --- | --- |
| Echo | `nova.echo.direct` | `echo-tui-nats-bridge.service` | `/adapt/novas/active/echo` | visible CLI proof, UX feedback, long-answer validation | `pong:echo:tui` |
| Tecton | `nova.tecton.direct` | `pipecat-hermes-agents.service` | `/adapt/novas/active/tecton` | runtime implementation, adapter hardening, transport review | `pong:tecton:hermes` |
| Vaeris | `nova.vaeris.direct` | `pipecat-hermes-agents.service` | `/adapt/novas/active/vaeris` | architecture review, risk analysis, memory/continuity notes | `pong:vaeris:hermes` |
| Iris | `nova.iris.direct` | `pipecat-hermes-agents.service` | `/adapt/novas/active/iris` | QA, screenshots, observability checks, user-facing proof | `pong:iris:hermes` |
| Herald | `nova.herald.direct` | `pipecat-hermes-agents.service` | `/adapt/novas/active/herald` | lifecycle dispatch, coordination notices | `pong:herald:hermes` |
| Synergy | `nova.synergy.direct` | `pipecat-hermes-agents.service` | `/adapt/novas/active/synergy` | integration review and cross-agent synthesis | `pong:synergy:hermes` |
| Cosmos | `nova.cosmos.direct` | `pipecat-hermes-agents.service` | `/adapt/novas/active/cosmos` | broad planning, long-context review | `pong:cosmos:hermes` |
| Pathfinder | `nova.pathfinder.direct` | `pipecat-hermes-agents.service` | `/adapt/novas/active/pathfinder` | route discovery, alternatives, migration maps | `pong:pathfinder:hermes` |
| Oracle | `nova.oracle.direct` | `pipecat-hermes-agents.service` | `/adapt/novas/active/oracle` | decision review, acceptance criteria, edge cases | `pong:oracle:hermes` |
| Vox | `nova.vox.direct` | `pipecat-hermes-agents.service` | `/adapt/novas/active/vox` | voice pipeline checks and CX path review | `pong:vox:hermes` |
| Zap | `nova.zap.direct` | `pipecat-hermes-agents.service` | `/adapt/novas/active/zap` | quick probes and small smoke tests | `pong:zap:hermes` |
| Switch | `nova.switch.direct` | `switch_agent.py` | n/a | routing switchboard only | `pong` |
| Skipper | `nova.skipper.direct` | `pipecat-hermes-agents.service` | `/adapt/novas/active/skipper` | Paperclip docs/package owner, release/docs sync, completion-report packaging | `pong:skipper:hermes` |

Skipper is now a live NATS route. Direct proof `skipper-proof-0cf7238c` returned `SKIPPER NATS OK` through `reply_to`.

## Delegation Envelope

Send direct NATS messages as structured JSON. Required fields:

```json
{
  "id": "delegation-unique-id",
  "from": "latch",
  "message": "bounded task prompt",
  "reply_to": "_INBOX...",
  "timestamp": 0
}
```

The prompt must include:

- objective;
- allowed files or read-only scope;
- forbidden actions;
- expected output format;
- deadline/timeout;
- where to put artifacts if write access is granted;
- instruction to avoid secrets and redact logs.

## Output Contract

Delegated results must come back as one of:

- short review with file/line references;
- implementation patch in an assigned write scope;
- QA report with screenshots/log snippets redacted;
- architecture or design note;
- completion-report draft.

Latch converts accepted output into:

- task docs;
- `completion_report.md`;
- `ops/operations_history.md`;
- `ops/decisions.log`;
- commits and pushes.

## Role Playbooks

### Echo

- Use for visible proof only when the operator needs confidence that NATS reached the foreground session.
- Prefer prompts that include explicit confirmation markers and enough detail to exercise long responses.
- Do not ask Echo to mutate ops files through the visible bridge unless a task grants that scope.

### Tecton

- Use for runtime and transport implementation reviews.
- Give exact files and rollback expectation.
- Require smoke commands and failure modes.

### Vaeris

- Use for architecture risks, memory/continuity, and plan critique.
- Ask for concrete blockers and alternative designs, not generic commentary.

### Iris

- Use for QA, screenshots, log inspection, and dogfood reports.
- Require evidence paths and viewport/service state.

### Skipper

- Use for Paperclip docs packaging, release/documentation sync, and completion-report drafting.
- Route through `nova.skipper.direct`.
- Keep Skipper read-only unless a task explicitly grants a file write scope.
- Latch still moves task folders and commits accepted output.

## Escalation Rules

- Provider/auth failure: stop delegation for that agent, record blocker, fall back to another reachable nova.
- Duplicate subject owner: stop the newer or fallback owner, log the change, re-ping.
- Destructive request ambiguity: do not delegate; Latch clarifies or writes the task.
- Secret exposure risk: halt, redact, and document the boundary before continuing.
- Long-running task: require periodic status via `nova.logs.<name>` or task notes.

## Rollback Rules

- Every delegated code change must identify touched files and a rollback command.
- Systemd changes must include prior state, new state, and exact restart/disable commands.
- For Echo, rollback owner is `echo-tui-nats-bridge.service` unless a native owner is explicitly promoted.
- For core novas, rollback owner is `pipecat-hermes-agents.service`.
- For Paperclip sync, rollback is a git revert in the Paperclip repo plus a NovaOps doc update.

## Example Delegation Prompt

```text
Latch delegation for Tecton.

Objective: review scripts/echo_tui_nats_bridge.py for race conditions in reply capture.
Scope: read-only; do not edit files.
Forbidden: no service restarts, no config reads containing secrets, no git commands.
Output: findings ordered by severity, exact file/line references, and suggested smoke tests.
Return a concise report suitable for inclusion in a task completion report.
```

**— SIGNED_BY_AGENT**
