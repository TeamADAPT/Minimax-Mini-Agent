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
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger
from nats.aio.client import Client as NATSClient

ROOT = Path(__file__).parent
ROSTER_PATH = ROOT / "roster.json"

for _env in (Path("/adapt/secrets/db.env"), Path("/adapt/secrets/m2.env"), ROOT / ".env"):
    if _env.exists():
        load_dotenv(_env, override=True)

SELF_AGENT = os.environ.get("SELF_AGENT", "chase")
SUBJECT_NS = os.environ.get("SUBJECT_NS", "nova")
NATS_REPLY_TIMEOUT = float(os.environ.get("NATS_REPLY_TIMEOUT", "30"))

# ------------------------------------------------------------------ NATS client

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


# --------------------------------------------------------------- FastAPI app


@asynccontextmanager
async def lifespan(app: FastAPI):
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
    peer: str = "switch",
    channel: str = "direct",
) -> StreamingResponse:
    """OpenAI-compatible SSE endpoint called by Deepgram's think step.

    Extracts the last user message from the messages[] array, publishes it
    to the NATS nova collective, and streams the reply as chat completion chunks.
    The model/provider fields in the request body are ignored — routing is
    determined by the ``peer`` and ``channel`` query parameters.
    """
    body = await request.json()
    messages: list[dict] = body.get("messages", [])

    text = ""
    for msg in reversed(messages):
        if msg.get("role") == "user":
            content = msg.get("content", "")
            text = (
                content
                if isinstance(content, str)
                else " ".join(
                    p.get("text", "") for p in content if isinstance(p, dict)
                )
            )
            break

    if not text.strip():
        raise HTTPException(400, "no user message in request body")

    async def _stream():
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

        cid = f"chatcmpl-{uuid.uuid4().hex[:8]}"
        try:
            while True:
                try:
                    chunk = await asyncio.wait_for(q.get(), timeout=NATS_REPLY_TIMEOUT)
                except asyncio.TimeoutError:
                    logger.warning(f"NATS reply timeout waiting on {peer}")
                    break
                if chunk is None:
                    break
                data = {
                    "id": cid,
                    "object": "chat.completion.chunk",
                    "choices": [
                        {"index": 0, "delta": {"content": chunk}, "finish_reason": None}
                    ],
                }
                yield f"data: {json.dumps(data)}\n\n"
        finally:
            try:
                await sub.unsubscribe()
            except Exception:
                pass
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        _stream(),
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


@app.post("/api/route")
async def set_route(body: dict) -> dict:
    """Broadcast a route-change event; the client reconfigures its DG WS settings."""
    peer = (body.get("peer") or "").strip()
    channel = (body.get("channel") or "direct").strip()
    if peer and not _NAME_RE.match(peer):
        raise HTTPException(400, "invalid peer name")
    await bus.publish({"type": "route", "peer": peer, "channel": channel, "room": None})
    return {"peer": peer, "channel": channel}


# --------------------------------------------------------------- Deepgram WS proxy


@app.websocket("/ws/voice")
async def ws_voice_proxy(browser: WebSocket) -> None:
    """Transparent proxy to wss://agent.deepgram.com/v1/agent/converse.

    Keeps the DG API key server-side and avoids short-lived token scope issues.
    Relays binary PCM (browser→DG) and binary TTS + JSON events (DG→browser).
    """
    await browser.accept()
    dg_key = os.environ.get("DEEPGRAM_API_KEY", "")
    if not dg_key:
        await browser.close(code=1011, reason="DEEPGRAM_API_KEY not configured")
        return

    logger.info("DG proxy: browser connected, opening upstream WS")
    try:
        async with _ws_lib.connect(
            "wss://agent.deepgram.com/v1/agent/converse",
            additional_headers={"Authorization": f"Token {dg_key}"},
            ping_interval=None,
            compression=None,
        ) as dg:
            logger.info("DG proxy: upstream connected")

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
            _, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            for t in pending:
                t.cancel()
                try:
                    await t
                except (asyncio.CancelledError, Exception):
                    pass

    except WebSocketDisconnect:
        pass
    except Exception as exc:
        logger.error(f"DG proxy error: {exc}")
        try:
            await browser.close(code=1011)
        except Exception:
            pass
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


# --------------------------------------------------------------- entry point

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=18085)
    args = parser.parse_args()
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")
