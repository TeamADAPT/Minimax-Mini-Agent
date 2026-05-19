"""Latch NATS inbox for nova-initiated messages.

This service gives other novas a stable target when they need to initiate a
message to the current Codex/Latch operator. It intentionally does not attempt
to call a model. It records inbound messages, emits an ACK when requested, and
leaves the operator-facing reply in a durable JSONL inbox.
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import signal
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import nats

NS = os.environ.get("SUBJECT_NS", "nova")
AGENT = os.environ.get("LATCH_NATS_AGENT", "latch")
ROOT = Path(
    os.environ.get(
        "LATCH_INBOX_ROOT",
        "/adapt/platform/novaops/controlplane/pipecat-voice/ops",
    )
)
INBOX_PATH = Path(os.environ.get("LATCH_INBOX_PATH", ROOT / "latch_inbox.jsonl"))


def load_nats_url() -> str:
    """Load the NATS URL without printing secret-bearing configuration."""
    if url := os.environ.get("NATS_URL"):
        return url
    text = Path("/adapt/secrets/db.env").read_text(encoding="utf-8")
    match = re.search(r'^NATS_URL\s*=\s*"?([^"\n]+)"?', text, re.M)
    if not match:
        raise RuntimeError("NATS_URL not found")
    return match.group(1).strip().strip('"')


def decode_payload(data: bytes) -> dict[str, Any]:
    """Decode a nova envelope, falling back to a text message wrapper."""
    text = data.decode("utf-8", errors="replace")
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return {"message": text}
    if isinstance(payload, dict):
        return payload
    return {"message": payload}


def inbox_record(subject: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Build the durable inbox record stored for operator polling."""
    return {
        "received_at": datetime.now(timezone.utc).isoformat(),
        "subject": subject,
        "id": str(payload.get("id") or ""),
        "from": str(payload.get("from") or payload.get("sender") or "unknown"),
        "message": payload.get("message", payload.get("content", "")),
        "raw": payload,
    }


def append_record(record: dict[str, Any]) -> None:
    """Append one JSONL inbox record and keep file permissions local-user only."""
    INBOX_PATH.parent.mkdir(parents=True, exist_ok=True)
    with INBOX_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=True, sort_keys=True))
        handle.write("\n")
    os.chmod(INBOX_PATH, 0o600)


async def reply_ack(nc: nats.NATS, reply_to: object, record: dict[str, Any]) -> None:
    """Publish an ACK to reply_to using the existing chunk/final convention."""
    if not reply_to:
        return
    ack = {
        "chunk": (
            f"ACK latch inbox received id={record['id']} "
            f"from={record['from']} subject={record['subject']}"
        ),
        "final": True,
        "id": record["id"],
        "from": "latch-inbox",
        "timestamp": time.time(),
    }
    await nc.publish(str(reply_to), json.dumps(ack).encode())


async def handle_message(nc: nats.NATS, msg: nats.aio.msg.Msg) -> None:
    """Persist one inbound message and optionally acknowledge it."""
    if msg.subject == f"{NS}.{AGENT}.ping":
        await msg.respond(f"pong:{AGENT}:inbox".encode())
        return

    payload = decode_payload(msg.data)
    record = inbox_record(msg.subject, payload)
    append_record(record)
    await nc.publish(
        f"{NS}.logs.{AGENT}",
        json.dumps(
            {
                "from": "latch-inbox",
                "event": "received",
                "id": record["id"],
                "sender": record["from"],
                "subject": record["subject"],
                "timestamp": record["received_at"],
            },
            sort_keys=True,
        ).encode(),
    )
    await reply_ack(nc, payload.get("reply_to") or msg.reply, record)
    print(
        f"{record['received_at']} received {record['subject']} "
        f"id={record['id']} from={record['from']}",
        flush=True,
    )


async def main() -> None:
    """Run the inbox subscriber until systemd or the operator stops it."""
    nc = await nats.connect(load_nats_url())
    done = asyncio.Event()

    def stop() -> None:
        done.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop)

    subjects = [
        f"{NS}.{AGENT}.direct",
        f"{NS}.{AGENT}.meet",
        f"{NS}.{AGENT}.ping",
    ]
    async def callback(msg: nats.aio.msg.Msg) -> None:
        await handle_message(nc, msg)

    for subject in subjects:
        await nc.subscribe(subject, cb=callback)

    print(f"latch inbox listening on {', '.join(subjects)}", flush=True)
    await done.wait()
    await nc.drain()


if __name__ == "__main__":
    asyncio.run(main())
