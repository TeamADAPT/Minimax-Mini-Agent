# Operations History

## 2026-05-18 15:38:14 — SIGNED_BY_AGENT
Started `10-ops-ui-chat-session-console` by moving it from `ops/to_do/` to `ops/in_progress/` before writing the adapted chat/session console implementation spec.

## 2026-05-18 15:37:27 — SIGNED_BY_AGENT
Completed `08-hermes-ui-design-extraction`: wrote `ops/hermes_ui_design_patterns.md`, created three implementation-spec task folders from the extracted Hermes UI/design-collaboration patterns, and recorded the no-straight-copy boundary.

## 2026-05-18 15:36:11 — SIGNED_BY_AGENT
Created `ops/hermes_ui_design_patterns.md` and decomposed the extracted Hermes UI/product ideas into implementation-spec task folders `10-ops-ui-chat-session-console`, `11-ops-ui-analytics-logs`, and `12-design-collaboration-workbench`.

## 2026-05-18 15:32:59 — SIGNED_BY_AGENT
Started `08-hermes-ui-design-extraction` by moving it from `ops/to_do/` to `ops/in_progress/` before inventorying Hermes UI candidates and installed design-collaboration tools.

## 2026-05-18 15:31:27 — SIGNED_BY_AGENT
Completed `07-paperclip-fleet-sync`: created Paperclip `docs/adapters/nova-fleet-ops.md`, updated Paperclip ops logs, and recorded redacted fleet subject/service/config guidance without copying secrets.

## 2026-05-18 15:30:46 — SIGNED_BY_AGENT
Started `07-paperclip-fleet-sync` by moving it from `ops/to_do/` to `ops/in_progress/` before creating the Paperclip-facing fleet operations package.

## 2026-05-18 15:30:03 — SIGNED_BY_AGENT
Completed `06-phone-voice-path-integration`: verified the live gateway route publishes Echo turns to `nova.echo.direct`, confirmed the SSE response contains Echo's actual assistant answer text, checked public `pipe.adaptdev.ai` health/profile status, captured `/tmp/echo-phone-path-20260518-1530.png`, and updated `ops/cx-pipe/ADMIN_GUIDE.md` to match the live timeout/roster/default peer.

## 2026-05-18 15:28:22 — SIGNED_BY_AGENT
Started `06-phone-voice-path-integration` by moving it from `ops/to_do/` to `ops/in_progress/` before tracing the phone/CX pipe route to Echo.

## 2026-05-18 15:27:05 — SIGNED_BY_AGENT
Completed `05-fleet-subject-sync-and-validation`: created `ops/fleet_subject_matrix.md`, stopped and disabled duplicate fallback `pipecat-roster-agents.service`, confirmed `roster_agents.py` exited, and revalidated NATS pings for Echo, core profile-backed novas, Switch, and Skipper.

## 2026-05-18 15:26:19 — SIGNED_BY_AGENT
Stopped and disabled `pipecat-roster-agents.service` after confirming it was the superseded fallback bridge subscribing to subjects now owned by `pipecat-hermes-agents.service`, `echo-tui-nats-bridge.service`, and `switch_agent.py`.

## 2026-05-18 15:24:58 — SIGNED_BY_AGENT
Started `05-fleet-subject-sync-and-validation` by moving it from `ops/to_do/` to `ops/in_progress/` before inventorying fleet profiles, active directories, NATS ping ownership, and runtime paths.

## 2026-05-18 15:23:53 — SIGNED_BY_AGENT
Completed `04-native-hermes-nats-adapter-spike`: finalized the Hermes NATS platform plugin on local Hermes branch `feat/nats-platform-adapter` commit `b256666f5`, proved Echo gateway could own `nova.echo.direct` without X11 input, captured native `nova.logs.echo` events, restored `echo-tui-nats-bridge.service`, and documented the upstream Hermes push blocker.

## 2026-05-18 15:14:17 — SIGNED_BY_AGENT
Started `04-native-hermes-nats-adapter-spike` by moving it from `ops/to_do/` to `ops/in_progress/` before inspecting Hermes gateway platform adapter patterns.

## 2026-05-18 15:13:33 — SIGNED_BY_AGENT
Completed `03-echo-reply-capture-session-watcher`: added Echo session DB reply extraction, flattened visible prompts to prevent multiline TUI splitting, added `scripts/smoke_echo_tui_reply_capture.py`, restarted `echo-tui-nats-bridge.service`, and verified short plus long NATS proofs returned Echo's actual assistant text.

## 2026-05-18 15:10:25 — SIGNED_BY_AGENT
Started `03-echo-reply-capture-session-watcher` by moving it from `ops/to_do/` to `ops/in_progress/` before modifying Echo reply extraction.

