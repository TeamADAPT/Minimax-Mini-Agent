"""Guarded direct NATS session hook planning for pipecat voice routes."""

from __future__ import annotations

import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from session_state_api import build_session_state

HOOK_ENABLE_ENV = "PIPECAT_DIRECT_NATS_SESSION_HOOK_ENABLED"
NAME_RE = re.compile(r"^[a-z][a-z0-9_-]{1,30}$")


def now_utc() -> str:
    """Return the current UTC timestamp in ISO-8601 format."""
    return datetime.now(timezone.utc).isoformat()


def hook_publish_enabled() -> bool:
    """Return whether live hook publishing is enabled by environment flag."""
    return os.environ.get(HOOK_ENABLE_ENV, "").strip().lower() in {"1", "true", "yes", "on"}


def _target_status(agent: dict[str, Any]) -> str:
    route_mode = str(agent.get("route_mode") or "")
    route_health = str(agent.get("route_health") or "")
    bridge_active = str(agent.get("bridge_active") or "")
    if route_mode == "visible-ready" and route_health == "healthy" and bridge_active == "active":
        return "available"
    if route_health == "degraded" or route_mode in {"visible-missing", "fallback-active"}:
        return "guarded"
    return "unavailable"


def _target_blockers(agent: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if agent.get("bridge_active") != "active":
        blockers.append("bridge-not-active")
    if agent.get("route_health") and agent.get("route_health") != "healthy":
        blockers.append(f"route-health-{agent['route_health']}")
    if agent.get("route_mode") and agent.get("route_mode") != "visible-ready":
        blockers.append(f"route-mode-{agent['route_mode']}")
    if not agent.get("window_present") and agent.get("route_mode") == "visible-ready":
        blockers.append("visible-window-missing")
    if agent.get("name") == "testova":
        blockers.append("operator-hold")
    return blockers


def _summarize_target(agent: dict[str, Any]) -> dict[str, Any]:
    name = str(agent.get("name") or "")
    subject = str(agent.get("subject") or "")
    return {
        "name": name,
        "subject": subject,
        "status": _target_status(agent),
        "route_mode": agent.get("route_mode"),
        "route_health": agent.get("route_health"),
        "route_reason": agent.get("route_reason"),
        "bridge_owner": agent.get("bridge_owner"),
        "window_present": agent.get("window_present"),
        "fallback_enabled": agent.get("fallback_enabled"),
        "latest_session_id": agent.get("latest_session_id"),
        "latest_proof_event_id": agent.get("latest_proof_event_id"),
        "latest_proof_timestamp": agent.get("latest_proof_timestamp"),
        "latest_reply_mode": agent.get("latest_reply_mode"),
        "blockers": _target_blockers(agent),
    }


def build_direct_nats_session_hook(root: Path) -> dict[str, Any]:
    """Build the guarded direct-session hook payload.

    The payload is read-only and does not publish NATS traffic. Live publishing
    remains disabled unless ``PIPECAT_DIRECT_NATS_SESSION_HOOK_ENABLED`` is set.
    """
    session_state = build_session_state(root)
    targets = [
        _summarize_target(agent)
        for agent in session_state.get("agents", [])
        if isinstance(agent, dict) and agent.get("name") and agent.get("subject")
    ]
    publish_enabled = hook_publish_enabled()
    return {
        "generated_at": now_utc(),
        "enabled": publish_enabled,
        "mode": "live-publish" if publish_enabled else "dry-run",
        "default_voice_behavior": "preserved",
        "publish_guard_env": HOOK_ENABLE_ENV,
        "contract": {
            "target_source": "/api/session-state",
            "dry_run_endpoint": "/api/direct-nats-session-hook/dry-run",
            "live_publish_default": False,
            "requires_reply_to": True,
            "forbidden_owner_change": True,
        },
        "targets": targets,
    }


def build_dry_run_envelope(
    root: Path,
    target_name: str,
    message: str,
    from_agent: str = "pipecat",
) -> dict[str, Any]:
    """Build a direct NATS envelope without publishing it.

    Parameters:
        root: Repository root for the pipecat-voice service.
        target_name: Target nova name from the session hook target list.
        message: Message text that would be sent.
        from_agent: Logical caller name used in the envelope.

    Returns:
        A JSON-serializable dry-run result containing target metadata and the
        envelope that would be published if the hook were explicitly enabled.

    Raises:
        ValueError: If the target name or message is invalid.
    """
    normalized = target_name.strip().lower()
    if not NAME_RE.match(normalized):
        raise ValueError("invalid target name")
    if not message.strip():
        raise ValueError("message must not be empty")

    hook = build_direct_nats_session_hook(root)
    targets = {item["name"]: item for item in hook["targets"]}
    target = targets.get(normalized)
    if not target:
        raise ValueError("unknown target")

    event_id = f"pipecat-dry-run-{normalized}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    envelope = {
        "id": event_id,
        "from": from_agent,
        "to": normalized,
        "type": "voice",
        "message": message,
        "timestamp": now_utc(),
        "reply_to": "_DRY_RUN_REPLY_INBOX_",
    }
    return {
        "generated_at": now_utc(),
        "published": False,
        "enabled": hook["enabled"],
        "mode": hook["mode"],
        "subject": target["subject"],
        "target": target,
        "envelope": envelope,
    }
