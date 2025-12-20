TeamADAPT Rules

---

## Environment Rules

- Docker is **not** used.  
- Python virtual environments (**venv**) are **not** used.  
- All Python execution is **system-wide**.  
- All services must be deployed and managed using **systemd**, not containers.

---

## Repository Structure Note

This repository operates as a global, generic structure.  
Where you see `[DIRECTORY_NAME]`, treat it as the **actual working directory name on disk**.

---

## Git Ignore Policy

All logical, ephemeral, temporary, runtime, or generated artifacts must be added to `.gitignore`.  
Only permanent documentation, ops files, and tracked tasks belong in version control.

---

## Ops Discipline

Every operational action must be logged in:

- `/ops/operations_history.md`  
- `/ops/decisions.log`

All entries must be:

- Timestamped (`YYYY-MM-DD HH:MM:SS`)  
- Reverse-chronological (newest first)  
- Signed by the agent performing the action using the format:  
  **— SIGNED_BY_AGENT**

---

## Task Workflow Protocol

1. **Selecting a Task**  
   Choose a task directory from `/ops/to_do/`.

2. **Begin Work**  
   Move the task directory into `/ops/in_progress/`.

3. **Execution**  
   Perform the work directly at the system level.  
   Log all decisions and actions in:
   - `ops/operations_history.md`
   - `ops/decisions.log`  
   Entries must be timestamped and signed by the agent completing the action.

4. **Completion**  
   Write a `completion_report.md` inside the task directory.  
   Move the directory into `/ops/completed/`.

5. **Version Control Workflow**  
   After each step:
   - `git add .`
   - `git commit -m "<description> — SIGNED_BY_AGENT"`
   - `git push`

---

## GitHub CLI Workflow Template

```
gh repo create x1_[DIRECTORY_NAME] --private --source=. --remote=origin --push
git checkout -b working
git add .
git commit -m "Initial commit — SIGNED_BY_AGENT"
git push --set-upstream origin working
```

---

## Documentation Best Practices

### 1. The README Is the Source of Truth

Every repository must include a clear, structured `README.md` describing:

- Purpose of the repo  
- System requirements  
- Directory structure  
- Execution instructions  
- Operational conventions (systemd, system Python, no Docker, no venv)  
- Maintenance rules  
- Task flow model:  
  `to_do → in_progress → completed`

The README must always reflect the **real, current operational state**.

---

### 2. Documentation Must Be Reverse-Chronological

All log entries are stacked with the **newest first** for operational clarity.

---

### 3. Every Decision Must Be Logged

Any modification, reasoning path, change, divergence, or rejection is recorded in:

- `operations_history.md`
- `decisions.log`

Every entry must include:

- Timestamp  
- Decision summary  
- **Agent signature**: `— SIGNED_BY_AGENT`

---

### 4. No Redundancy, No Noise

Documentation must be:

- Direct  
- Operable  
- Minimal but complete  
- Accurate to system behavior  

---

### 5. Consistent Formatting Across All Ops Writing

- H1 for file titles  
- H2 for dated entries  
- ISO timestamp: `YYYY-MM-DD HH:MM:SS`  
- Signature line:  
  **— SIGNED_BY_AGENT**

---

### 6. Git Hygiene

- Always work from a dedicated branch (`working`)  
- Keep `main` clean and protected  
- Commit after each meaningful step  
- `.gitignore` must exclude runtime artifacts and ephemeral files

---

### 7. Systemd + System Python Assumptions

All documentation assumes:

- System-level execution  
- Systemd service management  
- No Docker  
- No venv  

---

## Initialization Log Templates

### `ops/operations_history.md`

```
# Operations History

## YYYY-MM-DD HH:MM:SS — SIGNED_BY_AGENT
Initialized ops directory structure and documentation framework.
```

---

### `ops/decisions.log`

```
# Decisions Log

## YYYY-MM-DD HH:MM:SS — SIGNED_BY_AGENT
Decision recorded: Establish baseline operational rules (systemd-only, system Python, no Docker, no venv).
```

---

CHIEF SYSTEMS ARCHITECT