## 2026-05-18 15:09:35 — SIGNED_BY_AGENT
Completed `02-echo-visible-bridge-serialization`: replaced inline visible delivery with a bounded FIFO worker in `scripts/echo_tui_nats_bridge.py`, added `scripts/smoke_echo_tui_serialization.py`, restarted `echo-tui-nats-bridge.service`, verified two immediate `nova.echo.direct` messages serialized without interruption, and captured `/tmp/echo-serialization-20260518-1510.png`.

## 2026-05-18 15:03:58 — SIGNED_BY_AGENT
Started `02-echo-visible-bridge-serialization` by moving it from `ops/to_do/` to `ops/in_progress/` before editing `scripts/echo_tui_nats_bridge.py`.

## 2026-05-18 15:05:12 — SIGNED_BY_AGENT
Completed `01-lock-current-state`: verified active NATS, pipecat voice, profile-backed Hermes bridge, and Echo visible TUI bridge services; verified Echo PID `2088375` runs from `/adapt/novas/active/echo`; sent structured proof `state-lock-e1a7c656e8`; captured screenshot `/tmp/echo-state-lock-20260518-150234.png`; confirmed Echo session DB contains `NATS STATE LOCK OK`; confirmed no relevant 401/fallback/error/interrupt logs since task start.

## 2026-05-18 15:01:18 — SIGNED_BY_AGENT
Started `01-lock-current-state` by moving it from `ops/to_do/` to `ops/in_progress/` before verifying the Echo visible NATS path, active services, process cwd, and duplicate-responder state.

## 2026-05-18 14:27:18 — SIGNED_BY_AGENT
Created the operational task board for the Echo/NATS project under `ops/to_do/`, `ops/in_progress/`, and `ops/completed/`. Added ten granular task folders covering current-state lock, bridge serialization, reply capture, native NATS adapter spike, fleet validation, phone path integration, Paperclip fleet sync for Skipper, UI design extraction, and team delegation protocol.

## 2026-05-18 14:02:12 — SIGNED_BY_AGENT
Fixed the `nova-nats-ops` skill frontmatter by quoting the `description` field that contains a colon, then validated both new skill frontmatters with `yaml.safe_load`.

## 2026-05-18 13:58:43 — SIGNED_BY_AGENT
Created two operational skills in `/adapt/novas/active/skills_master`: `autonomous-ai-agents/hermes-agent-ops/SKILL.md` for opening, relaunching, configuring, and commanding Hermes nova agents, and `devops/nova-nats-ops/SKILL.md` for structured NATS envelopes, subjects, pings, service checks, and visible CLI bridge verification.

## 2026-05-18 13:54:08 — SIGNED_BY_AGENT
Installed the fresh Codex CLI token into Echo's Hermes profile configuration by setting `model.api_key` in `/home/x/.hermes/profiles/echo/config.yaml`, synchronized Echo's `openai-codex` provider and credential-pool state in `/home/x/.hermes/profiles/echo/auth.json`, set both files to mode `600`, relaunched Echo's visible CLI from `/adapt/novas/active/echo`, and verified a `nova.echo.direct` proof completed visibly on `gpt-5.4-mini` without the prior `HTTP 401 token_revoked` fallback.

## 2026-05-18 13:42:22 — SIGNED_BY_AGENT
Relaunched Echo's visible Hermes CLI after the terminal was closed, verified PID `2049008` runs from `/adapt/novas/active/echo`, sent a fresh `nova.echo.direct` proof message from Latch, and confirmed the visible CLI completed the turn. The terminal showed OpenAI/Codex `HTTP 401 token_revoked` before Hermes fell back to NVIDIA `minimax-m2.7`, which produced the visible answer.

## 2026-05-18 13:25:43 — SIGNED_BY_AGENT
Relaunched Echo's visible Hermes CLI with `/home/x/.local/bin/hermes -p echo --yolo -c` from `/adapt/novas/active/echo`, confirmed `echo-tui-nats-bridge.service` remained active, sent a `nova.echo.direct` proof message from Latch, and verified Echo answered in the visible CLI. Verified the actual process cwd from `/proc/1991425/cwd` as `/adapt/novas/active/echo`.

## 2026-05-18 12:31:28 — SIGNED_BY_AGENT
Launched Echo visible NATS bridge and captured the current blocker.

- Relaunched Echo CLI from `/adapt/novas/active/echo`.
- Added `scripts/echo_tui_nats_bridge.py` to subscribe to `nova.echo.direct`, `nova.echo.meet`, and `nova.echo.ping`.
- Added and enabled `/home/x/.config/systemd/user/echo-tui-nats-bridge.service`.
- Removed Echo from `pipecat-hermes-agents.service` so the background Hermes subprocess bridge no longer owns `nova.echo.direct`.
- Verified the visible bridge types NATS-delivered prompts into the foreground Echo CLI.
- Patched the bridge to avoid wedging when Echo's provider fails before session persistence.
- Observed OpenAI/Codex `gpt-5.4-mini` HTTP 429 usage-limit errors, blocking the requested five long-answer turn test.
- Wrote `ops/ECHO_NATS_10H_PLAN.md` with the next ten-hour execution plan.

