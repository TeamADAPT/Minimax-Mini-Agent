from __future__ import annotations

import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ops_loop_common import (
    ensure_runtime_dir,
    latest_open_cli_session,
    now_utc,
    service_env_flag,
    systemctl_state,
    window_present,
    write_json,
)

OUTPUT_PATH = Path(ensure_runtime_dir()) / "crew_route_state.json"
NATS_EVENT_RE = re.compile(r"\bEvent ID:\s*([A-Za-z0-9_.:-]+)")

AGENTS = (
    {
        "name": "echo",
        "unit": "echo-tui-nats-bridge.service",
        "window": "Echo CLI",
        "profile_root": Path("/home/x/.hermes/profiles/echo"),
    },
    {
        "name": "skipper",
        "unit": "skipper-tui-nats-bridge.service",
        "window": "Skipper CLI",
        "profile_root": Path("/home/x/.hermes/profiles/skipper"),
    },
    {
        "name": "testova",
        "unit": "testova-tui-nats-bridge.service",
        "window": "Testova CLI",
        "profile_root": Path("/home/x/.hermes/profiles/testova"),
    },
)


def unix_to_iso(timestamp: float | int | None) -> str | None:
    if timestamp is None:
        return None
    return datetime.fromtimestamp(float(timestamp), tz=timezone.utc).isoformat()


def env_bool(unit: str, key: str) -> bool:
    return str(service_env_flag(unit, key) or "").strip().lower() in {"1", "true", "yes", "on"}


def env_int(unit: str, key: str) -> int | None:
    value = service_env_flag(unit, key)
    if value is None:
        return None
    try:
        return int(float(value))
    except ValueError:
        return None


def event_id_from_content(content: str) -> str | None:
    match = NATS_EVENT_RE.search(content)
    if not match:
        return None
    return match.group(1).rstrip(".")


def classify_route(
    *,
    service_active: str,
    window_found: bool,
    fallback_enabled: bool,
) -> tuple[str, str, str]:
    if service_active != "active":
        return "bridge-down", "down", "bridge service is not active"
    if window_found:
        return "visible-ready", "healthy", "bridge active and visible CLI window found"
    if fallback_enabled:
        return "fallback-active", "degraded", "bridge active but visible CLI is missing; CLI fallback is enabled"
    return "visible-missing", "degraded", "bridge active but visible CLI is missing and fallback is disabled"


def latest_nats_proof(profile_root: Path, subject: str) -> dict[str, Any] | None:
    db_path = profile_root / "state.db"
    if not db_path.exists():
        return None
    pattern = f"%Subject: {subject}.%"
    with sqlite3.connect(str(db_path), timeout=10) as conn:
        conn.row_factory = sqlite3.Row
        user_row = conn.execute(
            """
            SELECT id, session_id, content, timestamp
            FROM messages
            WHERE role = 'user'
              AND COALESCE(content, '') LIKE ?
            ORDER BY timestamp DESC, id DESC
            LIMIT 1
            """,
            (pattern,),
        ).fetchone()
        if not user_row:
            return None
        session_row = conn.execute(
            "SELECT source FROM sessions WHERE id = ?",
            (str(user_row["session_id"]),),
        ).fetchone()
        assistant_row = conn.execute(
            """
            SELECT id, content, timestamp
            FROM messages
            WHERE session_id = ?
              AND id > ?
              AND role = 'assistant'
              AND COALESCE(content, '') != ''
            ORDER BY timestamp ASC, id ASC
            LIMIT 1
            """,
            (str(user_row["session_id"]), int(user_row["id"])),
        ).fetchone()

    content = str(user_row["content"] or "")
    source = str(session_row["source"] if session_row else "")
    reply_mode = "none"
    if assistant_row:
        reply_mode = "visible-cli" if source == "cli" else source or "unknown"
    return {
        "event_id": event_id_from_content(content),
        "session_id": str(user_row["session_id"]),
        "session_source": source or None,
        "user_message_id": int(user_row["id"]),
        "timestamp": unix_to_iso(user_row["timestamp"]),
        "assistant_message_id": int(assistant_row["id"]) if assistant_row else None,
        "assistant_timestamp": unix_to_iso(assistant_row["timestamp"]) if assistant_row else None,
        "reply_mode": reply_mode,
        "reply_captured": bool(assistant_row),
    }


def main() -> None:
    agents: list[dict[str, object]] = []
    for agent in AGENTS:
        unit = str(agent["unit"])
        window_name = str(agent["window"])
        profile_root = Path(agent["profile_root"])
        subject = f"nova.{agent['name']}.direct"
        service = {"unit": unit, **systemctl_state(unit, user=True)}
        window_found = window_present(window_name)
        fallback_enabled = env_bool(unit, "ECHO_TUI_ALLOW_CLI_FALLBACK")
        mode, health, reason = classify_route(
            service_active=str(service.get("active") or "unknown"),
            window_found=window_found,
            fallback_enabled=fallback_enabled,
        )
        agents.append(
            {
                "name": agent["name"],
                "subject": subject,
                "service": service,
                "window": {
                    "name": window_name,
                    "present": window_found,
                },
                "route_mode": mode,
                "route_health": health,
                "route_reason": reason,
                "fallback_enabled": fallback_enabled,
                "delivery_timeout_seconds": service_env_flag(unit, "ECHO_TUI_DELIVERY_TIMEOUT"),
                "reply_capture_timeout_seconds": env_int(unit, "ECHO_TUI_REPLY_CAPTURE_TIMEOUT"),
                "latest_open_cli_session": latest_open_cli_session(profile_root),
                "latest_proof": latest_nats_proof(profile_root, subject),
            }
        )
        latest_proof = agents[-1]["latest_proof"]
        if isinstance(latest_proof, dict):
            agents[-1]["latest_proof_timestamp"] = latest_proof.get("timestamp")
            agents[-1]["latest_reply_mode"] = latest_proof.get("reply_mode")
        else:
            agents[-1]["latest_proof_timestamp"] = None
            agents[-1]["latest_reply_mode"] = None

    latch_unit = "latch-nats-inbox.service"
    payload = {
        "generated_at": now_utc(),
        "agents": agents,
        "operator_inbox": {
            "name": "latch",
            "subject": "nova.latch.direct",
            "service": {"unit": latch_unit, **systemctl_state(latch_unit, user=True)},
            "route_mode": "inbox",
        },
    }
    write_json(OUTPUT_PATH, payload)


if __name__ == "__main__":
    main()
