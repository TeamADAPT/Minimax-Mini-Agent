"""Vox auto-turn trigger.

Subscribes to ``nova.vox.direct`` / ``nova.vox.meet`` and acts as a fallback
when the interactive CC (vox) session fails to reply within the debounce
window.

Mechanism
---------

1. Subscribe to ``nova.vox.direct`` (incoming voice messages).
2. When an inbound arrives with a ``reply_to`` inbox, subscribe to that inbox
   to detect whether the interactive CC session already replied.
3. Wait ``VOX_DEBOUNCE_MS``. If a reply appears on the inbox, CC self-turned —
   do nothing.
4. Otherwise, spawn ``claude --print -p "<voice prompt>"`` and capture stdout.
   Publish the captured text directly to ``reply_to`` via NATS — no MCP, no
   tool calls.

No tmux, no ``--resume`` (avoids the "busy" session lock). Each fallback is a
fully independent one-shot CC invocation.

Configuration via env (with defaults):

* ``VOX_DEBOUNCE_MS``       — reply-wait window before forcing a turn (``4000``).
* ``VOX_CLAUDE_TIMEOUT_S``  — headless CC subprocess timeout seconds (``60``).
* ``VOX_CLAUDE_CWD``        — working dir for headless CC
                              (``/adapt/platform/novaops/controlplane/pipecat``).
* ``SUBJECT_NS``            — NATS namespace prefix (``nova``).
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import sys
from pathlib import Path

import nats
from loguru import logger

NS = os.environ.get("SUBJECT_NS", "nova")
SELF = "vox"
DEBOUNCE_MS = int(os.environ.get("VOX_DEBOUNCE_MS", "4000"))
CLAUDE_CWD = os.environ.get(
    "VOX_CLAUDE_CWD",
    "/adapt/platform/novaops/controlplane/pipecat",
)
# Minimal CC config dir with no MCP servers — eliminates ~15s of MCP init per invocation.
CLAUDE_CONFIG_DIR = os.environ.get("VOX_CLAUDE_CONFIG_DIR", "/home/x/.claude-headless")

_PROMPT_TEMPLATE = (
    "You are Vox, a voice assistant. Reply to the following message in 1-2 short spoken "
    "sentences. No markdown, no bullet points, no emoji, no lists. Respond with only the "
    "reply text — nothing else.\n\nMessage: {message}"
)


def _load_nats_url() -> str:
    if v := os.environ.get("NATS_URL"):
        return v
    txt = Path("/adapt/secrets/db.env").read_text()
    return re.search(r'^NATS_URL\s*=\s*"?([^"\n]+)"?', txt, re.M).group(1).strip().strip('"')


async def _claude_reply(nc: nats.aio.client.Client, reply_to: str, message: str) -> None:
    """Spawn headless CC, capture stdout, publish reply directly to NATS."""
    prompt = _PROMPT_TEMPLATE.format(message=message)
    cmd = [
        "claude",
        "--print",
        "--dangerously-skip-permissions",
        "-p", prompt,
    ]
    env = {**os.environ, "CLAUDE_CONFIG_DIR": CLAUDE_CONFIG_DIR}
    logger.info(f"spawning headless CC (reply_to={reply_to!r}, config={CLAUDE_CONFIG_DIR})")
    proc: asyncio.subprocess.Process | None = None
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=CLAUDE_CWD,
            env=env,
        )
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(),
            timeout=float(os.environ.get("VOX_CLAUDE_TIMEOUT_S", "60")),
        )
        if proc.returncode != 0:
            logger.error(
                f"headless CC rc={proc.returncode} "
                f"stderr={stderr[:400].decode(errors='replace')!r}"
            )
            return
        reply = stdout.decode(errors="replace").strip()
        if not reply:
            logger.warning("headless CC produced empty output; skipping publish")
            return
        logger.info(f"headless CC reply: {reply[:80]!r}")
        payload = json.dumps({"chunk": reply, "final": True}).encode()
        await nc.publish(reply_to, payload)
        logger.info(f"published reply -> {reply_to}")
    except asyncio.TimeoutError:
        if proc is not None:
            proc.kill()
        logger.warning("headless CC timed out; killed")
    except Exception as exc:
        logger.error(f"headless CC failed: {exc}")


async def main() -> None:
    """Run the trigger daemon until interrupted."""
    nats_url = _load_nats_url()
    logger.info(
        f"vox-trigger connecting -> {nats_url.split('@')[-1]} "
        f"(debounce={DEBOUNCE_MS}ms)"
    )
    nc = await nats.connect(nats_url, name="vox-turn-trigger")

    async def on_inbound(msg) -> None:
        try:
            payload = json.loads(msg.data.decode())
        except Exception:
            return
        if payload.get("from") == SELF:
            return  # echo filter

        sender = payload.get("from", "?")
        message: str = payload.get("message") or ""
        reply_to: str = payload.get("reply_to", "")
        logger.info(f"<- inbound from {sender}: {message[:60]!r} (reply_to={reply_to!r})")

        if not reply_to:
            logger.debug("no reply_to; skipping fallback")
            return

        replied = asyncio.Event()

        async def on_reply(_m):
            replied.set()

        sub = await nc.subscribe(reply_to, cb=on_reply)

        try:
            try:
                await asyncio.wait_for(replied.wait(), timeout=DEBOUNCE_MS / 1000.0)
                logger.info("CC self-replied within debounce; no fallback needed")
                return
            except asyncio.TimeoutError:
                pass

            logger.info("debounce expired; spawning headless CC fallback")
            await _claude_reply(nc, reply_to, message)
        finally:
            await sub.unsubscribe()

    await nc.subscribe(f"{NS}.{SELF}.direct", cb=on_inbound)
    await nc.subscribe(f"{NS}.{SELF}.meet", cb=on_inbound)
    logger.info("vox-trigger ready")
    try:
        await asyncio.Future()
    except (KeyboardInterrupt, asyncio.CancelledError):
        pass
    finally:
        await nc.drain()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)