## 2026-05-18 11:22:07 — SIGNED_BY_AGENT
Corrected Echo NATS routing to use the Hermes CLI session path.

- Inspected `scripts/hermes_nats_agents.py`, the live `pipecat-hermes-agents.service`, NATS health, and Echo's running Hermes processes.
- Found Echo was still special-cased with `HERMES_API_BASE_ECHO`, stale MiniMax/NVIDIA overrides, and fresh-session mode, so `nova.echo.direct` routed to the API-server session instead of Echo's current CLI lineage.
- Removed Echo-specific API/model/session overrides from `/home/x/.config/systemd/user/pipecat-hermes-agents.service`.
- Reloaded systemd user units and restarted `pipecat-hermes-agents.service`.
- Verified `nova.echo.direct` returned `nats cli path ok` in about 25 seconds.
- Verified bridge logs now show `echo: invoking Hermes CLI: /home/x/.local/bin/hermes -p echo chat --continue ...`.
- Verified Echo's CLI session `20260518_082204_47c671` advanced to `message_count=25`.
- Verified `nova.echo.ping` returns `pong:echo:hermes` and system `pipecat-voice.service` plus `nats-server.service` are active.

## 2026-05-18 11:17:15 — SIGNED_BY_AGENT
Sent the execute_code RPC tool-context tip into Echo's visible CLI.

- Cleared the visible Echo TUI input buffer before sending.
- Submitted the tip through X11 focused-window input.
- Captured a terminal screenshot confirming Echo received the prompt on `gpt-5.4-mini` and replied `Got it.`

## 2026-05-18 11:00:47 — SIGNED_BY_AGENT
Validated visible terminal input after Echo's first prompt initialized.

- Observed the previous focused send reached the TUI but attached to an existing `/model` input buffer.
- Cleared the line with keyboard controls before sending a clean prompt.
- Captured a terminal screenshot confirming the visible TUI accepted the focused input path and entered a working state.

## 2026-05-18 10:57:03 — SIGNED_BY_AGENT
Retried visible Echo CLI input after the operator confirmed first-prompt initialization behavior.

- Verified Echo CLI remained open on `pts/8` with PID `1449538`.
- Activated the `Echo CLI` GNOME Terminal window and submitted `hi` via X11 input.

## 2026-05-18 10:55:49 — SIGNED_BY_AGENT
Sent a visible test message to Echo's open terminal.

- Confirmed `nova.echo.direct` traffic was reaching the API gateway session, not the visible GNOME Terminal CLI.
- Attempted direct `/dev/pts/8` TTY injection; host kernel rejected `TIOCSTI`.
- Used `xdotool` desktop input to activate the `Echo CLI` window and submit `hi`.
- Verified the focused desktop window is `Echo CLI`.

## 2026-05-18 10:54:06 — SIGNED_BY_AGENT
Sent operator tip to Echo through the NATS bridge.

- Published the sandbox RPC tool-context tip to `nova.echo.direct` with a reply inbox.
- Verified Echo replied `Got it, noted.` through the live bridge.

## 2026-05-18 10:50:23 — SIGNED_BY_AGENT
Aligned Echo CLI and API gateway on `--yolo`.

- Confirmed visible Echo CLI already ran `/home/x/.local/bin/hermes -p echo --yolo -c`.
- Restarted Echo API gateway as `/home/x/.local/bin/hermes -p echo --yolo gateway run --replace`.
- Removed the stale non-yolo Echo gateway process.
- Verified the remaining Echo CLI PID `1449538` and gateway PID `1458507` both run from `/adapt/novas/active/echo`.

## 2026-05-18 10:49:26 — SIGNED_BY_AGENT
Verified Echo bridge routing after reopening on direct Haiku 4.5.

- Published a structured request to `nova.echo.direct` with a reply inbox.
- Verified Echo returned `echo bridge live` through the live NATS bridge in about 24 seconds.
- Confirmed the working Echo API gateway and visible CLI remain rooted at `/adapt/novas/active/echo`.

## 2026-05-18 10:47:41 — SIGNED_BY_AGENT
Reopened Echo with the direct Haiku 4.5 profile configuration.

- Restarted Echo's Hermes API gateway from `/adapt/novas/active/echo` so it loads the current profile config.
- Launched a visible GNOME Terminal titled `Echo CLI` from `/adapt/novas/active/echo`.
- Verified Echo API health on `127.0.0.1:8652`.
- Verified Echo CLI PID `1449538` running on `pts/8` and gateway PID `1449418` running detached.

