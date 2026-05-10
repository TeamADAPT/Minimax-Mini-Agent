"""NATS agent bridge as a Pipecat FrameProcessor.

Replaces the LLM stage in a Pipecat pipeline. Routes user transcripts to one of
three destinations:

* **direct** — single peer agent at ``nova.<peer>.direct`` (1:1 conversation).
* **meet**   — single peer agent at ``nova.<peer>.meet``   (legacy 1:1 meeting).
* **room**   — multi-agent room at ``nova.room.<room_id>``. The bot subscribes
  to the same subject so every agent's reply is heard. Optional ``addressed``
  field hints which agent should speak next.

Replies stream back via a per-request ``reply_to`` inbox. Agents may also
embed control directives in chunks - ``{"control": {"action": "set_peer",
"peer": "echo"}}`` - which the bridge applies live (used by the *switch*
router agent).

Status callbacks (``on_status``) emit short string events for the UI orb.
"""

from __future__ import annotations

import asyncio
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable

import nats
from loguru import logger
from nats.aio.client import Client as NATSClient
from nats.aio.msg import Msg
from nats.aio.subscription import Subscription

from pipecat.frames.frames import (
    CancelFrame,
    EndFrame,
    ErrorFrame,
    Frame,
    LLMFullResponseEndFrame,
    LLMFullResponseStartFrame,
    LLMTextFrame,
    StartFrame,
    TranscriptionFrame,
)
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor

ControlHandler = Callable[[dict], Awaitable[None]]
StatusHandler = Callable[[str], Awaitable[None]]


