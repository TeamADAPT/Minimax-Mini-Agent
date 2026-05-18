# Design Collaboration Workbench Spec

## 2026-05-18 15:40:58 — SIGNED_BY_AGENT

## Purpose

Define a repeatable NovaOps design-collaboration loop that turns ideas into durable specs, diagrams, mockups, QA reports, and Paperclip-synced operating context without making design tools part of the runtime control plane.

## Tool Roles

### DESIGN.md

- Durable design-system contract for UI tokens, typography, spacing, components, accessibility, and rationale.
- Store in the repo next to the UI implementation once a design direction is accepted.
- Validate with the `design-md` workflow before implementation.

### Architecture Diagrams

- Use `architecture-diagram` for system topology, service ownership, NATS route maps, data flows, and deployment diagrams.
- Store generated diagrams under `ops/diagrams/` with a short README and source timestamp.
- Prefer diagrams for routing/state contracts, not detailed UI layout.

### Sketch

- Use `sketch` for 2-3 disposable HTML variants before coding a screen.
- Store variants under `ops/sketches/<task-id>/`.
- Each variant must represent a different product stance, not just color changes.
- Promote only chosen decisions into `DESIGN.md` or implementation specs.

### Dogfood

- Use `dogfood` after a prototype is running.
- Store reports under `ops/dogfood/<task-id>/report.md` with screenshots.
- Required coverage: desktop, laptop, mobile, long answer, collapsed/open activity, empty/error states, keyboard path, console errors.

### Excalidraw

- Use for informal whiteboard flows, collaboration sketches, sequence diagrams, and design reviews.
- Store `.excalidraw` exports or PNG/SVG snapshots under `ops/diagrams/`.
- The local app lives at `/adapt/repos/gui/collab-tools/excalidraw`.

### Penpot Desktop

- Use for higher-fidelity static UI design reviews.
- Treat as a desktop client. Do not claim a self-hosted Penpot server is running unless one is explicitly deployed and secured.

### OpenPencil/Pencil

- Use for quick wireframes and throwaway layout comparisons.
- Promote decisions into markdown specs; do not rely on binary-only files as the source of truth.

### CryptPad

- Use only after systemd packaging and auth review.
- Candidate role: multi-person notes/spec drafting.
- Local source: `/adapt/repos/gui/collab-tools/cryptpad`.
- First-pass server requirements: systemd unit, local-only bind or TLS proxy, admin credentials documented outside git, backup path, redaction policy.

## Paperclip Sync

Paperclip should receive:

- accepted specs;
- fleet topology diagrams;
- task completion reports;
- redacted service/config inventories;
- QA reports and screenshot paths.

Paperclip must not receive:

- raw `.env` files;
- provider tokens;
- auth cookies;
- raw profile configs containing API keys;
- unredacted connection strings.

## Workflow

1. Start from a task folder.
2. Write or update the implementation spec.
3. If visual uncertainty remains, create 2-3 sketch variants.
4. Capture architecture/state diagrams for nontrivial routing.
5. Promote accepted decisions to `DESIGN.md` and task docs.
6. Build prototype.
7. Run dogfood QA.
8. Sync durable docs/reports to Paperclip.
9. Complete the task with a report and ops logs.

## Artifact Naming

- `ops/sketches/<task-id>/<variant-name>/index.html`
- `ops/diagrams/<task-id>-<topic>.html`
- `ops/diagrams/<task-id>-<topic>.excalidraw`
- `ops/dogfood/<task-id>/report.md`
- `ops/dogfood/<task-id>/screenshots/<name>.png`
- `DESIGN.md`

## Systemd And Auth Gates

Before any collaborative server is exposed:

- service must run under systemd;
- runtime artifacts must be gitignored;
- auth must be enabled and documented without secrets;
- bind address must be explicit;
- logs must be redacted or local-only;
- shutdown/restart commands must be documented;
- Paperclip sync must include only redacted docs.

## Tests And QA

- Verify links to artifacts are valid before completion.
- Verify no secret patterns are present in Paperclip-bound docs.
- Run `git status` to ensure runtime files are not accidentally staged.
- Dogfood reports must include screenshot evidence and console-error checks.

**— SIGNED_BY_AGENT**