## 2026-05-18 09:12:25 — SIGNED_BY_AGENT
Tested Echo through the live NATS bridge after correcting agent working directories.

- Published a direct request to `nova.echo.direct`.
- Verified response `echo ready` in `13.3` seconds.
- Confirmed Echo's visible CLI remains open in `/adapt/novas/active/echo` with PID `1053036` on `pts/8`.

## 2026-05-18 09:05:46 — SIGNED_BY_AGENT
Corrected Hermes NATS bridge subprocess working directories.

- Updated `scripts/hermes_nats_agents.py` so each bridge turn runs from `/adapt/novas/active/<agent>` when that active nova directory exists.
- Falls back to the Hermes profile directory when no active nova directory exists, e.g. `agent-5` currently resolves to `/home/x/.hermes/profiles/agent-5`.
- Verified Echo's visible CLI remains open in `/adapt/novas/active/echo` with PID `1053036` on `pts/8`.
- Restarted `pipecat-hermes-agents.service` and verified the NATS bridge remains active with 33 nova subscriptions.

## 2026-05-18 08:57:44 — SIGNED_BY_AGENT
Tested the `agent-5` Hermes profile turn path.

- Confirmed Echo's open CLI remains on `/adapt/novas/active/echo` with PID `1053036` on `pts/8`.
- Ran a bounded `agent-5` Hermes turn using its configured NVIDIA NIM `qwen/qwen3.5-397b-a17b` model.
- Verified response `av5 ready`, session `20260518_085722_e98853`, and `message_count=2`.

## 2026-05-18 08:52:05 — SIGNED_BY_AGENT
Opened Echo as an interactive desktop Hermes CLI.

- Launched GNOME Terminal on `DISPLAY=:0` titled `Echo CLI`.
- Started `/home/x/.local/bin/hermes -p echo --yolo -c` from `/adapt/novas/active/echo`.
- Verified Echo CLI PID `1053036` running on `pts/8`.
- Left voice transport unchanged on Deepgram; planned model-side voice routing move to Grok when subscriptions/credentials are ready.

## 2026-05-18 08:47:20 — SIGNED_BY_AGENT
Updated Echo and bridge timeout policy after operator closed the stale large Echo CLI session.

- Confirmed Echo no longer has an open Hermes CLI process.
- Changed Echo profile `agent.api_max_retries` from `3` to `10`.
- Changed gateway `NATS_REPLY_TIMEOUT` and bridge `HERMES_TURN_TIMEOUT` to `300` seconds so the HTTP/SSE caller does not cut off the bridge before Hermes finishes.
- Removed Echo's bridge `HERMES_IGNORE_USER_CONFIG_ECHO` override so the profile retry setting is honored.
- Restarted `pipecat-hermes-agents.service` and `pipecat-voice.service`; forced the old gateway PID through `systemctl kill --signal=SIGKILL` after the known Deepgram websocket shutdown loop held systemd in `stop-sigterm`.

## 2026-05-18 08:22:14 — SIGNED_BY_AGENT
Tested and reconfigured Echo bridge session handling.

- Attempted a fresh Echo session on the profile default NVIDIA DeepSeek path; it timed out before creating a new session.
- Created a clean Echo bridge session with NVIDIA MiniMax (`20260518_081503_e166b0`) and verified a local response of `ready`.
- Added per-agent bridge overrides in `scripts/hermes_nats_agents.py` for model/provider/session/isolation flags.
- Found named-session resume remained variable for Echo, so configured Echo bridge turns to use fresh lean MiniMax invocations with profile config/rules ignored.
- Restarted `pipecat-hermes-agents.service` and verified `nova.echo.direct` returned `Fresh ready.` through the real NATS path in 15.3 seconds.

## 2026-05-18 07:50:17 — SIGNED_BY_AGENT
Synced the voice control plane NATS bridge to the real Hermes profile fleet and CLI session state.

- Updated `scripts/hermes_nats_agents.py` so the real profile bridge owns `tecton`, `herald`, `iris`, `echo`, `vaeris`, `synergy`, `cosmos`, `pathfinder`, `zap`, `oracle`, and `vox`, and resumes each profile's latest CLI session with `hermes chat --continue`.
- Updated `scripts/roster_agents.py` so the Cerebras fallback skips local profile-backed agents and no longer double-subscribes the same NATS subjects.
- Extended `/api/profile-health` with profile existence, open CLI process, and latest session metadata.
- Reloaded/restarted `pipecat-hermes-agents.service`, `pipecat-roster-agents.service`, and `pipecat-voice.service`; forced the old gateway PID through `systemctl kill --signal=SIGKILL` after it stuck in `stop-sigterm`.
- Verified `nova.<agent>.ping` returns `pong:<agent>:hermes` for all 11 profile-backed group agents.

