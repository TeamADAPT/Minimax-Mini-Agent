# Design Collaboration Workbench

## Status

completed

## Objective

Write an implementable platform spec for using Penpot desktop, Excalidraw, CryptPad, OpenPencil, and design skills as a repeatable NovaOps design-collaboration loop.

## Inputs

- `ops/hermes_ui_design_patterns.md`
- Installed skills: `design-md`, `architecture-diagram`, `popular-web-designs`, `dogfood`, `sketch`
- `/adapt/repos/gui/collab-tools`
- Paperclip fleet sync docs

## Steps

1. Move this folder to `ops/in_progress/`.
2. Define what artifact belongs in each tool.
3. Define systemd/auth review gates for any collaborative server.
4. Define Paperclip sync outputs and redaction boundaries.
5. Define acceptance tests and dogfood cadence.
6. Write `ops/design_collaboration_workbench_spec.md`.
7. Write `completion_report.md`.
8. Move this folder to `ops/completed/`.
9. Commit and push.

## Acceptance

- Spec exists and maps tools to concrete outputs.
- Spec includes Paperclip sync guidance.
- Spec includes auth/systemd gates for server tools.
- Spec includes QA cadence and artifact naming.
