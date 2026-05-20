"""Visible Echo CLI NATS bridge.

This bridge is intentionally narrow: it subscribes to Echo's NATS subjects and
types incoming messages into the already-open Echo Hermes TUI. It exists because
`hermes chat -q --continue` updates session state in the background, but does
not render messages in the operator-visible TUI.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import os
import re
import time
import subprocess
import sys
import tempfile
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import nats
from loguru import logger

NS = os.environ.get("SUBJECT_NS", "nova")
AGENT = os.environ.get("ECHO_TUI_AGENT", "echo")
WINDOW_NAME = os.environ.get("ECHO_TUI_WINDOW_NAME", "Echo CLI")
WINDOW_CLASS = os.environ.get("ECHO_TUI_WINDOW_CLASS", "").strip()
WINDOW_ID = os.environ.get("ECHO_TUI_WINDOW_ID", "").strip()
DELIVERY_TIMEOUT = float(os.environ.get("ECHO_TUI_DELIVERY_TIMEOUT", "300"))
IDLE_POLL_SECONDS = float(os.environ.get("ECHO_TUI_IDLE_POLL_SECONDS", "1.5"))
MAX_QUEUE_DEPTH = int(os.environ.get("ECHO_TUI_MAX_QUEUE_DEPTH", "8"))
REPLY_CAPTURE_TIMEOUT = float(os.environ.get("ECHO_TUI_REPLY_CAPTURE_TIMEOUT", "30"))
PROFILE_ROOT = Path(os.environ.get("ECHO_PROFILE_ROOT", "/home/x/.hermes/profiles/echo"))

_delivery_lock = asyncio.Lock()
_queue_guard = asyncio.Lock()
_work_queue: asyncio.Queue["BridgeWork"] = asyncio.Queue()
_processing = False


@dataclass(frozen=True)
class BridgeWork:
    subject: str
    channel: str
    sender: str
    message: str
    reply_to: object
    event_id: str


def _load_nats_url() -> str:
    if url := os.environ.get("NATS_URL"):
        return url
    text = Path("/adapt/secrets/db.env").read_text(encoding="utf-8")
    match = re.search(r'^NATS_URL\s*=\s*"?([^"\n]+)"?', text, re.M)
    if not match:
        raise RuntimeError("NATS_URL not found")
    return match.group(1).strip().strip('"')


def _run_xdotool(*args: str, input_text: str | None = None, timeout: float = 30) -> str:
    proc = subprocess.run(
        ["xdotool", *args],
        input=input_text,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or proc.stdout or "xdotool failed").strip())
    return proc.stdout.strip()


def _window_id() -> str:
    if WINDOW_ID:
        _run_xdotool("getwindowname", WINDOW_ID, timeout=10)
        return WINDOW_ID
    if WINDOW_CLASS:
        output = _run_xdotool("search", "--class", WINDOW_CLASS, timeout=10)
        ids = [line.strip() for line in output.splitlines() if line.strip()]
        if ids:
            return ids[-1]
    output = _run_xdotool("search", "--name", WINDOW_NAME, timeout=10)
    ids = [line.strip() for line in output.splitlines() if line.strip()]
    if not ids:
        target = WINDOW_CLASS or WINDOW_NAME
        raise RuntimeError(f"{target!r} window not found")
    return ids[-1]


def _active_title() -> str:
    try:
        return _run_xdotool("getactivewindow", "getwindowname", timeout=10)
    except Exception:
        return ""


async def _wait_for_idle_window() -> str:
    deadline = asyncio.get_running_loop().time() + DELIVERY_TIMEOUT
    last_title = None
    while asyncio.get_running_loop().time() < deadline:
        try:
            win = _window_id()
            _run_xdotool("windowactivate", "--sync", win, timeout=10)
            title = _active_title()
            if title != last_title:
                logger.info(f"Echo TUI active title: {title!r}")
                last_title = title
            if WINDOW_ID or WINDOW_CLASS:
                return win
            if title == WINDOW_NAME:
                return win
        except Exception as exc:
            logger.debug(f"Echo TUI not ready: {exc}")
        await asyncio.sleep(IDLE_POLL_SECONDS)
    raise TimeoutError(f"Echo TUI did not become idle within {DELIVERY_TIMEOUT}s")


def _clear_input() -> None:
    for key in ("Escape", "ctrl+u", "ctrl+a", "ctrl+k"):
        _run_xdotool("key", "--clearmodifiers", key, timeout=10)


def _type_prompt(prompt: str) -> None:
    prompt = re.sub(r"\s+", " ", prompt).strip()
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as handle:
        handle.write(prompt)
        path = handle.name
    try:
        _run_xdotool("type", "--clearmodifiers", "--delay", "2", "--file", path, timeout=180)
        _run_xdotool("key", "--clearmodifiers", "Return", timeout=10)
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass


def _format_prompt(sender: str, channel: str, message: str, event_id: str) -> str:
    compact_message = re.sub(r"\s+", " ", message).strip()
    return (
        f"NATS delivery into visible Echo CLI. "
        f"Subject: {NS}.{AGENT}.{channel}. "
        f"Sender: {sender}. "
        f"Event ID: {event_id}. "
        f"Message: {compact_message}. "
        "Answer in this visible CLI session. Give a substantial answer when the "
        "message asks for depth. Mention that this came through NATS."
    )


def _active_cli_session_state() -> tuple[str, int, int]:
    db_path = PROFILE_ROOT / "state.db"
    with sqlite3.connect(str(db_path), timeout=10) as conn:
        row = conn.execute(
            """
            SELECT id, message_count
            FROM sessions
            WHERE source = 'cli' AND ended_at IS NULL
            ORDER BY message_count DESC, started_at DESC
            LIMIT 1
            """
        ).fetchone()
        if not row:
            return "", 0, 0
        message_id = conn.execute(
            "SELECT COALESCE(MAX(id), 0) FROM messages WHERE session_id = ?",
            (str(row[0]),),
        ).fetchone()[0]
    return str(row[0]), int(row[1] or 0), int(message_id or 0)


def _active_cli_session_count() -> tuple[str, int]:
    session_id, count, _message_id = _active_cli_session_state()
    return session_id, count


def _assistant_reply_after(session_id: str, after_message_id: int) -> tuple[int, str]:
    db_path = PROFILE_ROOT / "state.db"
    with sqlite3.connect(str(db_path), timeout=10) as conn:
        row = conn.execute(
            """
            SELECT id, content
            FROM messages
            WHERE session_id = ?
              AND id > ?
              AND role = 'assistant'
              AND COALESCE(content, '') != ''
            ORDER BY id DESC
            LIMIT 1
            """,
            (session_id, after_message_id),
        ).fetchone()
    if not row:
        return 0, ""
    return int(row[0]), str(row[1] or "")


async def _wait_for_assistant_reply_after(
    session_id: str,
    after_message_id: int,
) -> tuple[int, str]:
    deadline = asyncio.get_running_loop().time() + REPLY_CAPTURE_TIMEOUT
    while asyncio.get_running_loop().time() < deadline:
        assistant_message_id, assistant_text = _assistant_reply_after(session_id, after_message_id)
        if assistant_text:
            return assistant_message_id, assistant_text
        await asyncio.sleep(IDLE_POLL_SECONDS)
    return 0, ""


async def _wait_for_cli_turn(before_session: str, before_count: int) -> tuple[str, int]:
    loop = asyncio.get_running_loop()
    deadline = loop.time() + DELIVERY_TIMEOUT
    last_seen: tuple[str, int] | None = None
    while loop.time() < deadline:
        session_id, count = _active_cli_session_count()
        current = (session_id, count)
        if current != last_seen:
            logger.info(f"Echo CLI session progress: {session_id} messages={count}")
            last_seen = current
        if session_id == before_session and count >= before_count + 2:
            return current
        if session_id != before_session and count >= 2:
            return current
        await asyncio.sleep(IDLE_POLL_SECONDS)
    raise TimeoutError(
        f"Echo CLI session did not advance from {before_session}:{before_count} "
        f"within {DELIVERY_TIMEOUT}s"
    )


async def _publish_trace(nc, event: str, **fields: object) -> None:
    payload = {
        "from": "echo-tui-nats-bridge",
        "agent": AGENT,
        "event": event,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **fields,
    }
    logger.info(
        "trace event={} id={} channel={} queue_depth={} elapsed_seconds={}".format(
            event,
            fields.get("id", ""),
            fields.get("channel", ""),
            fields.get("queue_depth", ""),
            fields.get("elapsed_seconds", ""),
        )
    )
    await nc.publish(f"{NS}.logs.{AGENT}", json.dumps(payload).encode())


async def _reply(nc, reply_to: object, payload: dict[str, object]) -> None:
    if not reply_to:
        return
    await nc.publish(str(reply_to), json.dumps(payload).encode())


async def _reply_final(nc, reply_to: object) -> None:
    if not reply_to:
        return
    await nc.publish(str(reply_to), json.dumps({"chunk": "", "final": True}).encode())


async def _enqueue_work(nc, work: BridgeWork) -> bool:
    async with _queue_guard:
        queued = _processing or not _work_queue.empty()
        if queued and _work_queue.qsize() >= MAX_QUEUE_DEPTH:
            await _publish_trace(
                nc,
                "busy_rejected",
                channel=work.subject,
                sender=work.sender,
                reply_to=bool(work.reply_to),
                id=work.event_id,
                queue_depth=_work_queue.qsize(),
                max_queue_depth=MAX_QUEUE_DEPTH,
            )
            await _reply(
                nc,
                work.reply_to,
                {
                    "chunk": (
                        "Echo visible bridge is busy and its bounded queue is full. "
                        "Retry after the active turn completes."
                    ),
                    "final": False,
                    "error": "echo_tui_busy",
                },
            )
            await _reply_final(nc, work.reply_to)
            return True
        if queued:
            await _publish_trace(
                nc,
                "queued",
                channel=work.subject,
                sender=work.sender,
                reply_to=bool(work.reply_to),
                id=work.event_id,
                queue_depth=_work_queue.qsize() + 1,
            )
        _work_queue.put_nowait(work)
        return False


async def _handle_message(nc, channel: str, msg) -> None:
    try:
        env = json.loads(msg.data.decode())
    except Exception as exc:
        logger.warning(f"non-JSON payload on {msg.subject}: {exc}")
        return

    sender = str(env.get("from") or "?")
    if sender == AGENT:
        return
    message = str(env.get("message") or "").strip()
    if not message:
        return
    reply_to = env.get("reply_to")
    event_id = str(env.get("id") or f"{sender}:{env.get('timestamp')}:{message[:40]}")

    await _publish_trace(
        nc,
        "inbound",
        channel=msg.subject,
        sender=sender,
        message=message,
        reply_to=bool(reply_to),
        id=event_id,
    )
    work = BridgeWork(
        subject=msg.subject,
        channel=channel,
        sender=sender,
        message=message,
        reply_to=reply_to,
        event_id=event_id,
    )
    await _enqueue_work(nc, work)


async def _process_work(nc, work: BridgeWork) -> None:
    started = time.monotonic()
    try:
        await _publish_trace(
            nc,
            "typed",
            channel=work.subject,
            sender=work.sender,
            message=work.message,
            reply_to=bool(work.reply_to),
            id=work.event_id,
        )
        prompt = _format_prompt(work.sender, work.channel, work.message, work.event_id)
        logger.info(f"typing NATS message into Echo TUI from={work.sender} channel={work.channel}")
        await _wait_for_idle_window()
        before_session, before_count, before_message_id = _active_cli_session_state()
        _clear_input()
        _type_prompt(prompt)
        after_session, after_count = await _wait_for_cli_turn(before_session, before_count)
        assistant_after_id = before_message_id if after_session == before_session else 0
        assistant_message_id, assistant_text = await _wait_for_assistant_reply_after(
            after_session,
            assistant_after_id,
        )
        if not assistant_text:
            raise RuntimeError(
                "Echo CLI completed the visible turn but no assistant reply was found "
                f"after message id {assistant_after_id}"
            )
        await _publish_trace(
            nc,
            "reply_captured",
            channel=work.subject,
            sender=work.sender,
            reply_to=bool(work.reply_to),
            id=work.event_id,
            session_id=after_session,
            assistant_message_id=assistant_message_id,
            response_chars=len(assistant_text),
        )
        await _publish_trace(
            nc,
            "completed",
            channel=work.subject,
            sender=work.sender,
            message=work.message,
            reply_to=bool(work.reply_to),
            id=work.event_id,
            session_id=after_session,
            message_count=after_count,
            assistant_message_id=assistant_message_id,
            response_chars=len(assistant_text),
            elapsed_seconds=round(time.monotonic() - started, 3),
        )
        await _reply(nc, work.reply_to, {
            "chunk": assistant_text,
            "final": False,
            "session_id": after_session,
            "assistant_message_id": assistant_message_id,
        })
        await _reply_final(nc, work.reply_to)
    except Exception as exc:
        logger.exception(f"Echo visible bridge failed for event {work.event_id}: {exc}")
        await _publish_trace(
            nc,
            "timeout" if isinstance(exc, TimeoutError) else "error",
            channel=work.subject,
            sender=work.sender,
            reply_to=bool(work.reply_to),
            id=work.event_id,
            error=str(exc),
            elapsed_seconds=round(time.monotonic() - started, 3),
        )
        await _reply(nc, work.reply_to, {
            "chunk": f"Echo visible bridge failed: {exc}",
            "final": False,
            "error": "echo_tui_timeout" if isinstance(exc, TimeoutError) else "echo_tui_error",
        })
        await _reply_final(nc, work.reply_to)


async def _work_loop(nc) -> None:
    global _processing
    while True:
        work = await _work_queue.get()
        async with _queue_guard:
            _processing = True
        try:
            async with _delivery_lock:
                await _process_work(nc, work)
        finally:
            async with _queue_guard:
                _processing = False
            _work_queue.task_done()


async def main() -> None:
    nats_url = _load_nats_url()
    logger.info(f"echo-tui-nats-bridge connecting -> {nats_url.split('@')[-1]}")
    nc = await nats.connect(nats_url, name="echo-tui-nats-bridge")
    worker = asyncio.create_task(_work_loop(nc))

    async def on_direct(msg) -> None:
        await _handle_message(nc, "direct", msg)

    async def on_meet(msg) -> None:
        await _handle_message(nc, "meet", msg)

    await nc.subscribe(f"{NS}.{AGENT}.direct", cb=on_direct)
    await nc.subscribe(f"{NS}.{AGENT}.meet", cb=on_meet)

    async def on_ping(msg) -> None:
        if msg.reply:
            await nc.publish(msg.reply, f"pong:{AGENT}:tui".encode())

    await nc.subscribe(f"{NS}.{AGENT}.ping", cb=on_ping)
    logger.info(f"ready for {NS}.{AGENT}.direct/.meet/.ping -> {WINDOW_NAME}")
    try:
        await asyncio.Future()
    except (KeyboardInterrupt, asyncio.CancelledError):
        pass
    finally:
        worker.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await worker
        await nc.drain()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)