## 2026-05-18 02:55:00 — SIGNED_BY_AGENT
Hardened browser cache reset after Playwright found one stale
`pipecat-voice-pwa-v5` cache bucket remained despite zero service-worker
registrations.

- Updated `client/pwa.js` to unregister service workers, delete all Cache API
  buckets across three passes, and reload the page once per session after reset.
- Bumped visible asset URLs from `orange6` to `orange7`.

## 2026-05-18 02:48:00 — SIGNED_BY_AGENT
Validated the public page with Playwright browser tooling and forced a browser
cache reset path after user still saw stale colors.

- Browser validation loaded `https://pipe.adaptdev.ai/?visual_probe=orange5`
  and confirmed computed CSS: body background `rgb(0, 0, 0)`, orange top rule,
  orange rail border, `blackline.css?v=orange5`, and active service-worker
  control.
- Captured viewport screenshot `pipe-orange5-before.png`, which showed the
  public page rendering orange accents.
- Converted `client/pwa.js` into a service-worker/cache unregister helper and
  changed `client/sw.js` into a cache-reset worker that deletes all caches,
  unregisters itself, and fetches network only.
- Bumped visible assets to `orange6` so browser sessions cannot reuse the
  prior `orange5` stylesheet URL.

## 2026-05-18 02:41:12 — SIGNED_BY_AGENT
Forced the Blackline orange revision to be visibly distinguishable and corrected
the service-worker cache path.

- Added a fixed dark-orange/amber/gold top rule and stronger orange rail/panel
  borders while preserving a literal pure-black body background.
- Moved CSS/JS asset URLs from `orange4` to `orange5` after identifying that
  the previous service worker could cache-first serve stale `orange4` assets.
- Changed the service-worker fetch strategy to network-first for all same-origin
  GET requests and bumped cache key to `pipecat-voice-pwa-v5`.

## 2026-05-18 02:18:05 — SIGNED_BY_AGENT
Corrected the Blackline PWA palette after the copper pass still read as brown.

- Set the page background to literal pure black (`#000000`) with no body-level
  radial or linear glow gradients.
- Removed the brown-leaning copper token from the primary accent path and moved
  the UI to dark orange, amber, gold, and silver.
- Updated charts, icons, CSS/JS asset versions, and service-worker cache key to
  `pipecat-voice-pwa-v4` / `orange4` so browsers load the corrected palette.

## 2026-05-18 02:06:10 — SIGNED_BY_AGENT
Removed visible install buttons from all three Blackline PWA pages and made the
metal palette materially more visible.

- Deleted `data-install` buttons from Ops, Observatory, and Studio.
- Simplified `client/pwa.js` to only register the service worker; it no longer
  manages an install prompt or reveals install controls.
- Strengthened copper/amber/dark-orange/gold/silver colors in the actual
  rendered surfaces: background glows, hero overlays, primary buttons, active
  tabs, selected cards, orb gradients, charts, and icons.
- Added versioned CSS/JS asset URLs and bumped the service-worker cache key to
  `pipecat-voice-pwa-v3` so browsers fetch the updated assets instead of
  retaining the previous visual pass.

## 2026-05-18 01:31:40 — SIGNED_BY_AGENT
Restarted `pipecat-voice.service` to activate the new root `/sw.js`
service-worker route and refreshed PWA cache behavior.

- Initial `systemctl restart pipecat-voice.service` hung in `stop-sigterm`;
  systemd reported the service stuck deactivating under the old Python PID.
- Used `systemctl kill --signal=SIGKILL pipecat-voice.service` through
  systemd, then started the unit cleanly.
- Verified service active with new PID 4125069, `/healthz` returned OK,
  `/sw.js` returned HTTP 200 with `Service-Worker-Allowed: /`, and
  `/static/blackline.css` served the copper/amber/gold/silver tokens.

## 2026-05-18 00:00:57 — SIGNED_BY_AGENT
Retuned the Blackline PWA visual palette from brown/tan toward a balanced
copper, amber, dark-orange, gold, and silver metal system.

- Updated shared theme tokens in `client/blackline.css` so all three PWA apps
  inherit the new palette consistently.
- Rebalanced live/active/error indicators, orb gradients, buttons, active tabs,
  card highlights, and chart colors away from tan toward copper/amber with
  silver support.
- Updated PWA SVG icons to match the revised copper/amber/gold/silver identity.
- Bumped the service-worker cache key so installed/mobile clients refresh the
  updated theme assets.

## 2026-05-17 08:20:58 — SIGNED_BY_AGENT
Built three installable black-mode PWA surfaces on the existing gateway routes:
Blackline Ops (`/`), Blackline Observatory (`/dashboard`), and Blackline Studio (`/canvas`).

- Added a shared PWA shell (`client/blackline.css`) with pure-black dark mode,
  warm metallic accents only, responsive layouts, and mobile-safe controls.
