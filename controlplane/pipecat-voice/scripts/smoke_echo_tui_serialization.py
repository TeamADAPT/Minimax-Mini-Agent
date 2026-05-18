"""Smoke test for Echo visible TUI NATS serialization.

The helper sends two direct Echo messages back-to-back and waits for both bridge
responses. It does not print NATS credentials.
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import time
import uuid

import nats

SUBJECT = os.environ.get("ECHO_TUI_SMOKE_SUBJECT", "nova.echo.direct")
TIMEOUT_SECONDS = float(os.environ.get("ECHO_TUI_SMOKE_TIMEOUT", "420"))


def _load_nats_url() -> str:
    if url := os.environ.get("NATS_URL"):
        return url
    with open("/adapt/secrets/db.env", encoding="utf-8") as handle:
        text = handle.read()
    match = re.search(r'^NATS_URL\s*=\s*"?([^"\n]+)"?', text, re.M)
    if not match:
        raise RuntimeError("NATS_URL not found")
    return match.group(1).strip().strip('"')


async def _request(nc, label: str, message: str) -> dict[str, object]:
    inbox = nc.new_inbox()
    chunks: list[str] = []
    payloads: list[dict[str, object]] = []
    done = asyncio.Event()
    event_id = f"serial-{label}-{uuid.uuid4().hex[:10]}"

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
                "from": "latch-smoke",
                "message": message,
                "reply_to": inbox,
                "timestamp": time.time(),
            }
        ).encode(),
    )
    await nc.flush()
    await asyncio.wait_for(done.wait(), timeout=TIMEOUT_SECONDS)
    await sub.unsubscribe()
    return {
        "event_id": event_id,
        "reply": "".join(chunks).strip(),
        "payload_count": len(payloads),
        "error": next((p.get("error") for p in payloads if p.get("error")), None),
    }


async def main() -> None:
    nc = await nats.connect(_load_nats_url(), name="echo-tui-serialization-smoke")
    first = (
        "Serialization smoke first turn. Answer in three numbered points and include "
        "the exact phrase SERIAL FIRST DONE."
    )
    second = (
        "Serialization smoke second turn. Answer in two numbered points and include "
        "the exact phrase SERIAL SECOND DONE."
    )
    try:
        results = await asyncio.gather(
            _request(nc, "first", first),
            _request(nc, "second", second),
        )
        print(json.dumps({"subject": SUBJECT, "results": results}, indent=2))
        if any(result.get("error") for result in results):
            raise SystemExit(1)
    finally:
        await nc.drain()


if __name__ == "__main__":
    asyncio.run(main())
