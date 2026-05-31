"""Read-only Hermes TUI mirror payloads for the pipecat gateway."""

from __future__ import annotations

import os
import json
import re
import sqlite3
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from session_state_api import build_session_state

PROFILE_ROOT = Path("/home/x/.hermes/profiles")
ACTIVE_ROOT = Path("/adapt/novas/active")
NAME_RE = re.compile(r"^[a-z][a-z0-9_-]{1,30}$")


def _utc_from_unix(value: float | int | None) -> str | None:
    if value is None:
        return None
    try:
        return datetime.fromtimestamp(float(value), tz=timezone.utc).isoformat()
    except (OverflowError, OSError, ValueError):
        return None


def _clip(text: str | None, limit: int = 4000) -> str:
    clean = re.sub(r"\s+", " ", text or "").strip()
    if len(clean) <= limit:
        return clean
    return f"{clean[: limit - 1]}..."


def _utc_from_iso(value: str | None) -> str | None:
    if not value:
        return None
    raw = value.strip()
    if not raw:
        return None
    if raw.endswith("Z"):
        raw = f"{raw[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).isoformat()


def _speaker_label(agent: str, role: str, content: str) -> str:
    if role == "assistant":
        return agent.lower()
    sender = re.search(r"Voice message from ([^:]+):", content)
    if sender:
        name = sender.group(1).strip().lower()
        return "chase" if name == "chase" else name
    legacy_sender = re.search(r"Sender:\s*([^\n. ]+)", content)
    if legacy_sender:
        name = legacy_sender.group(1).strip().lower()
        return "chase" if name == "chase" else name
    return "chase"


def _display_turn_content(content: str) -> str:
    text = re.sub(r"\s+", " ", content or "").strip()
    if text.startswith("[IMPORTANT: You are running as a scheduled cron job."):
        close_index = text.rfind("] ")
        if close_index > 0:
            text = text[close_index + 2 :].strip()
    voice = re.search(r"Voice message from [^:]+:\s*(.*?)\s+Internal trace\b", text)
    if voice:
        return _clip(voice.group(1), 1200)
    latest = re.search(
        r"Latest user message:\s*(.*?)\s+Recent (?:shared room transcript|room context):",
        text,
    )
    if latest:
        return _clip(latest.group(1), 1200)
    message = re.search(r"Message:\s*(.*?)\s+Answer in this visible CLI session\.", text)
    if message:
        return _clip(message.group(1), 1200)
    text = re.sub(r"```.*?```", " ", text, flags=re.S)
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = re.sub(r"(?m)^\s*[-*•]\s+", "", text)
    text = re.sub(r"(?m)^\s*\d+[.)]\s+", "", text)
    text = re.sub(r"[*_#>]+", "", text)
    return _clip(text, 1200)