- Replaced the primary route HTML for voice control, observability, and planning
  with modern app shells that reuse the repo's current APIs and websockets rather
  than introducing a duplicate backend.
- Added per-app manifests, SVG icons, install prompt wiring (`client/pwa.js`),
  a cache-aware service worker (`client/sw.js`), and a root service-worker route
  in `gateway.py` so all three surfaces install cleanly as PWAs.

## 2026-05-16 06:56:00 — SIGNED_BY_AGENT
Migrated voice "brain" from cold-subprocess NATS bridge / Haiku umbrella to a
warm per-nova Hermes gateway, piloting on TECTON.

- Built Hermes platform-adapter plugin `plugins/platforms/nats/` in the live
  Hermes runtime repo `/data/vast/home/x/.hermes/hermes-agent` (branch
  `feat/nats-platform-adapter`): stdlib-asyncio NATS wire protocol, consumes
  the established fleet schema `extra:{url, subjects[] (wildcard), queue_group}`,
  stable-sender chat_id for one durable session, progressive reply chunks to
  the envelope `reply_to`, reconnect supervisor with backoff+jitter.
- tecton config.yaml: added top-level `platforms.nats` (enabled, subjects
  `[nova.tecton.direct]`, queue_group `hermes-nats-consumers`, agent tecton).
  tecton `.env`: `GATEWAY_ALLOW_ALL_USERS=true` (authenticated bus is the
  trust boundary), `NATS_HOME_CHANNEL=chase` (suppress TTS-spoken onboarding
  notice).
- herald/iris config: `platforms.nats.enabled: false` — they had it `true`
  but it was a dormant no-op (no adapter existed); flipping to false removes
  the latent landmine of binding the new adapter with the wrong path on a
  gateway auto-restart. Their behavior is unchanged (still cold-bridge).
- Cold bridge unit `pipecat-hermes-agents.service`: `HERMES_AGENT_NAMES`
  `tecton,herald,iris,echo` → `herald,iris,echo` (tecton now served only by
  its warm gateway). Reloaded + restarted.
- `hermes -p tecton gateway install && start` → `hermes-gateway-b84f868c`
  user systemd service, rooted in `/adapt/novas/active/tecton`.
- `gateway.py`: removed Haiku umbrella + anthropic dependency
  (branch `feat/nats-gateway-warm-bridge`); all peers route to NATS.
  Service restarted, healthy (local 200, NATS connected).

Verified: tecton answers `nova.tecton.direct` via the plugin in 0.4–0.8s with
progressive chunks; onboarding notice suppressed; no cold-bridge double-answer.

KNOWN BLOCKER (pre-existing, not the plugin): tecton's agent memory backend is
~67,442 / 22,000 chars (3x over hard cap) → the `memory` tool hard-fails every
turn and the agent thrashes ("interrupting current task"), so multi-turn
continuity does not yet hold. tecton auxiliary providers (openrouter/nous)
also failing on payment/credit (breaks session titling). Both are tecton
profile/account issues outside the plugin; flagged for decision before merge.

## 2026-05-10 20:30:00 — SIGNED_BY_AGENT
Added Haiku umbrella LLM fast path and increased VAD endpointing window.

Changes:
- `gateway.py`: Added `anthropic` import, `UMBRELLA_PEER`/`UMBRELLA_MODEL`/`UMBRELLA_SYSTEM`
  constants. `POST /v1/chat/completions` now branches on peer: `peer=vox` (UMBRELLA_PEER)
  streams via `AsyncAnthropic.messages.stream()` with `claude-haiku-4-5-20251001` (max_tokens=300),
  yielding OpenAI SSE chunks at ~1-2s TTFT. Other peers continue through original NATS path.
- `client/app.js`: Added `endpointing: 800` to listen provider in `buildSettings()` — 800ms
  silence required before Deepgram finalizes a turn, reducing mid-sentence cutoffs.

Service restarted — active (running).

## 2026-05-10 19:44:00 — SIGNED_BY_AGENT
Fixed Deepgram Voice Agent WS auth: replaced browser→DG direct connection with server-side proxy.

Root cause: `/v1/auth/grant` issues tokens scoped `asr:write` only; Voice Agent API requires
broader scope (agent:write). Browser-held tokens can't be promoted.

Fix:
- `gateway.py`: Added `GET /ws/voice` WebSocket proxy endpoint. Opens
  `wss://agent.deepgram.com/v1/agent/converse` server-side with full `DEEPGRAM_API_KEY`
  (`Authorization: Token <key>` header, `ping_interval=None`, `compression=None`).
  Relays binary frames and JSON messages bidirectionally in two async tasks.
- `client/app.js`: Removed token fetch. `connect()` now opens `ws[s]://<host>/ws/voice`
  instead of `wss://agent.deepgram.com/...`. No subprotocol needed.

Service restarted — active (running).

