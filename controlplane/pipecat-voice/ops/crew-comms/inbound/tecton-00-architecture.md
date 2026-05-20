# Tecton Task: Architecture Decomposition

## Objective
Architect the SignalCore/NovaOps control plane based on Action_Plan.md.

## Context
- Primary: /adapt/platform/novaops/controlplane/pipecat-voice
- Goal: reduce Codex token drain by dumping thread context, not stopping crew loops
- Do not stop existing loops/services unless concrete fault

## Steps
1. Read ops/directives/Action_Plan.md (full)
2. Read ops/operations_history.md
3. Identify top 3 architectural priorities from Action Plan
4. Propose decomposed task structure (what to build, what's blocked, what's parallel)
5. Output to ops/ARCHITECTURE_DECOMPOSITION.md

## Acceptance
- ops/ARCHITECTURE_DECOMPOSITION.md: priorities, dependencies, task decomposition
