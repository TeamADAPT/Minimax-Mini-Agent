"""Vox auto-turn trigger.

Subscribes to ``nova.vox.direct`` / ``nova.vox.meet`` and acts as a fallback
when the interactive CC (vox) session fails to reply within the debounce
window.

Mechanism
---------

1. Subscribe to ``nova.vox.direct`` (incoming voice messages).
2. When an inbound arrives with a ``reply_to`` inbox, subscribe to that inbox
   to detect whether the interactive CC session already replied via
   ``nats_reply``.
3. Wait ``VOX_DEBOUNCE_MS``. If a reply appears on the inbox, CC self-turned —
   do nothing.
4. Otherwise, spawn a fresh headless ``claude --print`` with ``reply_to`` and
   the message text embedded directly in the prompt. The nats-channel MCP is
   registered in user-scope settings.json so ``mcp__nats-channel__nats_reply``
   is available to every CC session without ``--dangerously-load-development-channels``.

No tmux, no ``--resume`` (avoids the "busy" session lock). Each fallback is a
fully independent one-shot CC invocation.

Configuration via env (with defaults):

* ``VOX_DEBOUNCE_MS``       — reply-wait window before forcing a turn (``4000``).
* ``VOX_CLAUDE_TIMEOUT_S``  — headless CC subprocess timeout seconds (``120``).
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

_PROMPT_TEMPLATE = (
    "Use ToolSearch(query='select:mcp__nats-channel__nats_reply') to load the tool schema. "
    "Then call mcp__nats-channel__nats_reply with reply_to={reply_to!r} and a 1-2 sentence "
    "voice-friendly reply (no markdown, no bullet points) to this message: {message!r}. "
    "Make exactly these two tool calls then stop."
)


def _load_nats_url() -> str:
    if v := os.environ.get("NATS_URL"):
        return v
    txt = Path("/adapt/secrets/db.env").read_text()
    return re.search(r'^NATS_URL\s*=\s*"?([^"\n]+)"?', txt, re.M).group(1).strip().strip('"')


async def _claude_inject(reply_to: str, message: str) -> None:
    """Spawn a fresh headless CC that calls nats_reply.

    Uses ``--print -p`` (no ``--resume``) so it is never blocked by a "busy"
    interactive session. The nats-channel MCP is loaded from user-scope
    settings.json automatically.
    """
    prompt = _PROMPT_TEMPLATE.format(reply_to=reply_to, message=message)
    cmd = [
        "claude",
        "--print",
        "--dangerously-skip-permissions",
        "-p", prompt,
    ]
    logger.info(f"spawning headless CC (fresh session, reply_to={reply_to!r})")
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=CLAUDE_CWD,
        )
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(),
            timeout=float(os.environ.get("VOX_CLAUDE_TIMEOUT_S", "120")),
        )
        if proc.returncode != 0:
            logger.error(
                f"headless CC rc={proc.returncode} "
                f"stderr={stderr[:400].decode(errors='replace')!r} "
                f"stdout={stdout[:400].decode(errors='replace')!r}"
            )
        else:
            logger.info(f"headless CC done (rc={proc.returncode})")
    except asyncio.TimeoutError:
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

        # Watch the reply_to inbox to detect whether interactive CC self-replies.
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

            logger.info("debounce expired without reply; spawning headless CC")
            await _claude_inject(reply_to, message)
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
