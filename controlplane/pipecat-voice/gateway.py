"""Voice gateway: Deepgram Voice Agent API + NATS bridge.

Replaces bot.py. WebRTC and the pipecat pipeline are gone.
Deepgram handles STT, VAD, and TTS directly via its Agent WebSocket API.

Architecture:
  Browser ←→ wss://agent.deepgram.com/v1/agent/converse
  Deepgram agent → POST /v1/chat/completions  (our NATS bridge, OpenAI-SSE)
  /v1/chat/completions → NATS → nova agent → SSE reply chunks → Deepgram TTS

HTTP/WS surface:
  GET  /                          front-end (cache-busted)
  GET  /healthz
  GET  /token                     short-lived DG bearer token for browser WS
  POST /v1/chat/completions        OpenAI-compatible SSE — routes to NATS
  GET  /api/roster                 agent roster CRUD
  POST /api/roster/agents
  DELETE /api/roster/agents/{name}
  GET  /api/presence
  POST /api/route                  broadcast route-change (client reconfigures DG)
  WS   /ws/status                  presence + roster event bus
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import subprocess
import time
import urllib.request
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import nats
import uvicorn
import websockets as _ws_lib
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, Response, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger
from nats.aio.client import Client as NATSClient
from nats.aio.subscription import Subscription

from canvas import handle_canvas_ws, canvas_state
from kanban import kanban_board

ROOT = Path(__file__).parent
ROSTER_PATH = ROOT / "roster.json"
ROOM_HISTORY_PATH = ROOT / "ops" / "cx-pipe" / "room_history.jsonl"

for _env in (Path("/adapt/secrets/db.env"), Path("/adapt/secrets/m2.env"), ROOT / ".env"):
    if _env.exists():
        load_dotenv(_env, override=True)

SELF_AGENT = os.environ.get("SELF_AGENT", "chase")
SUBJECT_NS = os.environ.get("SUBJECT_NS", "nova")
NATS_REPLY_TIMEOUT = float(os.environ.get("NATS_REPLY_TIMEOUT", "30"))
GROUP_PEERS = {"all", "everyone", "nats", "mats"}
GROUP_CHANNEL = os.environ.get("GROUP_CHANNEL", "meet")
GROUP_EXCLUDE_PEERS = {
    n.strip().lower()
    for n in os.environ.get("GROUP_EXCLUDE_PEERS", "switch,vox").split(",")
    if n.strip()
}
GROUP_AGENT_NAMES = [
    n.strip().lower()
    for n in os.environ.get("GROUP_AGENT_NAMES", "").split(",")
    if n.strip()
]
DEFAULT_MODERATOR = os.environ.get("DEFAULT_MODERATOR", "echo").strip().lower()
PROFILE_BLOCKERS = {
    # All previously blocked profiles have been fixed (2026-05-11):
    # - vaeris/synergy/cosmos: provider auth resolved (NVIDIA_API_KEY in .env)
    # - pathfinder: oversized payload resolved (correct context_length 131072)
    # - vox: real Hermes profile now exists
    # Add entries here only if a profile needs manual remediation.
}

# ------------------------------------------------------------------ NATS client
# ------------------------------------------------------------------ NATS streaming helper


class NATSStreamer:
    """Shared helper for NATS request/response streaming patterns.

    Encapsulates the common pattern of:
    1. Creating a reply_to inbox
    2. Subscribing to receive chunked responses
    3. Publishing a request message
    4. Streaming chunks until final or timeout
    5. Cleaning up subscription
    """

    def __init__(self, nc: NATSClient, timeout: float = NATS_REPLY_TIMEOUT):
        self.nc = nc
        self.timeout = timeout
        self._sub: Subscription | None = None
        self._queue: asyncio.Queue[str | None] | None = None

    async def request_stream(
        self,
        subject: str,
        message: str,
        from_agent: str = SELF_AGENT,
        to_agent: str | None = None,
        extra_fields: dict | None = None,
    ) -> str:
        """Send a request and stream the response chunks.

        Args:
            subject: NATS subject to publish to
            message: Message text to send
            from_agent: Sender agent name
            to_agent: Target agent name (optional)
            extra_fields: Additional envelope fields (optional)

        Returns:
            Concatenated response text
        """
        reply_to = self.nc.new_inbox()
        self._queue = asyncio.Queue()

        async def _on_chunk(msg: Any) -> None:
            try:
                payload = json.loads(msg.data.decode())
            except Exception:
                return
            chunk = payload.get("chunk", "")
            final = bool(payload.get("final", False))
            if chunk:
                self._queue.put_nowait(chunk)  # type: ignore
            if final:
                self._queue.put_nowait(None)

        self._sub = await self.nc.subscribe(reply_to, cb=_on_chunk)

        envelope: dict[str, Any] = {
            "from": from_agent,
            "type": "voice",
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "reply_to": reply_to,
        }
        if to_agent:
            envelope["to"] = to_agent
        if extra_fields:
            envelope.update(extra_fields)

        logger.info(f"NATS publish -> {subject} | {message[:80]!r}")
        await self.nc.publish(subject, json.dumps(envelope).encode())
        await self.nc.flush()

        chunks: list[str] = []
        try:
            while True:
                try:
                    chunk = await asyncio.wait_for(self._queue.get(), timeout=self.timeout)
                except asyncio.TimeoutError:
                    logger.warning(f"NATS reply timeout on {subject}")
                    break
                if chunk is None:
                    break
                chunks.append(chunk)
        finally:
            if self._sub:
                try:
                    await self._sub.unsubscribe()
                except Exception:
                    pass

        return "".join(chunks).strip()


_nc: NATSClient | None = None
_nc_lock = asyncio.Lock()


async def _get_nats() -> NATSClient:
    global _nc
    async with _nc_lock:
        if _nc and _nc.is_connected:
            return _nc
        url = os.environ.get("NATS_URL", "")
        if not url:
            raise RuntimeError("NATS_URL not set")
        logger.info(f"NATS connecting -> {url.split('@')[-1]}")
        _nc = await nats.connect(
            url,
            name="pipecat-gateway",
            reconnect_time_wait=1,
            max_reconnect_attempts=-1,
        )
        logger.info("NATS connected")
        return _nc


async def _close_nats() -> None:
    global _nc
    if _nc is not None:
        try:
            await _nc.drain()
        except Exception:
            pass
        _nc = None


# --------------------------------------------------------------- EventBus


class EventBus:
    """In-process pub/sub of JSON events to /ws/status subscribers."""

    def __init__(self) -> None:
        self._subs: set[WebSocket] = set()
        self._lock = asyncio.Lock()
        self._last_status: str = "idle"

    async def add(self, ws: WebSocket) -> None:
        async with self._lock:
            self._subs.add(ws)
        try:
            await ws.send_text(json.dumps({"type": "status", "event": self._last_status}))
        except Exception:
            pass

    async def remove(self, ws: WebSocket) -> None:
        async with self._lock:
            self._subs.discard(ws)

    async def publish(self, payload: dict | str) -> None:
        if isinstance(payload, str):
            self._last_status = payload
            payload = {"type": "status", "event": payload}
        elif payload.get("type") == "status":
            self._last_status = payload.get("event", self._last_status)
        async with self._lock:
            dead: list[WebSocket] = []
            data = json.dumps(payload)
            for ws in self._subs:
                try:
                    await ws.send_text(data)
                except Exception:
                    dead.append(ws)
            for ws in dead:
                self._subs.discard(ws)


bus = EventBus()

# --------------------------------------------------------------- PresenceTracker


class PresenceTracker:
    """Polls NATS monitoring /subsz and broadcasts per-agent online state."""

    def __init__(
        self,
        *,
        interval: float = 5.0,
        monitor_url: str = "http://127.0.0.1:8223/subsz?subs=1",
        subject_ns: str = "nova",
    ) -> None:
        self._interval = interval
        self._monitor_url = monitor_url
        self._ns = subject_ns
        self._task: asyncio.Task | None = None
        self._state: dict[str, dict] = {}

    @property
    def state(self) -> dict[str, dict]:
        return dict(self._state)

    async def start(self) -> None:
        if self._task is not None:
            return
        self._task = asyncio.create_task(self._loop())
        logger.info(f"presence tracker started ({self._monitor_url})")

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    async def _fetch_subjects(self) -> set[str]:
        loop = asyncio.get_running_loop()

        def _read() -> set[str]:
            with urllib.request.urlopen(self._monitor_url, timeout=2) as resp:
                data = json.loads(resp.read())
            return {s.get("subject", "") for s in data.get("subscriptions_list", [])}

        return await loop.run_in_executor(None, _read)

    async def _loop(self) -> None:
        while True:
            try:
                subjects = await self._fetch_subjects()
                roster = load_roster()
                names = [a["name"] for a in roster.get("agents", [])]
                now = time.time()
                changes: dict[str, bool] = {}
                for n in names:
                    online = f"{self._ns}.{n}.direct" in subjects
                    if self._state.get(n, {}).get("online") != online:
                        changes[n] = online
                    self._state[n] = {
                        "online": online,
                        "last_seen": now if online else self._state.get(n, {}).get("last_seen", 0),
                    }
                payload: dict[str, Any] = {"type": "presence", "snapshot": self._state}
                if changes:
                    payload["changes"] = changes
                await bus.publish(payload)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.warning(f"presence loop error: {exc}")
            await asyncio.sleep(self._interval)


presence = PresenceTracker(subject_ns=SUBJECT_NS)

# --------------------------------------------------------------- roster IO

_NAME_RE = re.compile(r"^[a-z][a-z0-9_-]{1,30}$")


def load_roster() -> dict:
    if not ROSTER_PATH.exists():
        default: dict = {"self": "chase", "default_peer": "switch", "agents": []}
        ROSTER_PATH.write_text(json.dumps(default, indent=2))
        return default
    try:
        return json.loads(ROSTER_PATH.read_text())
    except Exception as exc:
        logger.error(f"roster.json unreadable: {exc}")
        return {"self": "chase", "default_peer": "switch", "agents": []}


def save_roster(data: dict) -> None:
    tmp = ROSTER_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=2))
    tmp.replace(ROSTER_PATH)


def _valid_agent_names(names: list[str] | str) -> list[str]:
    if isinstance(names, str):
        names = re.split(r"[, ]+", names)
    seen: set[str] = set()
    result: list[str] = []
    for name in names:
        clean = name.strip().lower()
        if clean and _NAME_RE.match(clean) and clean not in seen:
            seen.add(clean)
            result.append(clean)
    return result


def _parse_agent_csv(value: str) -> list[str]:
    if not value:
        return []
    return _valid_agent_names(re.split(r"[, ]+", value))


def _configured_group_targets(roster: dict) -> list[str]:
    if GROUP_AGENT_NAMES:
        return _valid_agent_names(GROUP_AGENT_NAMES)
    return _valid_agent_names(
        [
            a["name"]
            for a in roster.get("agents", [])
            if a.get("name")
            and a["name"].strip().lower() not in {SELF_AGENT, *GROUP_EXCLUDE_PEERS}
            and a.get("tier") != "router"
        ]
    )


def _profile_health() -> dict:
    roster = load_roster()
    configured = set(_configured_group_targets(roster))
    online = presence.state
    agents: list[dict[str, Any]] = []
    for agent in roster.get("agents", []):
        name = (agent.get("name") or "").strip().lower()
        if not name:
            continue
        is_online = bool(online.get(name, {}).get("online"))
        if name in PROFILE_BLOCKERS:
            status = "blocked"
            reason = PROFILE_BLOCKERS[name]
        elif name in configured and is_online:
            status = "live"
            reason = "Subscribed on NATS and included in group room routing."
        elif name in configured:
            status = "offline"
            reason = "Configured for group routing but no NATS subscription is visible."
        elif agent.get("tier") == "router":
            status = "router"
            reason = "Router/control profile; not included in group agent fanout."
        else:
            status = "available"
            reason = "In roster but not enabled in GROUP_AGENT_NAMES."
        agents.append(
            {
                "name": name,
                "label": agent.get("label") or name.capitalize(),
                "tier": agent.get("tier") or "core",
                "online": is_online,
                "group_enabled": name in configured,
                "status": status,
                "reason": reason,
                "last_seen": online.get(name, {}).get("last_seen", 0),
            }
        )
    return {
        "group_agents": sorted(configured),
        "default_moderator": DEFAULT_MODERATOR,
        "agents": agents,
    }


def _run_readonly(args: list[str], timeout: float = 5.0) -> dict[str, Any]:
    try:
        proc = subprocess.run(args, capture_output=True, text=True, timeout=timeout, check=False)
        out = (proc.stdout or "").strip()
        err = (proc.stderr or "").strip()
        return {
            "ok": proc.returncode == 0,
            "code": proc.returncode,
            "stdout": out[-5000:],
            "stderr": err[-2000:],
        }
    except Exception as exc:
        return {"ok": False, "code": None, "stdout": "", "stderr": str(exc)}


def _nats_monitor_snapshot() -> dict[str, Any]:
    try:
        with urllib.request.urlopen("http://127.0.0.1:8223/subsz?subs=1", timeout=3) as resp:
            data = json.loads(resp.read())
    except Exception as exc:
        return {"ok": False, "error": str(exc), "nova_subjects": [], "count": 0}
    subjects = sorted(
        {
            s.get("subject", "")
            for s in data.get("subscriptions_list", [])
            if isinstance(s, dict) and str(s.get("subject", "")).startswith(f"{SUBJECT_NS}.")
        }
    )
    return {"ok": True, "count": len(subjects), "nova_subjects": subjects}


def _service_status() -> list[dict[str, Any]]:
    services = [
        ("gateway", ["systemctl", "is-active", "pipecat-voice.service"]),
        ("cloudflare", ["systemctl", "is-active", "cloudflared.service"]),
        ("nats", ["systemctl", "is-active", "nats-server.service"]),
        ("switch", ["systemctl", "is-active", "switch-agent.service"]),
        ("hermes-bridge", ["systemctl", "--user", "is-active", "pipecat-hermes-agents.service"]),
    ]
    statuses = []
    for name, cmd in services:
        result = _run_readonly(cmd, timeout=3)
        value = result["stdout"].splitlines()[0] if result["stdout"] else "unknown"
        if name == "hermes-bridge" and value == "unknown":
            proc = _run_readonly(["pgrep", "-af", "scripts/hermes_nats_agents.py"], timeout=3)
            if proc["ok"] and proc["stdout"]:
                value = "active"
                result = {**result, "ok": True, "stderr": "verified by process fallback"}
        statuses.append(
            {
                "name": name,
                "status": value,
                "ok": result["ok"] and value == "active",
                "detail": result["stderr"],
            }
        )
    return statuses


def _recent_errors() -> list[str]:
    result = _run_readonly(
        ["journalctl", "-u", "pipecat-voice.service", "--since", "30 min ago", "--no-pager"],
        timeout=5,
    )
    if not result["ok"] and not result["stdout"]:
        return [result["stderr"] or "journalctl unavailable"]
    lines = result["stdout"].splitlines()
    needles = ("error", "warning", "timeout", "failed", "exception")
    return [line[-500:] for line in lines if any(n in line.lower() for n in needles)][-20:]


def _agentops_handoff() -> dict[str, Any]:
    health = _profile_health()
    blocked = [a for a in health["agents"] if a["name"] in {"vaeris", "pathfinder", "synergy", "cosmos"}]
    checks = [
        "Hermes profile chat succeeds with a short bounded prompt.",
        "nova.<agent>.ping returns pong:<agent>:hermes.",
        "nova.<agent>.direct returns within timeout.",
        "nova.<agent>.meet returns within timeout.",
        "Profile is added to GROUP_AGENT_NAMES only after Iris marks it ready.",
    ]
    return {"blocked": blocked, "acceptance_checks": checks}


def _append_room_event(event: dict[str, Any]) -> None:
    try:
        ROOM_HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
        with ROOM_HISTORY_PATH.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(event, ensure_ascii=True) + "\n")
    except Exception as exc:
        logger.warning(f"room history append failed: {exc}")


def _room_history(limit: int = 40) -> list[dict[str, Any]]:
    if not ROOM_HISTORY_PATH.exists():
        return []
    try:
        lines = ROOM_HISTORY_PATH.read_text(encoding="utf-8").splitlines()[-max(1, min(limit, 200)):]
        return [json.loads(line) for line in lines if line.strip()]
    except Exception as exc:
        logger.warning(f"room history read failed: {exc}")
        return []


def _validate_startup() -> dict[str, Any]:
    """Validate required configuration and dependencies at startup.
    
    Returns:
        Dict with 'ok' (bool), 'errors' (list), 'warnings' (list)
    """
    errors: list[str] = []
    warnings: list[str] = []
    
    # Required env vars (loaded from secrets)
    dg_key = os.environ.get("DEEPGRAM_API_KEY", "")
    nats_url = os.environ.get("NATS_URL", "")
    
    if not dg_key:
        errors.append("DEEPGRAM_API_KEY not configured (check /adapt/secrets/m2.env)")
    
    if not nats_url:
        errors.append("NATS_URL not configured (check /adapt/secrets/db.env)")
    
    # Optional but recommended
    if not os.environ.get("GROQ_API_KEY") and not os.environ.get("GROQ_API_KEY_4"):
        warnings.append("GROQ_API_KEY not set; no STT fallback available")
    
    if not os.environ.get("ELEVENLABS_API_KEY"):
        warnings.append("ELEVENLABS_API_KEY not set; no TTS fallback available")
    
    # Validate GROUP_AGENT_NAMES if set
    group_names = os.environ.get("GROUP_AGENT_NAMES", "")
    if group_names:
        names = [n.strip().lower() for n in group_names.split(",") if n.strip()]
        for name in names:
            if not _NAME_RE.match(name):
                errors.append(f"Invalid GROUP_AGENT_NAMES entry: '{name}'")
    
    return {
        "ok": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
    }


# --------------------------------------------------------------- FastAPI app


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Validate startup configuration
    validation = _validate_startup()
    if not validation["ok"]:
        for err in validation["errors"]:
            logger.error(f"Startup validation failed: {err}")
        raise RuntimeError(f"Startup validation failed: {validation['errors']}")
    
    for warn in validation["warnings"]:
        logger.warning(f"Startup: {warn}")
    
    logger.info("Startup validation passed")
    
    try:
        await presence.start()
    except Exception as exc:
        logger.warning(f"presence tracker not started: {exc}")
    try:
        await _get_nats()
    except Exception as exc:
        logger.warning(f"NATS startup warning: {exc}")
    yield
    await presence.stop()
    await _close_nats()


app = FastAPI(lifespan=lifespan, title="pipecat-gateway")
CLIENT_DIR = ROOT / "client"


@app.middleware("http")
async def _no_cache(request: Request, call_next: Any) -> Any:
    response = await call_next(request)
    if request.url.path.startswith("/static/") or request.url.path == "/":
        response.headers["Cache-Control"] = "no-cache, must-revalidate, max-age=0"
    return response


app.mount("/static", StaticFiles(directory=CLIENT_DIR), name="static")


def _asset_v(name: str) -> str:
    p = CLIENT_DIR / name
    return str(int(p.stat().st_mtime)) if p.exists() else "0"


@app.get("/", include_in_schema=False)
async def root() -> Any:
    html = (CLIENT_DIR / "index.html").read_text()
    html = html.replace("/static/styles.css", f"/static/styles.css?v={_asset_v('styles.css')}")
    html = html.replace("/static/app.js", f"/static/app.js?v={_asset_v('app.js')}")
    return Response(content=html, media_type="text/html", headers={"Cache-Control": "no-store"})


@app.get("/healthz")
async def healthz() -> dict:
    return {"status": "ok"}


# --------------------------------------------------------------- Deepgram token


@app.get("/token")
async def get_token() -> dict:
    """Fetch a 30-second Deepgram API key scoped for the Voice Agent WS."""
    dg_key = os.environ.get("DEEPGRAM_API_KEY", "")
    if not dg_key:
        raise HTTPException(500, "DEEPGRAM_API_KEY not configured")
    loop = asyncio.get_running_loop()

    def _fetch() -> dict:
        req = urllib.request.Request(
            "https://api.deepgram.com/v1/auth/grant",
            headers={"Authorization": f"Token {dg_key}", "Content-Type": "application/json"},
            data=b"{}",
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())

    try:
        result = await loop.run_in_executor(None, _fetch)
    except Exception as exc:
        logger.error(f"Deepgram token grant failed: {exc}")
        raise HTTPException(502, "failed to obtain Deepgram token")

    token = result.get("key") or result.get("token") or result.get("access_token") or ""
    if not token:
        raise HTTPException(502, f"unexpected Deepgram auth response: {result}")
    return {"token": token}


# --------------------------------------------------------------- NATS/LLM bridge (SSE)


@app.post("/v1/chat/completions")
async def chat_completions(
    request: Request,
    peer: str = "vox",
    channel: str = "direct",
    agents: str = "",
    mode: str = "parallel",
    moderator: str = "",
) -> StreamingResponse:
    """OpenAI-compatible SSE endpoint called by Deepgram's think step.

    All peers publish to NATS and stream the real nova agent's reply. The
    warm per-nova Hermes gateway (NATS platform plugin) answers on
    nova.<peer>.direct; group peers fan out on nova.<agent>.meet.
    """
    body = await request.json()
    raw_messages: list[dict] = body.get("messages", [])

    # Normalise content to strings; keep only user/assistant turns
    norm_messages: list[dict] = []
    for m in raw_messages:
        role = m.get("role", "")
        if role not in ("user", "assistant"):
            continue
        content = m.get("content", "")
        if isinstance(content, list):
            content = " ".join(p.get("text", "") for p in content if isinstance(p, dict))
        if content:
            norm_messages.append({"role": role, "content": content})

    if not norm_messages:
        raise HTTPException(400, "no usable messages in request body")

    # Last user text (for NATS path)
    text = next(
        (m["content"] for m in reversed(norm_messages) if m["role"] == "user"), ""
    )

    cid = f"chatcmpl-{uuid.uuid4().hex[:8]}"

    def _sse(chunk_text: str) -> str:
        data = {
            "id": cid,
            "object": "chat.completion.chunk",
            "choices": [{"index": 0, "delta": {"content": chunk_text}, "finish_reason": None}],
        }
        return f"data: {json.dumps(data)}\n\n"

    # ---- NATS nova agent (warm Hermes gateway / cold bridge) ---------------
    if not text.strip():
        raise HTTPException(400, "no user message in request body")

    if peer.lower() in GROUP_PEERS:
        async def _stream_nats_group():
            turn_id = f"room-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6]}"
            try:
                nc = await _get_nats()
            except Exception as exc:
                logger.error(f"NATS unavailable for group completions: {exc}")
                yield f'data: {{"error":"NATS unavailable"}}\n\n'
                yield "data: [DONE]\n\n"
                return

            roster = load_roster()
            requested_targets = _parse_agent_csv(agents)
            targets = requested_targets or _configured_group_targets(roster)
            if not targets:
                yield _sse("No roster agents are available for group routing.")
                yield "data: [DONE]\n\n"
                return

            mode_clean = (mode or "parallel").strip().lower()
            moderator_name = (moderator or DEFAULT_MODERATOR).strip().lower()
            if not _NAME_RE.match(moderator_name):
                moderator_name = DEFAULT_MODERATOR
            _append_room_event(
                {
                    "turn_id": turn_id,
                    "ts": datetime.now(timezone.utc).isoformat(),
                    "kind": "user",
                    "mode": mode_clean,
                    "targets": targets,
                    "moderator": moderator_name,
                    "message": text,
                }
            )

            async def _request_agent(agent: str, message: str, group: str | None = None) -> str:
                reply_to = nc.new_inbox()
                q: asyncio.Queue[str | None] = asyncio.Queue()

                async def _on_chunk(msg: Any) -> None:
                    try:
                        payload = json.loads(msg.data.decode())
                    except Exception:
                        return
                    chunk = payload.get("chunk", "")
                    final = bool(payload.get("final", False))
                    if chunk:
                        q.put_nowait(chunk)
                    if final:
                        q.put_nowait(None)

                sub = await nc.subscribe(reply_to, cb=_on_chunk)
                envelope = {
                    "from": SELF_AGENT,
                    "type": "voice",
                    "message": message,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "reply_to": reply_to,
                    "to": agent,
                }
                if group:
                    envelope["group"] = group
                subject = f"{SUBJECT_NS}.{agent}.{GROUP_CHANNEL}"
                logger.info(f"NATS group publish -> {subject} | {message[:80]!r}")
                await nc.publish(subject, json.dumps(envelope).encode())
                await nc.flush()

                chunks: list[str] = []
                try:
                    while True:
                        try:
                            chunk = await asyncio.wait_for(q.get(), timeout=NATS_REPLY_TIMEOUT)
                        except asyncio.TimeoutError:
                            logger.warning(f"NATS group reply timeout waiting on {agent}")
                            break
                        if chunk is None:
                            break
                        chunks.append(chunk)
                finally:
                    try:
                        await sub.unsubscribe()
                    except Exception:
                        pass
                return "".join(chunks).strip()

            fanout_targets = list(targets)
            if mode_clean in {"moderated", "moderator"} and len(fanout_targets) > 1:
                fanout_targets = [agent for agent in fanout_targets if agent != moderator_name] or fanout_targets

            async def _fanout_one(agent: str) -> tuple[str, str]:
                reply = await _request_agent(agent, text, peer.lower())
                return agent, reply

            try:
                if mode_clean in {"moderated", "moderator"}:
                    logger.info(
                        f"NATS moderated group | targets={','.join(fanout_targets)} "
                        f"moderator={moderator_name} | {text[:80]!r}"
                    )
                    results = await asyncio.gather(*[_fanout_one(agent) for agent in fanout_targets])
                    usable = [(agent, reply) for agent, reply in results if reply]
                    for agent, reply in usable:
                        _append_room_event(
                            {
                                "turn_id": turn_id,
                                "ts": datetime.now(timezone.utc).isoformat(),
                                "kind": "agent",
                                "agent": agent,
                                "message": reply,
                            }
                        )
                    if not usable:
                        yield _sse("No room replies came back before timeout.")
                    else:
                        transcript = "\n".join(f"{agent}: {reply}" for agent, reply in usable)
                        prompt = (
                            "You are moderating the live nova voice room for Chase. "
                            "Synthesize the agent replies into one concise spoken answer. "
                            "Mention only the important disagreement or next action. "
                            f"Chase asked: {text}\n\nAgent replies:\n{transcript}"
                        )
                        summary = await _request_agent(moderator_name, prompt, peer.lower())
                        if summary:
                            _append_room_event(
                                {
                                    "turn_id": turn_id,
                                    "ts": datetime.now(timezone.utc).isoformat(),
                                    "kind": "moderator",
                                    "agent": moderator_name,
                                    "message": summary,
                                }
                            )
                            yield _sse(f"{moderator_name.capitalize()}: {summary} ")
                        else:
                            fallback = " ".join(f"{agent.capitalize()}: {reply}" for agent, reply in usable)
                            yield _sse(fallback)
                else:
                    logger.info(
                        f"NATS parallel group | targets={','.join(fanout_targets)} | {text[:80]!r}"
                    )
                    tasks = [asyncio.create_task(_fanout_one(agent)) for agent in fanout_targets]
                    for task in asyncio.as_completed(tasks):
                        agent, reply = await task
                        if reply:
                            _append_room_event(
                                {
                                    "turn_id": turn_id,
                                    "ts": datetime.now(timezone.utc).isoformat(),
                                    "kind": "agent",
                                    "agent": agent,
                                    "message": reply,
                                }
                            )
                            yield _sse(f"{agent.capitalize()}: {reply} ")
            finally:
                yield "data: [DONE]\n\n"

        return StreamingResponse(
            _stream_nats_group(),
            media_type="text/event-stream",
            headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache"},
        )

    async def _stream_nats():
        try:
            nc = await _get_nats()
        except Exception as exc:
            logger.error(f"NATS unavailable for completions: {exc}")
            yield f'data: {{"error":"NATS unavailable"}}\n\n'
            yield "data: [DONE]\n\n"
            return

        reply_to = nc.new_inbox()
        q: asyncio.Queue[str | None] = asyncio.Queue()

        async def _on_chunk(msg: Any) -> None:
            try:
                payload = json.loads(msg.data.decode())
            except Exception:
                return
            chunk = payload.get("chunk", "")
            final = bool(payload.get("final", False))
            if chunk:
                q.put_nowait(chunk)
            if final:
                q.put_nowait(None)

        sub = await nc.subscribe(reply_to, cb=_on_chunk)
        envelope = {
            "from": SELF_AGENT,
            "type": "voice",
            "message": text,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "reply_to": reply_to,
            "to": peer,
        }
        subject = f"{SUBJECT_NS}.{peer}.{channel}"
        logger.info(f"NATS publish -> {subject} | {text[:80]!r}")
        await nc.publish(subject, json.dumps(envelope).encode())
        await nc.flush()

        try:
            while True:
                try:
                    chunk = await asyncio.wait_for(q.get(), timeout=NATS_REPLY_TIMEOUT)
                except asyncio.TimeoutError:
                    logger.warning(f"NATS reply timeout waiting on {peer}")
                    break
                if chunk is None:
                    break
                yield _sse(chunk)
        finally:
            try:
                await sub.unsubscribe()
            except Exception:
                pass
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        _stream_nats(),
        media_type="text/event-stream",
        headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache"},
    )


# --------------------------------------------------------------- roster API


@app.get("/api/roster")
async def get_roster() -> dict:
    return load_roster()


@app.post("/api/roster/agents")
async def add_agent(agent: dict) -> dict:
    name = (agent.get("name") or "").strip().lower()
    if not _NAME_RE.match(name):
        raise HTTPException(400, "invalid agent name (lowercase letters/digits/_-)")
    data = load_roster()
    agents = data.setdefault("agents", [])
    label = agent.get("label") or name.capitalize()
    tier = agent.get("tier") or "custom"
    channel = agent.get("channel") or "direct"
    for a in agents:
        if a["name"] == name:
            a.update({"label": label, "tier": tier, "channel": channel})
            break
    else:
        agents.append({"name": name, "label": label, "tier": tier, "channel": channel})
    save_roster(data)
    await bus.publish({"type": "roster", "data": data})
    return data


@app.delete("/api/roster/agents/{name}")
async def remove_agent(name: str) -> dict:
    data = load_roster()
    before = len(data.get("agents", []))
    data["agents"] = [a for a in data.get("agents", []) if a["name"] != name]
    if len(data["agents"]) == before:
        raise HTTPException(404, f"agent {name} not in roster")
    save_roster(data)
    await bus.publish({"type": "roster", "data": data})
    return data


@app.get("/api/presence")
async def get_presence() -> dict:
    return presence.state


@app.get("/api/profile-health")
async def get_profile_health() -> dict:
    return _profile_health()


@app.get("/api/ops/status")
async def get_ops_status() -> dict:
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "health": {"gateway": "ok"},
        "services": _service_status(),
        "nats": _nats_monitor_snapshot(),
        "recent_errors": _recent_errors(),
        "agentops": _agentops_handoff(),
    }


@app.get("/api/rooms/history")
async def get_room_history(limit: int = 40) -> dict:
    return {"events": _room_history(limit)}


# --------------------------------------------------------------- Canvas API


@app.get("/api/canvas")
async def get_canvas() -> dict:
    """Get current canvas state snapshot."""
    return canvas_state.get_state()


@app.websocket("/ws/canvas")
async def ws_canvas(ws: WebSocket) -> None:
    """WebSocket endpoint for real-time canvas collaboration."""
    await handle_canvas_ws(ws)


# --------------------------------------------------------------- Kanban API


@app.get("/api/kanban")
async def get_kanban() -> dict:
    """Get current kanban board state snapshot."""
    return kanban_board.get_state()


@app.post("/api/kanban/operate")
async def kanban_operate(op: dict) -> dict:
    """Apply an operation to the kanban board."""
    result = kanban_board.apply_operation(op)
    return result


@app.get("/canvas", include_in_schema=False)
async def canvas_page() -> Any:
    """Serve the Iris collaborative canvas page."""
    html = (CLIENT_DIR / "canvas.html").read_text()
    return Response(content=html, media_type="text/html")


@app.get("/kanban", include_in_schema=False)
async def kanban_page() -> Any:
    """Serve the Iris kanban board page."""
    html = (CLIENT_DIR / "kanban.html").read_text()
    return Response(content=html, media_type="text/html")


@app.get("/dashboard", include_in_schema=False)
async def dashboard_page() -> Any:
    """Serve the Iris dashboard page."""
    html = (CLIENT_DIR / "dashboard.html").read_text()
    return Response(content=html, media_type="text/html")


@app.get("/whiteboard", include_in_schema=False)
async def whiteboard_page() -> Any:
    """Serve the Iris whiteboard page."""
    html = (CLIENT_DIR / "whiteboard.html").read_text()
    return Response(content=html, media_type="text/html")


@app.get("/monitor", include_in_schema=False)
async def monitor_page() -> Any:
    """Serve the NATS monitor page."""
    html = (CLIENT_DIR / "monitor.html").read_text()
    return Response(content=html, media_type="text/html")


@app.websocket("/ws/monitor")
async def ws_monitor(ws: WebSocket) -> None:
    """WebSocket endpoint for NATS message monitoring."""
    await ws.accept()
    subscriptions = set()
    logger.info("Monitor: client connected")
    
    try:
        while True:
            data = await ws.receive_text()
            msg = json.loads(data)
            action = msg.get("action")
            
            if action == "subscribe":
                subject = msg.get("subject")
                if subject:
                    subscriptions.add(subject)
                    logger.info(f"Monitor: subscribed to {subject}")
            elif action == "unsubscribe":
                subject = msg.get("subject")
                subscriptions.discard(subject)
    except Exception as exc:
        logger.error(f"Monitor error: {exc}")
    finally:
        logger.info("Monitor: client disconnected")


@app.post("/api/route")
async def set_route(body: dict) -> dict:
    """Broadcast a route-change event; the client reconfigures its DG WS settings."""
    peer = (body.get("peer") or "").strip().lower()
    channel = (body.get("channel") or "direct").strip().lower()
    if peer and peer not in GROUP_PEERS and not _NAME_RE.match(peer):
        raise HTTPException(400, "invalid peer name")
    route = {
        "type": "route",
        "peer": "all" if peer in GROUP_PEERS else peer,
        "channel": GROUP_CHANNEL if peer in GROUP_PEERS else channel,
        "room": body.get("room"),
        "mode": (body.get("mode") or "solo").strip().lower(),
        "agents": _valid_agent_names(body.get("agents") or []),
        "moderator": (body.get("moderator") or DEFAULT_MODERATOR).strip().lower(),
    }
    await bus.publish(route)
    return {k: v for k, v in route.items() if k != "type"}


# --------------------------------------------------------------- Deepgram WS proxy


@app.websocket("/ws/voice")
async def ws_voice_proxy(browser: WebSocket) -> None:
    """Transparent proxy to wss://agent.deepgram.com/v1/agent/converse.

    Keeps the DG API key server-side and avoids short-lived token scope issues.
    Relays binary PCM (browser→DG) and binary TTS + JSON events (DG→browser).
    Includes reconnection logic for upstream resilience.
    """
    dg_key = os.environ.get("DEEPGRAM_API_KEY", "")
    if not dg_key:
        logger.error("DG proxy: DEEPGRAM_API_KEY not configured")
        await browser.accept()
        await browser.close(code=1011, reason="Server configuration error")
        return

    await browser.accept()
    logger.info("DG proxy: browser connected, opening upstream WS")

    max_reconnects = int(os.environ.get("DG_MAX_RECONNECTS", "5"))
    reconnect_delay = float(os.environ.get("DG_RECONNECT_DELAY", "2.0"))
    reconnect_attempts = 0

    while reconnect_attempts < max_reconnects or max_reconnects == 0:
        try:
            async with _ws_lib.connect(
                "wss://agent.deepgram.com/v1/agent/converse",
                additional_headers={"Authorization": f"Token {dg_key}"},
                ping_interval=20,  # Keep-alive ping
                compression=None,
                close_timeout=10,
            ) as dg:
                logger.info(f"DG proxy: upstream connected (attempt {reconnect_attempts + 1})")
                reconnect_attempts = 0  # Reset on successful connection

                async def browser_to_dg() -> None:
                    try:
                        while True:
                            frame = await browser.receive()
                            if frame["type"] == "websocket.disconnect":
                                break
                            if frame.get("bytes") is not None:
                                await dg.send(frame["bytes"])
                            elif frame.get("text") is not None:
                                await dg.send(frame["text"])
                    except Exception as exc:
                        logger.debug(f"DG proxy browser→dg: {exc}")
                    finally:
                        await dg.close()

                async def dg_to_browser() -> None:
                    try:
                        async for msg in dg:
                            if isinstance(msg, bytes):
                                await browser.send_bytes(msg)
                            else:
                                await browser.send_text(msg)
                    except Exception as exc:
                        logger.debug(f"DG proxy dg→browser: {exc}")

                tasks = [
                    asyncio.create_task(browser_to_dg()),
                    asyncio.create_task(dg_to_browser()),
                ]
                done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
                for t in pending:
                    t.cancel()
                    try:
                        await t
                    except (asyncio.CancelledError, Exception):
                        pass

        except _ws_lib.ConnectionClosed as exc:
            logger.warning(f"DG proxy: connection closed unexpectedly (code={exc.code})")
            reconnect_attempts += 1
            if reconnect_attempts < max_reconnects or max_reconnects == 0:
                logger.info(f"DG proxy: reconnecting in {reconnect_delay}s (attempt {reconnect_attempts}/{max_reconnects})")
                await asyncio.sleep(reconnect_delay)
            else:
                logger.error("DG proxy: max reconnection attempts reached")
                try:
                    await browser.close(code=1011, reason="Upstream connection failed")
                except Exception:
                    pass
                break
        except Exception as exc:
            logger.error(f"DG proxy error: {exc}")
            reconnect_attempts += 1
            if reconnect_attempts < max_reconnects or max_reconnects == 0:
                logger.info(f"DG proxy: reconnecting in {reconnect_delay}s (attempt {reconnect_attempts}/{max_reconnects})")
                await asyncio.sleep(reconnect_delay)
            else:
                logger.error("DG proxy: max reconnection attempts reached")
                try:
                    await browser.close(code=1011, reason="Upstream connection failed")
                except Exception:
                    pass
                break

    logger.info("DG proxy: session ended")


# --------------------------------------------------------------- status WebSocket


@app.websocket("/ws/status")
async def ws_status(ws: WebSocket) -> None:
    await ws.accept()
    await bus.add(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        await bus.remove(ws)


# --------------------------------------------------------------- monitor WebSocket (NATS streaming)


@app.websocket("/ws/monitor")
async def ws_monitor(ws: WebSocket) -> None:
    await ws.accept()
    nc = await _get_nats()
    subscriptions: list[Subscription] = []
    message_count = 0

    try:
        while True:
            data = await ws.receive_text()
            msg = json.loads(data)
            if msg.get("action") == "subscribe":
                subject = msg.get("subject", "")
                if subject:
                    async def msg_handler(msg_data):
                        nonlocal message_count
                        message_count += 1
                        try:
                            payload = json.loads(msg_data.data.decode())
                        except:
                            payload = msg_data.data.decode()
                        await ws.send_text(
                            json.dumps(
                                {
                                    "type": "message",
                                    "subject": msg_data.subject,
                                    "payload": payload,
                                    "time": datetime.now(timezone.utc).isoformat(),
                                    "count": message_count,
                                }
                            )
                        )

                    sub = await nc.subscribe(subject, cb=msg_handler)
                    subscriptions.append(sub)
                    await ws.send_text(
                        json.dumps({"type": "system", "text": f"Subscribed to {subject}"})
                    )
            elif msg.get("action") == "unsubscribe":
                subject = msg.get("subject", "")
                for sub in subscriptions:
                    if sub.subject == subject:
                        await sub.unsubscribe()
                        subscriptions.remove(sub)
                        await ws.send_text(
                            json.dumps({"type": "system", "text": f"Unsubscribed from {subject}"})
                        )
    except WebSocketDisconnect:
        logger.info("Monitor WS disconnected")
    finally:
        for sub in subscriptions:
            try:
                await sub.unsubscribe()
            except:
                pass


# --------------------------------------------------------------- entry point

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=18085)
    args = parser.parse_args()
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")
