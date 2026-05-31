"""Canonical CommsOps turn-event emission.

This module keeps the hot voice path simple: build a normalized event, redact
obvious secret material, and append one JSON object to a shared JSONL handoff
file. Memory, analytics, and audit consumers can tail that file without
scraping UI transcript text or Hermes-specific session tables.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA = "comms.turn.v1"
DEFAULT_TURN_EVENTS_PATH = Path("/adapt/novas/active/_shared/turn_events.jsonl")
SECRET_PATTERNS = (
    re.compile(r"\b(sk-[A-Za-z0-9_\-]{16,})\b"),
    re.compile(r"\b(nvapi-[A-Za-z0-9_\-]{16,})\b"),
    re.compile(r"\b(ghp_[A-Za-z0-9_]{16,})\b"),
    re.compile(r"\b(xox[baprs]-[A-Za-z0-9_\-]{16,})\b"),
    re.compile(r"(?i)\b(authorization:\s*bearer\s+)[A-Za-z0-9._\-]{16,}"),
    re.compile(r"(?i)\b(api[_-]?key|token|password)\s*[:=]\s*['\"]?[^'\"\s]{8,}"),
    re.compile(r"(?i)\b(redis|postgres(?:ql)?|nats)://([^:\s/@]+):([^@\s]+)@"),
)


def utc_now() -> str:
    """Return the current UTC timestamp as an ISO-8601 string."""
    return datetime.now(timezone.utc).isoformat()


def turn_events_path() -> Path:
    """Return the configured canonical turn-event handoff path."""
    configured = os.environ.get("COMMSOPS_TURN_EVENTS_PATH", "").strip()
    return Path(configured) if configured else DEFAULT_TURN_EVENTS_PATH


def redact_text(value: str | None) -> tuple[str, bool]:
    """Redact obvious secret strings from free-form text.

    Parameters:
        value: Text that may contain credentials or connection URLs.

    Returns:
        A tuple of ``(redacted_text, changed)``.
    """
    text = value or ""
    changed = False
    for pattern in SECRET_PATTERNS:
        new_text = pattern.sub(lambda match: _redaction_replacement(match), text)
        changed = changed or new_text != text
        text = new_text
    return text, changed


def _redaction_replacement(match: re.Match[str]) -> str:
    if match.re.pattern.startswith("(?i)\\b(redis"):
        return f"{match.group(1)}://{match.group(2)}:<redacted>@"
    if "authorization" in match.re.pattern.lower():
        return f"{match.group(1)}<redacted>"
    if "api" in match.re.pattern.lower() or "token" in match.re.pattern.lower():
        return f"{match.group(1)}=<redacted>"
    return "<redacted>"


def stable_event_id(parts: list[str]) -> str:
    """Build a stable event id from deterministic event fields."""
    digest = hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()
    return f"turn_{digest[:24]}"


def build_turn_event(
    *,
    turn_id: str,
    timestamp: str,
    role: str,
    actor: str,
    text: str,
    source: str,
    channel: str,
    direction: str,
    status: str = "ok",
    target_agent: str | None = None,
    targets: list[str] | None = None,
    runtime: str | None = None,
    subject: str | None = None,
    route: dict[str, Any] | None = None,
    session_id: str | None = None,
    provider: str | None = None,
    model: str | None = None,
    room: str | None = None,
    latency_ms: int | None = None,
    audio: dict[str, Any] | None = None,
    failure: dict[str, Any] | None = None,
    source_event: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build one canonical CommsOps turn event.

    Parameters:
        turn_id: Stable conversation or room turn id.
        timestamp: Event timestamp in ISO-8601 form.
        role: Actor role, usually ``user``, ``agent``, ``moderator``, or ``system``.
        actor: Human or nova name that produced the content.
        text: Free-form transcript text. Obvious secret material is redacted.
        source: Producing component name, for example ``gateway.room_history``.
        channel: Logical channel such as ``direct`` or ``room``.
        direction: ``inbound`` for Chase/user text, ``outbound`` for nova replies.
        status: ``ok``, ``timeout``, or ``error``.
        target_agent: Primary recipient or responding agent when applicable.
        targets: Full room target list when applicable.
        runtime: Route runtime such as ``rust``, ``tui``, or ``hermes``.
        subject: NATS subject used for route debugging.
        route: Route metadata from the bridge final chunk.
        session_id: Hermes or bridge session id when known.
        provider: LLM/TTS/STT provider when known.
        model: Model name when known.
        room: Room/group label when known.
        latency_ms: End-to-end or route latency when known.
        audio: Audio metadata only; never raw audio bytes.
        failure: Failure class/component/message when status is not ``ok``.
        source_event: Small source pointer for dedupe and backfill traceability.

    Returns:
        A JSON-serializable event using schema ``comms.turn.v1``.
    """
    clean_text, redacted = redact_text(text)
    route_data = _safe_route(route)
    resolved_session_id = session_id or route_data.get("hermes_session_id")
    event_id = stable_event_id(
        [
            SCHEMA,
            source,
            turn_id,
            timestamp,
            role,
            actor,
            channel,
            direction,
            target_agent or "",
            route_data.get("event_id") or "",
        ]
    )
    return {
        "schema": SCHEMA,
        "event_id": event_id,
        "turn_id": turn_id,
        "timestamp": timestamp,
        "created_at": utc_now(),
        "source": source,
        "channel": channel,
        "direction": direction,
        "status": status,
        "actor": {"role": role, "name": actor},
        "target": {"agent": target_agent, "agents": targets or []},
        "route": {
            "runtime": runtime or route_data.get("runtime"),
            "subject": subject,
            "delivery": route_data.get("delivery"),
            "event_id": route_data.get("event_id"),
        },
        "session": {"id": resolved_session_id, "provider": provider, "model": model},
        "room": {"id": room or turn_id if channel in {"room", "meet"} else room},
        "content": {
            "text": clean_text,
            "chars": len(clean_text),
            "redacted": redacted,
        },
        "audio": _safe_mapping(audio),
        "latency_ms": latency_ms,
        "failure": _safe_mapping(failure),
        "source_event": _safe_mapping(source_event),
        "dedupe_key": stable_event_id([SCHEMA, source, turn_id, role, actor, clean_text]),
    }


