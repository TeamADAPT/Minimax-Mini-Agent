# Operations History

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