class NATSAgentProcessor(FrameProcessor):
    """Bridge user transcripts to NATS-resident agents and stream replies back."""

    def __init__(
        self,
        *,
        nats_url: str,
        self_agent: str = "chase",
        peer: str = "switch",
        channel: str = "direct",
        subject_ns: str = "nova",
        reply_timeout: float = 30.0,
        on_status: StatusHandler | None = None,
        on_control: ControlHandler | None = None,
        **kwargs,
    ) -> None:
        """Initialize the NATS agent bridge.

        Args:
            nats_url: NATS connection URL with credentials.
            self_agent: This bot's NATS identity. Inbox is
                ``nova.<self_agent>.direct`` and ``.meet``.
            peer: Default outbound peer (``direct``/``meet`` modes).
            channel: ``direct``, ``meet``, or ``room``. Determines outbound
                subject and which subscription set is active.
            reply_timeout: Seconds to wait for any reply chunk before raising
                an ErrorFrame and terminating the LLM response window.
            on_status: Optional ``async cb(event_name)`` for UI orb updates.
            on_control: Optional ``async cb(directive_dict)`` invoked when a
                reply contains ``"control": {...}``. Used by the *switch*
                routing agent to retarget conversations on the fly.
            **kwargs: Forwarded to ``FrameProcessor``.
        """
        super().__init__(**kwargs)
        self._nats_url = nats_url
        self._self_agent = self_agent
        self._peer = peer
        self._channel = channel
        self._ns = subject_ns
        self._room_id: str | None = None
        self._reply_timeout = reply_timeout
        self._on_status = on_status
        self._on_control = on_control

        self._nc: NATSClient | None = None
        self._inbound_subs: dict[str, Subscription] = {}
        self._room_sub: Subscription | None = None

        # Per-request reply tracking.
        self._reply_queues: dict[str, asyncio.Queue[str | None]] = {}
        self._reply_subs: dict[str, Subscription] = {}

        # Transcript debounce — Deepgram emits multiple TranscriptionFrames per
        # utterance (one per recognized sentence). Buffer them and flush after
        # 600ms of silence so we publish a single joined message per turn.
        self._transcript_buffer: list[str] = []
        self._transcript_debounce_task: asyncio.Task | None = None
        self._transcript_debounce_s: float = 0.6

    # ----------------------------------------------------------------- props

    @property
    def peer(self) -> str:
        """Current outbound peer name."""
        return self._peer

    @property
    def channel(self) -> str:
        """Current outbound channel: ``direct`` | ``meet`` | ``room``."""
        return self._channel

    @property
    def room_id(self) -> str | None:
        """Active room id (only meaningful when ``channel == 'room'``)."""
        return self._room_id

    @property
    def nc(self) -> NATSClient | None:
        """Underlying NATS client (read-only access for ops endpoints)."""
        return self._nc

    # ----------------------------------------------------- runtime targeting

    def set_peer(self, peer: str, channel: str = "direct") -> None:
        """Retarget outbound to a single peer (``direct`` or ``meet``)."""
        if channel not in ("direct", "meet"):
            raise ValueError("channel must be 'direct' or 'meet' for set_peer")
        prev = (self._peer, self._channel, self._room_id)
        self._peer = peer
        self._channel = channel
        self._room_id = None
        logger.info(f"NATS retarget: {prev} -> ({peer}, {channel})")

    async def join_room(self, room_id: str | None = None) -> str:
        """Switch to room mode. Subscribes the bot to the room subject so it
        hears every member. Returns the room id."""
        rid = room_id or uuid.uuid4().hex[:10]
        if self._room_sub is not None:
            await self._room_sub.unsubscribe()
            self._room_sub = None
        self._room_id = rid
        self._channel = "room"
        if self._nc and self._nc.is_connected:
            self._room_sub = await self._nc.subscribe(
                f"{self._ns}.room.{rid}", cb=self._on_room_message
            )
        logger.info(f"NATS joined room: {rid}")
        return rid

    async def leave_room(self) -> None:
        """Leave any active room and revert to direct/meet on the prior peer."""
        if self._room_sub is not None:
            await self._room_sub.unsubscribe()
            self._room_sub = None
        self._room_id = None
        if self._channel == "room":
            self._channel = "direct"
        logger.info("NATS left room")

    # ---------------------------------------------------------------- helpers

    def _outbound_subject(self) -> str:
        if self._channel == "room" and self._room_id:
            return f"{self._ns}.room.{self._room_id}"
        return f"{self._ns}.{self._peer}.{self._channel}"

    async def _emit_status(self, event: str) -> None:
        if self._on_status is None:
            return
        try:
            await self._on_status(event)
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"status callback failed: {exc}")

    async def _emit_control(self, directive: dict) -> None:
        if self._on_control is None:
            return
        try:
            await self._on_control(directive)
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"control callback failed: {exc}")

    # --------------------------------------------------------------- lifecycle

    async def _connect(self) -> None:
        if self._nc and self._nc.is_connected:
            return
        logger.info(f"NATS connecting -> {self._nats_url.split('@')[-1]}")
        self._nc = await nats.connect(
            self._nats_url,
            name=f"pipecat-voice-{self._self_agent}",
            reconnect_time_wait=1,
            max_reconnect_attempts=-1,
        )
        # Inbound 1:1 channels (legacy + meet).
        for ch in ("direct", "meet"):
            subject = f"{self._ns}.{self._self_agent}.{ch}"
            self._inbound_subs[ch] = await self._nc.subscribe(
                subject, cb=self._on_inbound_legacy
            )
            logger.info(f"NATS subscribed: {subject}")
        # Re-subscribe room if we had one already.
        if self._channel == "room" and self._room_id:
            self._room_sub = await self._nc.subscribe(
                f"{self._ns}.room.{self._room_id}", cb=self._on_room_message
            )
        await self._emit_status("connected")

    async def _disconnect(self) -> None:
        for sub in list(self._reply_subs.values()):
            try: await sub.unsubscribe()
            except Exception: pass
        self._reply_subs.clear()
        for q in self._reply_queues.values():
            q.put_nowait(None)
        self._reply_queues.clear()
        for sub in self._inbound_subs.values():
            try: await sub.unsubscribe()
            except Exception: pass
        self._inbound_subs.clear()
        if self._room_sub is not None:
            try: await self._room_sub.unsubscribe()
            except Exception: pass
            self._room_sub = None
        if self._nc is not None:
            try: await self._nc.drain()
            except Exception: pass
            self._nc = None
        await self._emit_status("disconnected")

    # ------------------------------------------------------------ NATS handlers

    async def _on_inbound_legacy(self, msg: Msg) -> None:
        """Handle non-streaming replies posted to nova.<self>.<channel>."""
        try:
            payload = json.loads(msg.data.decode())
        except Exception:
            return
        if payload.get("from") == self._self_agent:
            return  # don't speak our own publishes
        text = payload.get("message") or payload.get("chunk") or ""
        if not text:
            return
        await self._emit_status("receiving")
        await self.push_frame(LLMFullResponseStartFrame())
        prefix = ""
        if (sender := payload.get("from")) and sender != self._peer:
            prefix = f"{sender} says, "
        await self.push_frame(LLMTextFrame(prefix + text))
        await self.push_frame(LLMFullResponseEndFrame())

    async def _on_room_message(self, msg: Msg) -> None:
        """Handle messages on nova.room.<id> from any participant."""
        try:
            payload = json.loads(msg.data.decode())
        except Exception:
            return
        if payload.get("from") == self._self_agent:
            return  # ignore own publishes
        text = payload.get("message") or payload.get("chunk") or ""
        if not text:
            return
        speaker = payload.get("from", "agent")
        await self._emit_status("receiving")
        await self.push_frame(LLMFullResponseStartFrame())
        await self.push_frame(LLMTextFrame(f"{speaker} says, {text}"))
        await self.push_frame(LLMFullResponseEndFrame())

    async def _on_reply_chunk(self, msg: Msg, reply_to: str) -> None:
        """Streamed chunk on a per-request inbox."""
        q = self._reply_queues.get(reply_to)
        if q is None:
            return
        try:
            payload = json.loads(msg.data.decode())
        except Exception:
            return
        if (control := payload.get("control")):
            await self._emit_control(control)
        chunk = payload.get("chunk", "")
        final = bool(payload.get("final", False))
        if chunk:
            q.put_nowait(chunk)
        if final:
            q.put_nowait(None)

    # --------------------------------------------------------- request/stream

    async def _send_and_stream(self, text: str, addressed: str | None = None) -> None:
        if not (self._nc and self._nc.is_connected):
            await self.push_frame(ErrorFrame("NATS not connected"))
            return

        reply_to = self._nc.new_inbox()
        q: asyncio.Queue[str | None] = asyncio.Queue()
        self._reply_queues[reply_to] = q

        async def _cb(m: Msg) -> None:
            await self._on_reply_chunk(m, reply_to)

        sub = await self._nc.subscribe(reply_to, cb=_cb)
        self._reply_subs[reply_to] = sub

        envelope: dict[str, Any] = {
            "from": self._self_agent,
            "type": "voice",
            "message": text,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "reply_to": reply_to,
        }
        if self._channel == "room" and self._room_id:
            envelope["room"] = self._room_id
            if addressed:
                envelope["addressed"] = addressed
        else:
            envelope["to"] = self._peer

        subject = self._outbound_subject()
        logger.info(f"NATS publish -> {subject} (reply_to={reply_to[-8:]})")
        await self._emit_status("sending")
        await self._nc.publish(subject, json.dumps(envelope).encode())
        await self._nc.flush()

        await self.push_frame(LLMFullResponseStartFrame())
        await self._emit_status("receiving")
        try:
            while True:
                try:
                    chunk = await asyncio.wait_for(q.get(), timeout=self._reply_timeout)
                except asyncio.TimeoutError:
                    target = self._room_id or self._peer
                    logger.warning(f"NATS reply timeout from {target}")
                    await self.push_frame(
                        ErrorFrame(f"No reply from {target} in {self._reply_timeout}s")
                    )
                    break
                if chunk is None:
                    break
                await self.push_frame(LLMTextFrame(chunk))
        finally:
            await self.push_frame(LLMFullResponseEndFrame())
            self._reply_queues.pop(reply_to, None)
            sub_to_close = self._reply_subs.pop(reply_to, None)
            if sub_to_close is not None:
                try: await sub_to_close.unsubscribe()
                except Exception: pass

    # -------------------------------------------------------- transcript debounce

    async def _flush_transcripts(self) -> None:
        """Wait for the debounce window, then publish the buffered transcript."""
        await asyncio.sleep(self._transcript_debounce_s)
        if self._transcript_buffer:
            combined = " ".join(self._transcript_buffer)
            self._transcript_buffer.clear()
            await self._send_and_stream(combined)

    # -------------------------------------------------- FrameProcessor hooks

    async def process_frame(self, frame: Frame, direction: FrameDirection) -> None:
        """Route frames; transcripts trigger NATS publish + reply streaming."""
        await super().process_frame(frame, direction)

        if isinstance(frame, StartFrame):
            await self._connect()
            await self.push_frame(frame, direction)
            return

        if isinstance(frame, (EndFrame, CancelFrame)):
            await self._disconnect()
            await self.push_frame(frame, direction)
            return

        if isinstance(frame, TranscriptionFrame) and direction == FrameDirection.DOWNSTREAM:
            text = (frame.text or "").strip()
            if text:
                self._transcript_buffer.append(text)
                if self._transcript_debounce_task is not None:
                    self._transcript_debounce_task.cancel()
                self._transcript_debounce_task = asyncio.create_task(self._flush_transcripts())
            await self.push_frame(frame, direction)
            return

        await self.push_frame(frame, direction)
