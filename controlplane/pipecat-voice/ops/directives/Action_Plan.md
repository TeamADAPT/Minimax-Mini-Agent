Action Plan

  This is the execution plan I’d run from the current state, with Skipper orchestrating, Latch integrating/fixing, Echo
  executing, and Testova validating.

  Goal
  Get the fleet into a state where:

  - Skipper can reliably orchestrate
  - Echo can execute real tasks continuously
  - Testova can validate without breaking flow
  - pipecat voice is usable and observable
  - Paperclip can reflect the real operating state

  Critical Path

  1. Stabilize Skipper/Testova session behavior
  2. Expose session/voice state in pipecat
  3. Put Skipper on a clean orchestration loop
  4. Start real decomposed execution through the crew

  Workstream 1: Crew runtime hardening

  1. Task 16: Skipper visible-session hardening

  - Owner: Latch
  - Support: Skipper
  - Steps:
      - inspect why Skipper CLI window is missing at snapshot time
      - verify terminal launch path, cwd, profile binding, and TUI persistence
      - separate “window not present” from “message persisted but not visible”
      - tighten bridge logging around window detection and post-send persistence
      - relaunch and run 5 direct NATS proofs
  - Acceptance:
      - 5/5 nova.skipper.direct prompts land in the intended session
      - no fallback required for those 5 turns
  - Rollback:
      - re-enable current fallback-only posture

  2. Task 17: Testova visible-session hardening

  - Owner: Latch
  - Support: Testova
  - Steps:
      - same pass as Skipper
      - confirm whether failure is terminal launch, xdotool targeting, or Hermes session state
  - Acceptance:
      - 3/3 visible proofs
  - Rollback:
      - keep Testova in fallback + validation role

  3. Task 18: Route-state fidelity upgrade

  - Owner: Latch
  - Steps:
      - improve crew_route_state.json
      - distinguish:
          - visible-ready
          - visible-missing
          - fallback-active
          - bridge-down
      - include latest proof timestamp and latest reply mode
  - Acceptance:
      - route state explains real posture without manual log reading

  Workstream 2: pipecat voice and session integration
  4. Task 19: Direct session-state API for pipecat

  - Owner: Latch
  - Steps:
      - extend gateway.py
      - expose latest agent session id, route mode, last proof, bridge owner, and recent snapshot summary
      - keep it read-only and lightweight
  - Acceptance:
      - one API response answers “who is live, how are they routed, what session are they on”

  5. Task 20: Voice/control-plane dashboard pass

  - Owner: Latch
  - Support: Echo
  - Steps:
      - add session/route widgets to existing dashboard
      - add cards for echo, skipper, testova, latch
      - add voice/gateway/NATS health strip
      - add route-mode indicators and last-proof timestamps
      - remove noisy panels that do not help operation
  - Acceptance:
      - waking up and loading dashboard gives actionable state in under 30 seconds

  6. Task 21: Monitor stream cleanup

  - Owner: Latch
  - Steps:
      - make monitor presets useful for real ops:
          - nova.*.direct
          - nova.*.ping
          - nova.logs.*
      - improve message rendering for proofs, failures, and route changes
  - Acceptance:
      - monitor is usable for live debugging without raw JSON hunting

  7. Task 22: Voice path validation

  - Owner: Echo
  - Support: Latch
  - Steps:
      - run turn tests through pipecat
      - verify direct route to active peer
      - verify STT -> NATS -> reply -> TTS path
      - capture failure classes cleanly
  - Acceptance:
      - 3 successful end-to-end voice turns
      - any failing path has a named root cause

  Workstream 3: Skipper orchestration loop
  8. Task 23: Skipper orchestration contract

  - Owner: Skipper
  - Support: Latch
  - Steps:
      - define exact delegation format:
          - objective
          - owner
          - acceptance
          - proof expected
          - checkback subject
      - define escalation rules
  - Acceptance:
      - every task issued by Skipper has a clean owner and proof contract

  9. Task 24: Skipper -> Echo execution lane

  - Owner: Skipper
  - Executor: Echo
  - Steps:
      - set a dedicated work cadence
      - short assignments, explicit completions, no ambiguous handoffs
  - Acceptance:
      - Echo completes 3 consecutive bounded tasks under Skipper direction

  10. Task 25: Skipper -> Testova validation lane

  - Owner: Skipper
  - Executor: Testova
  - Steps:
      - Testova receives validation-only work until session stability improves
      - define standard validation outputs
  - Acceptance:
      - validation results are usable without re-interpretation

  Workstream 4: Paperclip and task decomposition
  11. Task 26: Paperclip fleet sync refresh

  - Owner: Latch
  - Support: Skipper
  - Steps:
      - sync current docs/config posture into Paperclip-facing artifacts
      - only include live routes, active roles, and current constraints
  - Acceptance:
      - Paperclip reflects the actual fleet, not historical assumptions

  12. Task 27: Decompose buildout into task folders

  - Owner: Skipper
  - Support: Latch
  - Steps:
      - create one task directory per real unit of work
      - move active work to ops/in_progress
      - require completion_report.md for each completed slice
  - Acceptance:
      - no vague umbrella tasks; each task is ownable and closable

  13. Task 28: PEA/nova bootstrap execution queue

  - Owner: Skipper
  - Executors: Echo, Latch, Testova
  - Steps:
      - split bootstrap, NATS adapter, UI, Paperclip sync, and voice validation into independent slices
      - assign disjoint owners
  - Acceptance:
      - at least 5 executable tasks ready with owners and order

  Suggested first task set

  - 16-skipper-visible-session-hardening
  - 17-testova-visible-session-hardening
  - 18-route-state-fidelity-upgrade
  - 19-pipecat-session-state-api
  - 20-dashboard-session-voice-observability
  - 21-monitor-stream-cleanup
  - 22-voice-path-validation
  - 23-skipper-orchestration-contract
  - 24-skipper-echo-execution-lane
  - 25-skipper-testova-validation-lane
  - 26-paperclip-fleet-sync-refresh
  - 27-task-decomposition-enforcement
  - 28-pea-bootstrap-execution-queue

  Recommended order

  1. 16
  2. 17
  3. 18
  4. 19
  5. 20
  6. 21
  7. 23
  8. 24
  9. 25
  10. 22
  11. 26
  12. 27
  13. 28

  What I’d do first when execution resumes

  - harden Skipper session path
  - harden Testova session path
  - add session-state API + dashboard route widgets
  - let Skipper start issuing bounded tasks on the steadier surface
  

  Workstream 7: Crew Multi-Nova Orchestration

  1. Task 35: Crew online six-way

  - Owner: Zap (with Iris routing support)
  - Steps:
      - extend parameterized bridge to iris/zap/forge/synergy/tecton
      - launch 4 new TUI sessions (echo/skipper already live)
      - start nova-tui-bridge@X.service for each new nova
      - ping all 6 to verify unique pong
  - Acceptance:
      - all 6 nova.<name>.direct return pong; systemctl green for all bridges
  - References: ops/to_do/35-crew-online-sixway/TASK.md

  2. Task 37: Swift Brane wasm64 pilot (PARTIAL — scaffold done, Skipper 029f788)

  - Owner: Forge
  - Steps:
      - expand wasm64 file_read FFI (real path reading, not stub)
      - build host/shim.rs with wasmtime (see mnemos/l6-store-host pattern)
      - write scripts/swift_registry.json
      - wire nova.crew.swift.invoke NATS subscribe+dispatch
  - Acceptance:
      - cargo build --target wasm64-unknown-unknown passes; NATS invoke returns file content without python subprocess
  - References: ops/to_do/37-swift-brane-pilot/TASK.md, swift-brane/README.md

  3. Task 39: Crew consensus protocol (PARTIAL — skeleton done, Skipper 4c27312)

  - Owner: Synergy
  - Steps:
      - review scripts/crew_consensus_service.py
      - implement quorum vote counting, proposal state machine (PROPOSED → VOTING → BIND/NO_QUORUM/NO_BIND)
      - mock 3-voter BIND test (quorum=2, votes from iris/zap/forge → BIND result)
      - mock timeout NO_QUORUM test (quorum=3, only 2 votes)
      - record proof_id in ops/operations_history.md
  - Acceptance:
      - BIND published on nova.crew.consensus.bind.<topic> after sufficient yes votes
      - NO_QUORUM published on timeout without quorum
  - References: ops/to_do/39-crew-consensus-protocol/TASK.md, scripts/crew_consensus_service.py

  4. Crew Coordination Architecture (Tecton)

  - Owner: Tecton
  - Steps:
      - review ops/crew-coordination-architecture.md (Skipper draft)
      - resolve open questions: persistence model (ephemeral vs fjall/redb), wasm64 runtime (wasmtime vs FFI), crew health heartbeat, bridge delivery ACK/NACK
      - produce revised architecture doc + commit
  - Acceptance:
      - doc at ops/crew-coordination-architecture.md updated and committed
  - References: ops/crew-coordination-architecture.md

  New task set (updated):

  - /adapt/platform/novaops/controlplane/pipecat-voice/ops/to_do/16-skipper-visible-session-hardening/TASK.md
  - /adapt/platform/novaops/controlplane/pipecat-voice/ops/to_do/17-testova-visible-session-hardening/TASK.md
  - /adapt/platform/novaops/controlplane/pipecat-voice/ops/to_do/18-route-state-fidelity-upgrade/TASK.md
  - /adapt/platform/novaops/controlplane/pipecat-voice/ops/to_do/19-pipecat-session-state-api/TASK.md
  - /adapt/platform/novaops/controlplane/pipecat-voice/ops/to_do/20-dashboard-session-voice-observability/TASK.md
  - /adapt/platform/novaops/controlplane/pipecat-voice/ops/to_do/21-monitor-stream-cleanup/TASK.md
  - /adapt/platform/novaops/controlplane/pipecat-voice/ops/to_do/22-voice-path-validation/TASK.md
  - /adapt/platform/novaops/controlplane/pipecat-voice/ops/to_do/23-skipper-orchestration-contract/TASK.md
  - /adapt/platform/novaops/controlplane/pipecat-voice/ops/to_do/24-skipper-echo-execution-lane/TASK.md
  - /adapt/platform/novaops/controlplane/pipecat-voice/ops/to_do/25-skipper-testova-validation-lane/TASK.md
  - /adapt/platform/novaops/controlplane/pipecat-voice/ops/to_do/26-paperclip-fleet-sync-refresh/TASK.md
  - /adapt/platform/novaops/controlplane/pipecat-voice/ops/to_do/27-task-decomposition-enforcement/TASK.md
  - /adapt/platform/novaops/controlplane/pipecat-voice/ops/to_do/28-pea-bootstrap-execution-queue/TASK.md
  - /adapt/platform/novaops/controlplane/pipecat-voice/ops/to_do/35-crew-online-sixway/TASK.md
  - /adapt/platform/novaops/controlplane/pipecat-voice/ops/to_do/37-swift-brane-pilot/TASK.md
  - /adapt/platform/novaops/controlplane/pipecat-voice/ops/to_do/39-crew-consensus-protocol/TASK.md


