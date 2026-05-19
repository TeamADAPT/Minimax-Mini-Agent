from __future__ import annotations

import asyncio
import time
from pathlib import Path

import nats

from ops_loop_common import ensure_runtime_dir, load_nats_url, now_utc, write_json

AGENTS = ("echo", "skipper", "testova", "latch")
OUTPUT_PATH = Path(ensure_runtime_dir()) / "crew_heartbeat.json"


async def ping_agent(nc: nats.NATS, name: str) -> dict[str, object]:
    subject = f"nova.{name}.ping"
    started = time.perf_counter()
    try:
        message = await nc.request(subject, b"ping", timeout=5)
        latency_ms = round((time.perf_counter() - started) * 1000, 2)
        response = message.data.decode("utf-8", errors="replace").strip()
        return {
            "name": name,
            "subject": subject,
            "ok": True,
            "latency_ms": latency_ms,
            "response": response,
        }
    except Exception as exc:
        latency_ms = round((time.perf_counter() - started) * 1000, 2)
        return {
            "name": name,
            "subject": subject,
            "ok": False,
            "latency_ms": latency_ms,
            "error": str(exc),
        }


async def main() -> None:
    nc = await nats.connect(load_nats_url())
    try:
        results = await asyncio.gather(*(ping_agent(nc, name) for name in AGENTS))
    finally:
        await nc.drain()

    live = sum(1 for item in results if item["ok"])
    payload = {
        "generated_at": now_utc(),
        "summary": {
            "live": live,
            "total": len(results),
            "offline": len(results) - live,
        },
        "agents": results,
    }
    write_json(OUTPUT_PATH, payload)


if __name__ == "__main__":
    asyncio.run(main())
