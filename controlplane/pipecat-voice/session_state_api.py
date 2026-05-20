"""Read-only session-state aggregation for the pipecat gateway."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def now_utc() -> str:
    """Return the current UTC timestamp in ISO-8601 format."""
    return datetime.now(timezone.utc).isoformat()


def read_json_snapshot(path: Path) -> dict[str, Any] | None:
    """Read a JSON snapshot, returning ``None`` when the file is absent or invalid."""
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def snapshot_meta(path: Path) -> dict[str, Any]:
    """Return existence and mtime metadata for a runtime snapshot path."""
    if not path.exists():
        return {"path": str(path), "exists": False, "updated_at": None}
    stat = path.stat()
    return {
        "path": str(path),
        "exists": True,
        "updated_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
    }


def summarize_agents(route_state: dict[str, Any] | None) -> list[dict[str, Any]]:
    """Flatten route-state agents into a dashboard-friendly summary list."""
    agents = route_state.get("agents", []) if route_state else []
    if not isinstance(agents, list):
        return []

    summaries: list[dict[str, Any]] = []
    for item in agents:
        if not isinstance(item, dict):
            continue
        service = item.get("service") if isinstance(item.get("service"), dict) else {}
        window = item.get("window") if isinstance(item.get("window"), dict) else {}
        latest_session = item.get("latest_open_cli_session")
        latest_proof = item.get("latest_proof")
        summaries.append(
            {
                "name": item.get("name"),
                "subject": item.get("subject"),
                "route_mode": item.get("route_mode"),
                "route_health": item.get("route_health"),
                "route_reason": item.get("route_reason"),
                "bridge_owner": service.get("unit"),
                "bridge_active": service.get("active"),
                "bridge_enabled": service.get("enabled"),
                "window_name": window.get("name"),
                "window_present": bool(window.get("present")),
                "fallback_enabled": bool(item.get("fallback_enabled")),
                "latest_session_id": (
                    latest_session.get("id") if isinstance(latest_session, dict) else None
                ),
                "latest_session_message_count": (
                    latest_session.get("message_count")
                    if isinstance(latest_session, dict)
                    else None
                ),
                "latest_proof_timestamp": item.get("latest_proof_timestamp"),
                "latest_reply_mode": item.get("latest_reply_mode"),
                "latest_proof_event_id": (
                    latest_proof.get("event_id") if isinstance(latest_proof, dict) else None
                ),
                "latest_proof_reply_captured": (
                    latest_proof.get("reply_captured")
                    if isinstance(latest_proof, dict)
                    else None
                ),
            }
        )
    return summaries


def count_by_key(items: list[dict[str, Any]], key: str) -> dict[str, int]:
    """Count string-ish values in a summary list."""
    counts: dict[str, int] = {}
    for item in items:
        value = str(item.get(key) or "unknown")
        counts[value] = counts.get(value, 0) + 1
    return counts


def build_session_state(root: Path) -> dict[str, Any]:
    """Build one read-only API payload from runtime snapshots.

    Parameters:
        root: Repository root for the pipecat-voice service.

    Returns:
        A JSON-serializable payload containing agent route/session summaries and
        raw snapshot metadata. The function performs no model calls, NATS
        traffic, service restarts, or writes.
    """
    runtime = root / "ops" / "runtime"
    route_path = runtime / "crew_route_state.json"
    heartbeat_path = runtime / "crew_heartbeat.json"
    health_path = runtime / "pipecat_health.json"
    watchdog_path = runtime / "crew_watchdog.json"

    route_state = read_json_snapshot(route_path)
    heartbeat = read_json_snapshot(heartbeat_path)
    pipecat_health = read_json_snapshot(health_path)
    watchdog = read_json_snapshot(watchdog_path)
    agents = summarize_agents(route_state)

    return {
        "generated_at": now_utc(),
        "agents": agents,
        "summary": {
            "agent_count": len(agents),
            "route_modes": count_by_key(agents, "route_mode"),
            "route_health": count_by_key(agents, "route_health"),
        },
        "operator_inbox": (route_state or {}).get("operator_inbox"),
        "snapshots": {
            "route_state": snapshot_meta(route_path),
            "heartbeat": snapshot_meta(heartbeat_path),
            "pipecat_health": snapshot_meta(health_path),
            "watchdog": snapshot_meta(watchdog_path),
        },
        "raw": {
            "route_state": route_state,
            "heartbeat": heartbeat,
            "pipecat_health": pipecat_health,
            "watchdog": watchdog,
        },
    }
