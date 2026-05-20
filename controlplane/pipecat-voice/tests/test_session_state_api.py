"""Tests for the read-only session-state API payload builder."""

import json
from pathlib import Path

from session_state_api import build_session_state, summarize_agents


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_build_session_state_summarizes_route_snapshot(tmp_path: Path) -> None:
    """One payload should answer who is live, how routed, and current session id."""
    write_json(
        tmp_path / "ops" / "runtime" / "crew_route_state.json",
        {
            "agents": [
                {
                    "name": "echo",
                    "subject": "nova.echo.direct",
                    "route_mode": "visible-ready",
                    "route_health": "healthy",
                    "route_reason": "bridge active and visible CLI window found",
                    "service": {
                        "unit": "echo-tui-nats-bridge.service",
                        "active": "active",
                        "enabled": "enabled",
                    },
                    "window": {"name": "Echo CLI", "present": True},
                    "fallback_enabled": False,
                    "latest_open_cli_session": {"id": "session-1", "message_count": 4},
                    "latest_proof_timestamp": "2026-05-19T20:00:00+00:00",
                    "latest_reply_mode": "visible-cli",
                    "latest_proof": {
                        "event_id": "echo-proof-1",
                        "reply_captured": True,
                    },
                }
            ],
            "operator_inbox": {"name": "latch", "route_mode": "inbox"},
        },
    )
    write_json(tmp_path / "ops" / "runtime" / "crew_heartbeat.json", {"ok": True})

    payload = build_session_state(tmp_path)

    assert payload["summary"]["agent_count"] == 1
    assert payload["summary"]["route_modes"] == {"visible-ready": 1}
    assert payload["operator_inbox"]["name"] == "latch"
    assert payload["snapshots"]["route_state"]["exists"] is True
    assert payload["snapshots"]["watchdog"]["exists"] is False
    assert payload["agents"] == [
        {
            "name": "echo",
            "subject": "nova.echo.direct",
            "route_mode": "visible-ready",
            "route_health": "healthy",
            "route_reason": "bridge active and visible CLI window found",
            "bridge_owner": "echo-tui-nats-bridge.service",
            "bridge_active": "active",
            "bridge_enabled": "enabled",
            "window_name": "Echo CLI",
            "window_present": True,
            "fallback_enabled": False,
            "latest_session_id": "session-1",
            "latest_session_message_count": 4,
            "latest_proof_timestamp": "2026-05-19T20:00:00+00:00",
            "latest_reply_mode": "visible-cli",
            "latest_proof_event_id": "echo-proof-1",
            "latest_proof_reply_captured": True,
        }
    ]


def test_summarize_agents_ignores_invalid_snapshot_shapes() -> None:
    """Malformed route snapshots should degrade to an empty agent list."""
    assert summarize_agents(None) == []
    assert summarize_agents({"agents": {"echo": {}}}) == []
    assert summarize_agents({"agents": ["bad"]}) == []