def _collapse_display_turns(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    collapsed: list[dict[str, Any]] = []
    for message in messages:
        if (
            collapsed
            and collapsed[-1].get("speaker") == message.get("speaker")
            and collapsed[-1].get("role") == message.get("role")
        ):
            collapsed[-1] = message
            continue
        collapsed.append(message)
    return collapsed


def _read_model_config(profile_path: Path) -> dict[str, str | None]:
    config_path = profile_path / "config.yaml"
    if not config_path.exists():
        return {"provider": None, "model": None}
    try:
        text = config_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return {"provider": None, "model": None}

    result = {"provider": None, "model": None}
    for match in re.finditer(r"(?ms)^model:\n(?P<body>.*?)(?=^\S|\Z)", text):
        body = match.group("body")
        provider = re.search(r"(?m)^\s+provider:\s*'?([^'\n]+)'?", body)
        default = re.search(r"(?m)^\s+default:\s*'?([^'\n]+)'?", body)
        if provider or default:
            result = {
                "provider": provider.group(1).strip() if provider else None,
                "model": default.group(1).strip() if default else None,
            }
    return result


def _latest_session(profile_path: Path, agent: str) -> dict[str, Any] | None:
    db_path = profile_path / "state.db"
    if db_path.exists():
        try:
            with sqlite3.connect(str(db_path), timeout=3) as conn:
                conn.row_factory = sqlite3.Row
                session = conn.execute(
                    """
                    SELECT id, source, model, started_at, ended_at, message_count, title
                    FROM sessions
                    ORDER BY COALESCE(ended_at, started_at) DESC, started_at DESC
                    LIMIT 1
                    """
                ).fetchone()
                if not session:
                    return _latest_json_session(profile_path, agent)
                messages = conn.execute(
                    """
                    SELECT id, role, content, timestamp
                    FROM messages
                    WHERE session_id = ?
                      AND role IN ('user', 'assistant')
                      AND COALESCE(content, '') != ''
                    ORDER BY id DESC
                    LIMIT 6
                    """,
                    (session["id"],),
                ).fetchall()
        except sqlite3.Error:
            return _latest_json_session(profile_path, agent)

        recent = _collapse_display_turns([
            {
                "id": int(row["id"]),
                "role": str(row["role"]),
                "speaker": _speaker_label(agent, str(row["role"]), str(row["content"] or "")),
                "content": _display_turn_content(str(row["content"] or "")),
                "timestamp": _utc_from_unix(row["timestamp"]),
            }
            for row in reversed(messages)
        ])
        return {
            "id": str(session["id"]),
            "source": str(session["source"]),
            "model": str(session["model"] or ""),
            "title": str(session["title"] or ""),
            "started_at": _utc_from_unix(session["started_at"]),
            "ended_at": _utc_from_unix(session["ended_at"]),
            "message_count": int(session["message_count"] or 0),
            "recent_messages": recent,
        }
    return _latest_json_session(profile_path, agent)


def _latest_json_session(profile_path: Path, agent: str) -> dict[str, Any] | None:
    session_dir = profile_path / "sessions"
    if not session_dir.exists():
        return None

    candidates = sorted(
        session_dir.glob("session_*.json"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    for path in candidates[:12]:
        try:
            payload = json.loads(path.read_text(encoding="utf-8", errors="replace"))
        except (OSError, json.JSONDecodeError):
            continue
        messages = payload.get("messages")
        if not isinstance(messages, list):
            continue

        recent: list[dict[str, Any]] = []
        for index, message in enumerate(messages):
            if not isinstance(message, dict):
                continue
            role = str(message.get("role") or "")
            content = str(message.get("content") or "")
            if role not in {"user", "assistant"} or not content.strip():
                continue
            recent.append(
                {
                    "id": index + 1,
                    "role": role,
                    "speaker": _speaker_label(agent, role, content),
                    "content": _display_turn_content(content),
                    "timestamp": _utc_from_iso(
                        str(message.get("timestamp") or payload.get("last_updated") or "")
                    ),
                }
            )
        if not recent:
            continue

        return {
            "id": str(payload.get("session_id") or path.stem),
            "source": str(payload.get("platform") or "json"),
            "model": str(payload.get("model") or ""),
            "title": str(payload.get("title") or ""),
            "started_at": _utc_from_iso(str(payload.get("session_start") or "")),
            "ended_at": None,
            "message_count": int(payload.get("message_count") or len(messages)),
            "recent_messages": _collapse_display_turns(recent[-6:]),
        }
    return None


def _window_snapshot(agent: str, expected_name: str) -> dict[str, Any]:
    cmd = ["xdotool", "search", "--name", expected_name]
    env = {**os.environ, "DISPLAY": os.environ.get("DISPLAY", ":0")}
    try:
        proc = subprocess.run(
            cmd,
            text=True,
            capture_output=True,
            timeout=3,
            check=False,
            env=env,
        )
    except (OSError, subprocess.SubprocessError):
        return {"expected_name": expected_name, "present": False, "id": None}
    ids = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
    return {
        "expected_name": expected_name,
        "present": bool(ids),
        "id": ids[-1] if ids else None,
        "agent": agent,
    }


def _agent_route(root: Path, agent: str) -> dict[str, Any] | None:
    state = build_session_state(root)
    for item in state.get("agents", []):
        if isinstance(item, dict) and item.get("name") == agent:
            return item
    return None


def _systemctl_user_state(unit: str, action: str) -> str:
    env = {
        **os.environ,
        "XDG_RUNTIME_DIR": os.environ.get("XDG_RUNTIME_DIR", "/run/user/1000"),
        "DBUS_SESSION_BUS_ADDRESS": os.environ.get(
            "DBUS_SESSION_BUS_ADDRESS",
            "unix:path=/run/user/1000/bus",
        ),
    }
    try:
        proc = subprocess.run(
            ["systemctl", "--user", action, unit],
            text=True,
            capture_output=True,
            timeout=3,
            check=False,
            env=env,
        )
    except (OSError, subprocess.SubprocessError):
        return "unknown"
    return (proc.stdout or proc.stderr or "unknown").strip() or "unknown"


def _route_with_fallback(root: Path, agent: str) -> dict[str, Any]:
    route = _agent_route(root, agent)
    if route:
        return route
    unit = f"{agent}-tui-nats-bridge.service"
    active = _systemctl_user_state(unit, "is-active")
    enabled = _systemctl_user_state(unit, "is-enabled")
    return {
        "name": agent,
        "subject": f"nova.{agent}.direct",
        "route_mode": "visible-ready" if active == "active" else "unknown",
        "route_health": "healthy" if active == "active" else "unknown",
        "route_reason": "mirror fallback from user systemd unit state",
        "bridge_owner": unit,
        "bridge_active": active,
        "bridge_enabled": enabled,
    }


def build_tui_mirror(root: Path, agent: str = "iris") -> dict[str, Any]:
    """Build a read-only, secret-redacted mirror payload for one Hermes TUI.

    Parameters:
        root: Repository root for runtime route-state snapshots.
        agent: Lowercase nova profile name to inspect.

    Returns:
        JSON-serializable session, model, route, and window metadata. The
        function never sends NATS traffic, performs model calls, or exposes
        config values outside the provider/model names needed by the UI.

    Raises:
        ValueError: If ``agent`` is not a valid nova route name.
    """
    normalized = agent.strip().lower()
    if not NAME_RE.match(normalized):
        raise ValueError("invalid agent name")

    profile_path = PROFILE_ROOT / normalized
    active_path = ACTIVE_ROOT / normalized
    expected_name = f"{normalized.capitalize()} CLI"

    return {
        "agent": normalized,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "profile_path": str(profile_path),
        "active_path": str(active_path) if active_path.exists() else None,
        "model": _read_model_config(profile_path),
        "route": _route_with_fallback(root, normalized),
        "window": _window_snapshot(normalized, expected_name),
        "latest_session": _latest_session(profile_path, normalized),
        "controls": {"read_only": True, "remote_input": False, "desktop_stream": False},
    }