def build_turn_event_from_room_event(event: dict[str, Any]) -> dict[str, Any]:
    """Convert an existing CX Pipe room-history row into a canonical turn event."""
    kind = str(event.get("kind") or "event").lower()
    turn_id = str(event.get("turn_id") or stable_event_id([json.dumps(event, sort_keys=True)]))
    timestamp = str(event.get("ts") or utc_now())
    route = event.get("route") if isinstance(event.get("route"), dict) else None
    message = str(event.get("message") or "")
    targets = [str(item) for item in event.get("targets", []) if str(item).strip()]
    runtime_value = event.get("runtime")
    if not runtime_value and route:
        runtime_value = route.get("runtime")
    runtime = str(runtime_value or "")
    subject = str(event.get("subject") or "") or None
    status = str(event.get("status") or ("ok" if message.strip() else "timeout"))
    failure = event.get("failure") if isinstance(event.get("failure"), dict) else None

    if kind == "user":
        role = "user"
        actor = "chase"
        direction = "inbound"
        target_agent = None
    elif kind == "moderator":
        role = "moderator"
        actor = str(event.get("agent") or event.get("moderator") or "unknown").lower()
        direction = "outbound"
        target_agent = actor
    else:
        role = "agent"
        actor = str(event.get("agent") or "unknown").lower()
        direction = "outbound"
        target_agent = actor if actor != "unknown" else None

    channel = "direct" if kind == "direct" else str(event.get("mode") or "room").lower()
    return build_turn_event(
        turn_id=turn_id,
        timestamp=timestamp,
        role=role,
        actor=actor,
        text=message,
        source="gateway.room_history",
        channel=channel,
        direction=direction,
        status=status,
        target_agent=target_agent,
        targets=targets,
        runtime=runtime or None,
        subject=subject,
        route=route,
        failure=failure,
        source_event={"kind": kind, "path": "ops/cx-pipe/room_history.jsonl"},
    )