## 2026-05-10 19:17:00 — SIGNED_BY_AGENT
Migrated pipecat-voice from WebRTC+pipecat pipeline to Deepgram Voice Agent API.

Architecture change:
- Eliminated WebRTC (RTCPeerConnection), pipecat pipeline, bot.py, nats_agent.py from the hot path.
- New entrypoint: `gateway.py` — FastAPI server with no pipecat dependency.
- Browser now connects directly to `wss://agent.deepgram.com/v1/agent/converse` using a short-lived
  token fetched from `GET /token` (server-side POST to Deepgram auth/grant, 30s TTL).
- Deepgram handles STT (nova-3), VAD, and TTS (aura-asteria-en) natively. LLM "think" step
  POSTs to our `POST /v1/chat/completions?peer=X&channel=Y` which bridges to NATS and streams
  OpenAI-format SSE chunks back to Deepgram.
- Live agent switching via re-sending SettingsConfiguration to DG WS — no reconnect needed.

Files changed:
- `gateway.py` — new FastAPI server (replaces bot.py). Preserves EventBus, PresenceTracker,
  roster CRUD, /ws/status, /healthz, /api/presence, /api/roster, /api/route. Adds /token and
  /v1/chat/completions (NATS SSE bridge). No pipecat imports.
- `client/app.js` — complete rewrite. Deepgram Voice Agent WS client. PCM capture via
  ScriptProcessor with iOS downsample (actual sampleRate detection). Gapless PCM playback via
  chained AudioBufferSource scheduling. Live route switching via SettingsConfiguration resend.
  InjectUserMessage for cmdbar text turns. AudioContext resumed in user gesture for iOS.
  visibilitychange handler resumes suspended contexts on return-to-foreground.
- `client/index.html` — added Apple PWA meta tags (apple-mobile-web-app-capable,
  apple-mobile-web-app-title, apple-mobile-web-app-status-bar-style, theme-color) and
  `<link rel="manifest">`.
