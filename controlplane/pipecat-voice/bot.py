"""Pipecat speech-to-speech bot bridging WebRTC <-> NATS agents.

Routes audio between a browser client at https://pipe.adaptdev.ai and any
NATS-resident agent or multi-agent room. Front-end gets live presence,
roster CRUD, and live retargeting via WebSocket events.

Pipeline:

    SmallWebRTC.input -> STT (Deepgram | Groq Whisper)
                      -> NATSAgentProcessor
                      -> TTS (Deepgram Aura-2 | ElevenLabs)
                      -> SmallWebRTC.output
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import nats
import uvicorn
from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, HTTPException, Response, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger

from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.audio.vad.vad_analyzer import VADParams
from pipecat.frames.frames import BotStartedSpeakingFrame, BotStoppedSpeakingFrame
from pipecat.observers.base_observer import BaseObserver, FramePushed
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.transports.base_transport import TransportParams
from pipecat.transports.smallwebrtc.connection import IceServer, SmallWebRTCConnection
from pipecat.transports.smallwebrtc.transport import SmallWebRTCTransport

from nats_agent import NATSAgentProcessor

ROOT = Path(__file__).parent
ROSTER_PATH = ROOT / "roster.json"

for env_file in (
    Path("/adapt/secrets/db.env"),
    Path("/adapt/secrets/m2.env"),
    ROOT / ".env",
):
    if env_file.exists():
        load_dotenv(env_file, override=True)


# ----------------------------------------------------------------- service factories


def _build_stt() -> Any:
    """Return a Pipecat STT service. Deepgram primary; Groq Whisper fallback."""
    if dg_key := os.environ.get("DEEPGRAM_API_KEY"):
        from pipecat.services.deepgram.stt import DeepgramSTTService

        logger.info("STT: Deepgram (Nova-3, endpointing=False)")
        # Disable Deepgram's internal endpointing so it never sends mid-utterance
        # finals on its own. Turn completion is driven solely by SileroVAD, which
        # sends VADUserStoppedSpeakingFrame → STT finalize() → one TranscriptionFrame
        # per utterance. Without this, Deepgram splits long utterances at sentence
        # boundaries and floods the bridge with fragments.
        return DeepgramSTTService(
            api_key=dg_key,
            settings=DeepgramSTTService.Settings(endpointing=False),
        )
    if groq_key := (os.environ.get("GROQ_API_KEY") or os.environ.get("GROQ_API_KEY_4")):
        from pipecat.services.groq.stt import GroqSTTService

        logger.info("STT: Groq Whisper (fallback)")
        return GroqSTTService(api_key=groq_key)
    raise RuntimeError("No STT API key (DEEPGRAM_API_KEY or GROQ_API_KEY)")


def _build_tts() -> Any:
    """Return a Pipecat TTS service. Deepgram Aura-2 primary; ElevenLabs fallback."""
    if dg_key := os.environ.get("DEEPGRAM_API_KEY"):
        from pipecat.services.deepgram.tts import DeepgramTTSService

        logger.info("TTS: Deepgram Aura-2")
        return DeepgramTTSService(api_key=dg_key)
    if el_key := os.environ.get("ELEVENLABS_API_KEY"):
        from pipecat.services.elevenlabs.tts import ElevenLabsTTSService

        logger.info("TTS: ElevenLabs (fallback)")
        return ElevenLabsTTSService(
            api_key=el_key, voice_id=os.environ.get("ELEVENLABS_VOICE_ID", "EXAVITQu4vr4xnSDxMaL")
        )
    raise RuntimeError("No TTS API key (DEEPGRAM_API_KEY or ELEVENLABS_API_KEY)")


# --------------------------------------------------------- status broadcast bus


class EventBus:
    """In-process pub/sub of JSON events to WebSocket subscribers."""

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


class BotSpeakingObserver(BaseObserver):
    """Translate bot-speaking lifecycle frames to orb status events."""

    async def on_push_frame(self, data: FramePushed) -> None:
        if isinstance(data.frame, BotStartedSpeakingFrame):
            await bus.publish("speaking")
        elif isinstance(data.frame, BotStoppedSpeakingFrame):
            await bus.publish("ready")


# -------------------------------------------------------------- presence pinger


class PresenceTracker:
    """Periodically polls NATS monitoring (/subsz) and broadcasts online state.

    Online == ``<ns>.<name>.direct`` has at least one subscriber on the bus.
    Honest signal: we only call an agent online if it's actually listening.
    Falls back to a connection-presence ping if the monitoring port is gone.
    """

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
        logger.info(f"presence tracker started (monitor={self._monitor_url})")

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            try: await self._task
            except asyncio.CancelledError: pass
            self._task = None

    async def _fetch_subjects(self) -> set[str]:
        import urllib.request
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
                changes: dict[str, bool] = {}
                now = time.time()
                wildcard = f"{self._ns}.*.direct" in subjects or f"{self._ns}.>" in subjects
                for n in names:
                    direct = f"{self._ns}.{n}.direct"
                    online = direct in subjects  # explicit subscription wins over wildcard
                    if wildcard and not online:
                        # honest signal: wildcard listener exists but we still
                        # want a per-name dot. Treat as offline unless we see
                        # the explicit subject; wildcard alone isn't presence.
                        pass
                    prev = self._state.get(n, {}).get("online")
                    if prev != online:
                        changes[n] = online
                    self._state[n] = {
                        "online": online,
                        "last_seen": now if online else self._state.get(n, {}).get("last_seen", 0),
                    }
                payload = {"type": "presence", "snapshot": self._state}
                if changes:
                    payload["changes"] = changes
                await bus.publish(payload)
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # noqa: BLE001
                logger.warning(f"presence loop error: {exc}")
            await asyncio.sleep(self._interval)


presence = PresenceTracker(subject_ns=os.environ.get("SUBJECT_NS", "nova"))


# -------------------------------------------------------------------- roster IO


def load_roster() -> dict:
    """Load roster.json (idempotent; creates empty default if missing)."""
    if not ROSTER_PATH.exists():
        default = {"self": "chase", "default_peer": "switch", "agents": []}
        ROSTER_PATH.write_text(json.dumps(default, indent=2))
        return default
    try:
        return json.loads(ROSTER_PATH.read_text())
    except Exception as exc:  # noqa: BLE001
        logger.error(f"roster.json unreadable: {exc}")
        return {"self": "chase", "default_peer": "switch", "agents": []}


def save_roster(data: dict) -> None:
    """Atomically persist roster.json."""
    tmp = ROSTER_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=2))
    tmp.replace(ROSTER_PATH)


_NAME_RE = re.compile(r"^[a-z][a-z0-9_-]{1,30}$")


# --------------------------------------------------------- per-session state


class Session:
    """Mutable per-pipeline state that HTTP endpoints can mutate."""

    def __init__(self) -> None:
        self.bridge: NATSAgentProcessor | None = None

    async def set_peer(self, peer: str, channel: str = "direct") -> None:
        if self.bridge is None:
            raise RuntimeError("no active pipeline session")
        self.bridge.set_peer(peer, channel)
        await bus.publish({"type": "route", "peer": peer, "channel": channel, "room": None})

    async def join_room(self, room_id: str | None = None) -> str:
        if self.bridge is None:
            raise RuntimeError("no active pipeline session")
        rid = await self.bridge.join_room(room_id)
        await bus.publish({"type": "route", "peer": None, "channel": "room", "room": rid})
        return rid

    async def leave_room(self) -> None:
        if self.bridge is None:
            return
        await self.bridge.leave_room()
        await bus.publish(
            {"type": "route", "peer": self.bridge.peer, "channel": self.bridge.channel, "room": None}
        )


session = Session()  # single-user front-end; one active pipeline at a time


# ------------------------------------------------------------------ pipeline run


async def run_bot(
    webrtc_connection: SmallWebRTCConnection, peer: str, channel: str, room: str | None
) -> None:
    """Run a pipeline session for one connected client."""
    logger.info(f"bot session start (peer={peer}, channel={channel}, room={room})")
    await bus.publish("connecting")

    transport = SmallWebRTCTransport(
        webrtc_connection=webrtc_connection,
        params=TransportParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            vad_analyzer=SileroVADAnalyzer(params=VADParams(stop_secs=2.0)),
        ),
    )
    stt = _build_stt()
    tts = _build_tts()

    nats_url = os.environ.get("NATS_URL")
    if not nats_url:
        raise RuntimeError("NATS_URL is not set")

    async def on_control(directive: dict) -> None:
        action = directive.get("action")
        if action == "set_peer" and (p := directive.get("peer")):
            ch = directive.get("channel", "direct")
            session.bridge.set_peer(p, ch) if session.bridge else None
            await bus.publish({"type": "route", "peer": p, "channel": ch, "room": None})
        elif action == "join_room":
            rid = await session.join_room(directive.get("room"))
            logger.info(f"control directive joined room {rid}")
        elif action == "leave_room":
            await session.leave_room()

    bridge = NATSAgentProcessor(
        nats_url=nats_url,
        self_agent=os.environ.get("SELF_AGENT", "chase"),
        peer=peer,
        channel=channel,
        subject_ns=os.environ.get("SUBJECT_NS", "nova"),
        reply_timeout=float(os.environ.get("NATS_REPLY_TIMEOUT", "30")),
        on_status=bus.publish,
        on_control=on_control,
    )
    session.bridge = bridge

    pipeline = Pipeline(
        [transport.input(), stt, bridge, tts, transport.output()]
    )
    task = PipelineTask(
        pipeline,
        params=PipelineParams(enable_metrics=True, enable_usage_metrics=True),
        observers=[BotSpeakingObserver()],
    )

    @transport.event_handler("on_client_connected")
    async def _on_connect(_t, _client):
        logger.info("client connected")
        if room:
            await bridge.join_room(room)
        await bus.publish("ready")
        await bus.publish(
            {"type": "route", "peer": bridge.peer, "channel": bridge.channel, "room": bridge.room_id}
        )

    @transport.event_handler("on_client_disconnected")
    async def _on_disconnect(_t, _client):
        logger.info("client disconnected")
        await bus.publish("idle")
        await task.cancel()

    runner = PipelineRunner(handle_sigint=False)
    try:
        await runner.run(task)
    except Exception as exc:  # noqa: BLE001
        logger.exception(f"pipeline error: {exc}")
        await bus.publish("error")
    finally:
        if session.bridge is bridge:
            session.bridge = None


# ----------------------------------------------------------------------- HTTP app


pcs_map: dict[str, SmallWebRTCConnection] = {}
ice_servers = [IceServer(urls="stun:stun.l.google.com:19302")]


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await presence.start()
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"presence tracker not started: {exc}")
    yield
    await presence.stop()
    await asyncio.gather(*(pc.disconnect() for pc in pcs_map.values()), return_exceptions=True)
    pcs_map.clear()


app = FastAPI(lifespan=lifespan, title="pipecat-voice")
CLIENT_DIR = ROOT / "client"


@app.middleware("http")
async def _no_cache_static(request, call_next):
    """Browser/CDN must always re-validate the front-end bundle."""
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
    """Serve index.html with cache-busting ?v=<mtime> on referenced assets."""
    html = (CLIENT_DIR / "index.html").read_text()
    html = html.replace("/static/styles.css", f"/static/styles.css?v={_asset_v('styles.css')}")
    html = html.replace("/static/app.js", f"/static/app.js?v={_asset_v('app.js')}")
    return Response(content=html, media_type="text/html",
                    headers={"Cache-Control": "no-store"})


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


# -------- roster API
@app.get("/api/roster")
async def get_roster() -> dict:
    return load_roster()


@app.post("/api/roster/agents")
async def add_agent(agent: dict) -> dict:
    """Add or update an agent. Body: {name, label?, tier?, channel?}."""
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


# -------- routing API
@app.post("/api/route")
async def set_route(body: dict) -> dict:
    """Live-retarget the active pipeline. Body accepts ``peer``+``channel`` or
    ``room`` (room_id; pass empty string to leave room)."""
    if session.bridge is None:
        raise HTTPException(409, "no active session")
    if "room" in body:
        rid = body["room"]
        if rid in (None, ""):
            await session.leave_room()
            return {"channel": session.bridge.channel, "peer": session.bridge.peer, "room": None}
        rid = await session.join_room(rid or None)
        return {"channel": "room", "peer": None, "room": rid}
    peer = body.get("peer")
    channel = body.get("channel", "direct")
    if not peer:
        raise HTTPException(400, "peer required for direct/meet routing")
    await session.set_peer(peer, channel)
    return {"channel": channel, "peer": peer, "room": None}


@app.websocket("/ws/status")
async def ws_status(ws: WebSocket) -> None:
    await ws.accept()
    await bus.add(ws)
    # Hydrate the new client with current roster + presence.
    try:
        await ws.send_text(json.dumps({"type": "roster", "data": load_roster()}))
        await ws.send_text(json.dumps({"type": "presence", "snapshot": presence.state}))
    except Exception:
        pass
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        await bus.remove(ws)


@app.post("/api/offer")
async def offer(request: dict, background_tasks: BackgroundTasks) -> dict:
    """SDP offer -> answer. ``peer``/``channel``/``room`` route the conversation."""
    pc_id = request.get("pc_id")
    roster = load_roster()
    peer = request.get("peer") or roster.get("default_peer", "switch")
    channel = request.get("channel") or "direct"
    room = request.get("room")
    if room:
        channel = "room"

    if pc_id and pc_id in pcs_map:
        pc = pcs_map[pc_id]
        await pc.renegotiate(
            sdp=request["sdp"],
            type=request["type"],
            restart_pc=request.get("restart_pc", False),
        )
    else:
        pc = SmallWebRTCConnection(ice_servers)
        await pc.initialize(sdp=request["sdp"], type=request["type"])

        @pc.event_handler("closed")
        async def _on_closed(c: SmallWebRTCConnection) -> None:
            pcs_map.pop(c.pc_id, None)

        background_tasks.add_task(run_bot, pc, peer, channel, room)

    answer = pc.get_answer()
    pcs_map[answer["pc_id"]] = pc
    return answer


# --------------------------------------------------------------------------- main

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default=os.environ.get("HOST", "0.0.0.0"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "18085")))
    args = parser.parse_args()
    uvicorn.run(app, host=args.host, port=args.port)