def append_turn_event(event: dict[str, Any], path: Path | None = None) -> None:
    """Append one canonical turn event to the JSONL handoff path.

    The append uses ``O_APPEND`` so concurrent local writers cannot interleave
    file offsets. The caller is responsible for catching/logging exceptions if
    emission must remain best effort.
    """
    target = path or turn_events_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(event, sort_keys=True, ensure_ascii=True, separators=(",", ":")) + "\n"
    fd = os.open(target, os.O_APPEND | os.O_CREAT | os.O_WRONLY, 0o600)
    try:
        os.write(fd, line.encode("utf-8"))
    finally:
        os.close(fd)


def read_turn_events(limit: int = 200, path: Path | None = None) -> list[dict[str, Any]]:
    """Read the newest canonical turn events from the JSONL handoff path."""
    target = path or turn_events_path()
    if not target.exists():
        return []
    bounded = max(1, min(limit, 1000))
    rows: list[dict[str, Any]] = []
    for line in target.read_text(encoding="utf-8", errors="replace").splitlines()[-bounded:]:
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            rows.append(payload)
    return rows


def backfill_room_history(
    room_history_path: Path,
    output_path: Path | None = None,
    *,
    limit: int | None = None,
    dry_run: bool = False,
) -> dict[str, int]:
    """Convert CX Pipe room-history rows into canonical turn events.

    Parameters:
        room_history_path: Source `room_history.jsonl` file.
        output_path: Destination canonical `turn_events.jsonl` file.
        limit: Optional newest-row limit for bounded backfills.
        dry_run: Count rows without writing.

    Returns:
        Counts for scanned, written, skipped duplicate, and malformed rows.
    """
    if not room_history_path.exists():
        return {"scanned": 0, "written": 0, "skipped": 0, "bad": 0}

    target = output_path or turn_events_path()
    existing_ids = {
        str(event.get("event_id"))
        for event in read_turn_events(1000, target)
        if event.get("event_id")
    }
    lines = room_history_path.read_text(encoding="utf-8", errors="replace").splitlines()
    if limit is not None:
        lines = lines[-max(1, limit) :]

    counts = {"scanned": 0, "written": 0, "skipped": 0, "bad": 0}
    for line in lines:
        if not line.strip():
            continue
        counts["scanned"] += 1
        try:
            source_event = json.loads(line)
            if not isinstance(source_event, dict):
                counts["bad"] += 1
                continue
            turn_event = build_turn_event_from_room_event(source_event)
        except (json.JSONDecodeError, TypeError, ValueError):
            counts["bad"] += 1
            continue

        event_id = str(turn_event.get("event_id"))
        if event_id in existing_ids:
            counts["skipped"] += 1
            continue
        existing_ids.add(event_id)
        if not dry_run:
            append_turn_event(turn_event, target)
        counts["written"] += 1
    return counts


def _safe_mapping(value: dict[str, Any] | None) -> dict[str, Any]:
    if not value:
        return {}
    safe: dict[str, Any] = {}
    for key, item in value.items():
        if isinstance(item, (str, int, float, bool)) or item is None:
            safe[str(key)] = item
        elif isinstance(item, list):
            safe[str(key)] = [
                entry for entry in item if isinstance(entry, (str, int, float, bool)) or entry is None
            ]
    return safe


def _safe_route(route: dict[str, Any] | None) -> dict[str, str | None]:
    safe = _safe_mapping(route)
    return {
        "event_id": _optional_str(safe.get("event_id")),
        "runtime": _optional_str(safe.get("runtime")),
        "delivery": _optional_str(safe.get("delivery")),
        "hermes_session_id": _optional_str(safe.get("hermes_session_id")),
    }


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