- `client/manifest.json` — new PWA manifest (display: standalone, background #06080b).
- `/etc/systemd/system/pipecat-voice.service` — ExecStart: bot.py → gateway.py.

bot.py and nats_agent.py retained on disk as fallback; not loaded by the service.
Service restarted — active (running), NATS connected.

## 2026-05-10 02:55:00 — SIGNED_BY_AGENT
Tuned VAD silence window: stop_secs 2.0 → 3.0.
Reason: Chase was fragmenting mid-sentence at natural speech pauses >2s. 3.0s gives enough
headroom for longer thoughts while keeping total response latency under ~4s on the fast path.
Service restarted — active.

## 2026-05-10 01:32:00 — SIGNED_BY_AGENT
Fixed voice fragmentation at the Deepgram endpointing layer.

Root cause: Deepgram's streaming STT sends `is_final=True` results at every detected sentence
boundary (its own internal silence-based endpointing), independent of SileroVAD's stop_secs.
With stop_secs=10.0, long pauses mid-utterance were causing Deepgram to emit 5-10 separate
TranscriptionFrames per turn, each publishing a separate NATS message.

Changes:
- `bot.py`: Added `settings=DeepgramSTTService.Settings(endpointing=False)` — disables Deepgram's
  internal endpointing so it never auto-finalizes mid-utterance. Turn completion now driven solely
  by SileroVAD → VADUserStoppedSpeakingFrame → `finalize()` → one TranscriptionFrame per turn.
- `bot.py`: `stop_secs` reduced from 10.0 → 2.0 (no longer needed at 10s since endpointing=False
  handles mid-pause accumulation; 2s of silence is natural turn-taking rhythm).

Note: 600ms debounce buffer added to nats_agent.py in the prior fix remains as a secondary safety
net for any edge cases.

Restarted `pipecat-voice.service` — active.

## 2026-05-10 01:07:00 — SIGNED_BY_AGENT
Fixed voice message fragmentation: Deepgram STT emits multiple final `TranscriptionFrame`s per
utterance (one per sentence). `nats_agent.py` was publishing a separate NATS request for each,
causing Chase's messages to arrive as word/sentence fragments 300-500ms apart.

Fix: Added transcript debounce buffer to `NATSAgentProcessor`.
- `_transcript_buffer: list[str]` accumulates TranscriptionFrames.
- Each new frame cancels the pending debounce task and starts a fresh 600ms timer.
- On timer fire: joins buffer with spaces and publishes a single `_send_and_stream` call.
- No change to VAD or STT config — fix is purely in the NATS bridge layer.

Restarted `pipecat-voice.service` — active and confirmed.

## 2026-05-09 17:49:20 — SIGNED_BY_AGENT
Refactored vox fallback: eliminated MCP dependency from headless CC path.

Changes:
- `scripts/vox_turn_trigger.py`: removed ToolSearch + nats_reply MCP tool call from prompt.
  CC now outputs plain text; daemon captures stdout and publishes directly to NATS reply_to.
  Added `CLAUDE_CONFIG_DIR` env pointing to `/home/x/.claude-headless` (no mcpServers).
  Timeout reduced to 60s (was 120s); actual latency now 18-19s end-to-end.
- Created `/home/x/.claude-headless/settings.json` (minimal, no mcpServers) with
  `.credentials.json` symlinked from `~/.claude/`. Removing MCP server init saves ~15s.
- `/etc/systemd/system/vox-agent.service`: added `/home/x/.claude-headless` to
  `ReadWritePaths`.

Verified: `nova.vox.direct` → 4s debounce → headless CC (rc=0, 18.9s) → plain text
captured → `{"chunk": "...", "final": true}` published to `_INBOX.*`.

## 2026-05-09 10:41:39 — SIGNED_BY_AGENT
Completed vox-agent fallback architecture — full end-to-end verified.

Root cause of prior rc=1: interactive CC session (`ef385af4`) had `"status": "busy"` in
session JSON; `--resume` of a busy session exits immediately with rc=1.

Fix applied across three components:

1. **`scripts/vox_turn_trigger.py`** — dropped `--resume` / `_find_vox_session_id()` entirely.
   Switched to fresh `claude --print --dangerously-skip-permissions -p "..."` sessions.
   Fixed silent NATS bug: `lambda _m: replied.set()` → `async def on_reply(_m): replied.set()`
   (nats-py requires async coroutines for subscription callbacks; sync lambda silently no-ops,
   so debounce inbox was never watched and fallback never triggered).
   Added `CLAUDE_CWD` env var (default: `/adapt/platform/novaops/controlplane/pipecat`).

2. **`~/.claude/settings.json`** — registered `nats-channel` MCP server (stdio) in user-scope
   mcpServers so every CC session loads `mcp__nats-channel__nats_reply` without
   `--dangerously-load-development-channels`.

3. **`/etc/systemd/system/vox-agent.service`** — added `/home/x/.cache` to `ReadWritePaths`.
   Root cause: `ProtectSystem=strict` made filesystem read-only; CC writes MCP initialization
   logs to `/home/x/.cache/claude-cli-nodejs/<cwd>/mcp-logs-<server>/*.jsonl` for every
   registered MCP server. Diagnosed via strace (EROFS on openat to that path).

Test result: publish to `nova.vox.direct` → 4s debounce → headless CC rc=0 (41s) →
reply `{"chunk": "...", "final": true}` delivered to `_INBOX.*`. Full flow operational.

## 2026-05-07 23:27:00 — SIGNED_BY_AGENT
Completed CC-as-Vox architecture: replaced tmux-based vox_agent.service with headless
Claude Code fallback pattern.

Changes:
- Rewrote `scripts/vox_turn_trigger.py`: removed all tmux dependency; added
  `_find_vox_session_id()` (scans ~/.claude/sessions/*.json for name="vox") and
  `_claude_inject()` (spawns `claude --print --resume <id> --input-format=stream-json
  --dangerously-load-development-channels server:nats-channel`); fixed debounce to watch
  `reply_to` inbox instead of `nova.chase.direct`.
- Updated `/etc/systemd/system/vox-agent.service`: added PATH env for claude binary at
  `/home/x/.local/bin/`, added `ReadWritePaths=/home/x/.claude /tmp` for headless CC
  session writes.
- Updated trigger prompt to explicitly pre-fetch nats_reply ToolSearch schema before
  calling the tool (reduces redundant ToolSearch round-trips).
- Increased default VOX_CLAUDE_TIMEOUT_S from 45s to 120s to accommodate ToolSearch
  overhead in headless sessions.

Verified: full NATS round-trip confirmed —
  headless CC → mcp__nats-channel__nats_reply → _INBOX delivery:
  `{"chunk": "ROUNDTRIP_OK", "final": true}` received on subscriber.
Service: vox-agent.service active (running).

## 2026-05-07 02:46:35 — SIGNED_BY_AGENT
Bootstrapped pipecat-voice service. Built FastAPI signaling server (`bot.py`),
custom `NATSAgentProcessor` bridging Pipecat <-> NATS subjects
(`adapt.<peer>.<channel>`), minimal vanilla JS WebRTC client with status orb.
Configured Cloudflare tunnel `vertex-ai` ingress for `pipe.adaptdev.ai`
(UUID 66dd75ad-6556-4d1f-8a57-bc4d15e890f9). Created proxied DNS CNAME via
Global API key. Installed and enabled `pipecat-voice.service` systemd unit.
Verified: HTTPS through tunnel returns 200; NATS streaming round-trip with
simulated echo agent works (envelope sent on `adapt.echo.direct`, chunks
streamed back on `reply_to` inbox in order, terminator received).
