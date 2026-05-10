# Operations History

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
