"""Smoke test for Echo visible TUI NATS reply capture."""

from __future__ import annotations

import asyncio
import json
import os
import re
import time
import uuid

import nats

SUBJECT = os.environ.get("ECHO_TUI_REPLY_SMOKE_SUBJECT", "nova.echo.direct")
TIMEOUT_SECONDS = float(os.environ.get("ECHO_TUI_REPLY_SMOKE_TIMEOUT", "420"))


def _load_nats_url() -> str:
    if url := os.environ.get("NATS_URL"):
        return url
    with open("/adapt/secrets/db.env", encoding="utf-8") as handle:
        text = handle.read()
    match = re.search(r'^NATS_URL\s*=\s*"?([^"\n]+)"?', text, re.M)
    if not match:
        raise RuntimeError("NATS_URL not found")
    return match.group(1).strip().strip('"')


async def _request(nc, label: str, message: str, required_phrase: str) -> dict[str, object]:
    inbox = nc.new_inbox()
    chunks: list[str] = []
    payloads: list[dict[str, object]] = []
    done = asyncio.Event()
    event_id = f"reply-{label}-{uuid.uuid4().hex[:10]}"

    async def cb(msg) -> None:
        payload = json.loads(msg.data.decode())
        payloads.append(payload)
        if payload.get("chunk"):
            chunks.append(str(payload["chunk"]))
        if payload.get("final") or payload.get("error"):
            done.set()

    sub = await nc.subscribe(inbox, cb=cb)
    await nc.publish(
        SUBJECT,
        json.dumps(
            {
                "id": event_id,
                "from": "latch-reply-smoke",
                "message": message,
                "reply_to": inbox,
                "timestamp": time.time(),
            }
        ).encode(),
    )
    await nc.flush()
    await asyncio.wait_for(done.wait(), timeout=TIMEOUT_SECONDS)
    await sub.unsubscribe()
    reply = "".join(chunks).strip()
    error = next((p.get("error") for p in payloads if p.get("error")), None)
    return {
        "event_id": event_id,
        "reply": reply,
        "reply_chars": len(reply),
        "required_phrase_present": required_phrase in reply,
        "payload_count": len(payloads),
        "error": error,
    }


async def main() -> None:
    nc = await nats.connect(_load_nats_url(), name="echo-tui-reply-capture-smoke")
    short_phrase = "REPLY SHORT DONE"
    long_phrase = "REPLY LONG DONE"
    short = (
        "Reply capture short proof. Answer with one sentence and include the exact "
        f"phrase {short_phrase}."
    )
    long = (
        "Reply capture long proof. Give a substantial answer of at least six "
        "sentences about why serialized NATS delivery matters for a visible CLI "
        f"agent. Include the exact phrase {long_phrase}."
    )
    try:
        results = [
            await _request(nc, "short", short, short_phrase),
            await _request(nc, "long", long, long_phrase),
        ]
        print(json.dumps({"subject": SUBJECT, "results": results}, indent=2))
        if any(result.get("error") or not result["required_phrase_present"] for result in results):
            raise SystemExit(1)
        if int(results[1]["reply_chars"]) < 300:
            raise SystemExit("long reply was shorter than expected")
    finally:
        await nc.drain()


if __name__ == "__main__":
    asyncio.run(main())
