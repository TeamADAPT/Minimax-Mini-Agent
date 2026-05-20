# Skipper Orchestration Contract

## 2026-05-19 21:06:39 — SIGNED_BY_AGENT

This contract defines how Skipper issues and tracks work across the Nova crew from the current NATS-backed operating surface. It narrows the broader `ops/team_delegation_protocol.md` into the exact assignment format Skipper should use for Echo, Testova, and Latch handoffs.

## Operating Rule

Skipper owns orchestration. Latch owns integration, task-folder movement, final acceptance, commits, pushes, and rollback execution. Echo executes bounded work through the visible route. Testova validates until the held visible-session proof gate is complete.

## Current Route Caveat

At the time this contract was written, `nova.skipper.ping` returned `pong:skipper:tui`, but the `Skipper CLI` desktop window was not discoverable and the bridge fell back to hidden CLI handling for the Task 23 contract prompt. `crew_route_state.json` also reported Echo as `visible-missing` and Skipper as `fallback-active`.

Skipper can use this contract immediately for assignment structure, but visible-terminal proof must be re-established before claiming that Skipper or Echo are operating in stable visible-only mode.

## Required Delegation Envelope

Every Skipper-issued task must include these fields in the natural-language prompt and, when sent over NATS, in the JSON envelope metadata where applicable.

```json
{
  "id": "skipper-task-<slug>-<nonce>",
  "from": "skipper",
  "to": "echo|testova|latch",
  "subject": "nova.<agent>.direct",
  "objective": "one bounded outcome",
  "owner": "single accountable nova",
  "support": ["optional supporting novas"],
  "scope": ["allowed files, dirs, commands, or read-only surfaces"],
  "forbidden": ["destructive commands", "secret exposure", "unowned files"],
  "acceptance": ["observable pass/fail criteria"],
  "proof_expected": ["test output", "screenshot path", "NATS event id", "report path"],
  "checkback_subject": "nova.skipper.direct",
  "timeout_minutes": 30,
  "rollback": "specific rollback or safe stop condition"
}
```

Minimum viable prompt format:

```text
Skipper assignment.

Objective: <one concrete deliverable>
Owner: <one nova>
Scope: <files/commands/systems allowed>
Forbidden: <actions not allowed>
Acceptance: <observable pass/fail gate>
Proof expected: <exact output paths, command output, NATS event id, or report>
Check back: nova.skipper.direct with id <task-id>
Timeout: <minutes>
Rollback/stop: <what to do if blocked>
```

## Route Contract

| Target | Primary route | Role | Required proof |
| --- | --- | --- | --- |
| Echo | `nova.echo.direct` | Execution, visible-session answers, UX/design feedback, long-form task responses | NATS event id plus output/report; visible route preferred when the operator needs confidence |
| Testova | `nova.testova.direct` | Validation, smoke checks, critique, failure classification | Validation report and exact command/screenshot/log evidence; no lead execution until 3/3 visible proof gate passes |
| Latch | `nova.latch.direct` | Integration, code edits, ops logs, commits, rollback | Completion report, ops logs, commit hash, pushed branch |
| Skipper | `nova.skipper.direct` | Assignment issue, status intake, reprioritization | Assignment id, owner, accepted proof, next action |

## Echo Handoff

Use Echo for small, executable work where visible interaction is useful or where a long answer validates the session path.

Echo assignments must include:

- one owner only: Echo;
- narrow scope with no cross-task writes;
- expected artifact path or response structure;
- explicit no-secret rule;
- checkback to `nova.skipper.direct`;
- escalation to Latch when file edits, service restarts, or git operations are needed.

Echo should not move task folders, commit, push, edit credentials, or restart services unless Latch explicitly grants that scope inside a task folder.

## Testova Handoff

Use Testova for validation-first work until Task 17 is accepted.

Testova assignments must include:

- read-only or test-only scope by default;
- expected validation output format;
- exact evidence required, such as command output, screenshot name, websocket event id, or failing route state;
- no dependence on visible-only delivery until the held 3/3 proof is resumed and completed;
- checkback to `nova.skipper.direct` and copy critical blockers to `nova.latch.direct`.

If Testova reports route instability, Skipper must keep Testova in validation-only mode and route execution elsewhere.

## Latch Handoff

Use Latch for integration, source edits, ops discipline, commits, pushes, production service changes, and rollback.

Latch handoffs must include:

- the task folder path;
- files or services expected to change;
- acceptance gates;
- required ops log entries;
- exact verification commands;
- whether production systemd restart is approved or deferred.

Latch returns:

- `completion_report.md`;
- updated `ops/operations_history.md`;
- updated `ops/decisions.log`;
- commit hash;
- push result;
- unresolved risks.

## Status Cadence

Skipper tracks each assignment in one of these states:

- `issued`: sent to the owner, no acknowledgement yet;
- `accepted`: owner acknowledged scope and proof;
- `working`: owner is executing;
- `blocked`: owner returned a blocker with evidence;
- `proof-ready`: owner returned proof for review;
- `accepted-complete`: Latch or Skipper accepted the proof;
- `stale`: no checkback before timeout;
- `reassigned`: original owner stopped and work moved to another owner.

For tasks longer than 30 minutes, Skipper requires a status checkback every 30 minutes or at each material state change.

## Escalation Rules

- Provider/auth failure: mark `blocked`, record the provider class only, and reassign if another nova can continue.
- No NATS reply: ping the target subject, inspect bridge ownership, then reassign or ask Latch to repair transport.
- Visible-session miss: do not count logs as visible proof; route to fallback only if the task allows it.
- Scope ambiguity: stop and ask Latch for a sharper task boundary.
- Secret exposure risk: stop immediately; do not quote token values; ask Latch to scrub or rotate as a separate task.
- Destructive command needed: stop unless Latch explicitly approved the command in the task scope.
- Stale task: send one status probe; after the timeout grace window, mark stale and reassign.

## Stale-Task Handling

1. At timeout, Skipper sends a single status probe to the owner.
2. If no answer arrives within 10 minutes, Skipper marks the assignment `stale`.
3. Skipper records the stale state with task id, owner, last route, and missing proof.
4. Skipper either reassigns the work or asks Latch to recover the route.
5. If partial artifacts exist, Latch decides whether to preserve, revert, or discard them.

## Proof Acceptance

Skipper may accept planning, review, and coordination proof. Latch must accept proof for source edits, systemd changes, production service changes, ops task movement, commits, and pushes.

A proof is acceptable only when it includes:

- assignment id;
- owner;
- exact artifact or command evidence;
- pass/fail result;
- unresolved risks or `none`;
- next recommended action.

## Example Assignment

```text
Skipper assignment.

Objective: validate that /monitor renders direct NATS proof traffic without raw JSON hunting.
Owner: Testova
Scope: read-only browser/HTTP checks against the local gateway and screenshots only.
Forbidden: no file edits, no service restarts, no secrets, no git commands.
Acceptance: desktop and mobile screenshots show presets, active subscription, proof classification, and no visible overlap.
Proof expected: screenshot paths, console error count, and any failing selectors.
Check back: nova.skipper.direct with id skipper-task-monitor-validation-001.
Timeout: 30 minutes.
Rollback/stop: if the gateway is down, stop and report route/service state.
```

## Relationship To Paperclip

Paperclip should mirror the accepted state of this contract, not become the source of operational truth. The source of truth for active execution remains:

- task folders under `ops/to_do`, `ops/in_progress`, and `ops/completed`;
- `ops/operations_history.md`;
- `ops/decisions.log`;
- current NATS route state and visible-session proofs.

**— SIGNED_BY_AGENT**
