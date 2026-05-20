"""Tests for the guarded direct NATS session hook."""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from direct_nats_session_hook import (
    build_direct_nats_session_hook,
    build_dry_run_envelope,
)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def write_route_state(root: Path) -> None:
    write_json(
        root / "ops" / "runtime" / "crew_route_state.json",
        {
            "agents": [
                {
                    "name": "echo",
                    "subject": "nova.echo.direct",
                    "route_mode": "visible-ready",
                    "route_health": "healthy",
                    "route_reason": "bridge active and visible CLI window found",
                    "service": {"unit": "echo-tui-nats-bridge.service", "active": "active"},
                    "window": {"present": True},
                    "fallback_enabled": False,
                    "latest_open_cli_session": {"id": "session-1"},
                    "latest_proof": {"event_id": "proof-1"},
                    "latest_proof_timestamp": "2026-05-19T20:00:00+00:00",
                    "latest_reply_mode": "visible-cli",
                },
                {
                    "name": "testova",
                    "subject": "nova.testova.direct",
                    "route_mode": "visible-missing",
                    "route_health": "degraded",
                    "route_reason": "operator hold",
                    "service": {"unit": "testova-tui-nats-bridge.service", "active": "active"},
                    "window": {"present": False},
                    "fallback_enabled": False,
                },
            ]
        },
    )


def test_hook_exposes_targets_without_enabling_publish(tmp_path: Path, monkeypatch) -> None:
    """Default hook mode should be dry-run and preserve voice behavior."""
    monkeypatch.delenv("PIPECAT_DIRECT_NATS_SESSION_HOOK_ENABLED", raising=False)
    write_route_state(tmp_path)

    payload = build_direct_nats_session_hook(tmp_path)

    assert payload["enabled"] is False
    assert payload["mode"] == "dry-run"
    assert payload["default_voice_behavior"] == "preserved"
    assert payload["contract"]["forbidden_owner_change"] is True
    targets = {item["name"]: item for item in payload["targets"]}
    assert targets["echo"]["status"] == "available"
    assert targets["echo"]["subject"] == "nova.echo.direct"
    assert targets["testova"]["status"] == "guarded"
    assert "operator-hold" in targets["testova"]["blockers"]


def test_dry_run_builds_reply_envelope_without_publish(tmp_path: Path, monkeypatch) -> None:
    """Dry-run endpoint helper should return a publishable envelope but not send it."""
    monkeypatch.delenv("PIPECAT_DIRECT_NATS_SESSION_HOOK_ENABLED", raising=False)
    write_route_state(tmp_path)

    payload = build_dry_run_envelope(tmp_path, "echo", "route this", "voice-gateway")

    assert payload["published"] is False
    assert payload["subject"] == "nova.echo.direct"
    assert payload["envelope"]["from"] == "voice-gateway"
    assert payload["envelope"]["to"] == "echo"
    assert payload["envelope"]["reply_to"] == "_DRY_RUN_REPLY_INBOX_"
    assert payload["envelope"]["message"] == "route this"


@pytest.mark.parametrize("target,message", [("bad target", "hello"), ("echo", "")])
def test_dry_run_rejects_invalid_inputs(tmp_path: Path, target: str, message: str) -> None:
    """Invalid dry-run requests should fail before a NATS publish is possible."""
    write_route_state(tmp_path)

    with pytest.raises(ValueError):
        build_dry_run_envelope(tmp_path, target, message)


def test_gateway_exposes_guarded_hook_endpoints(tmp_path: Path, monkeypatch) -> None:
    """Gateway endpoints should expose the hook without publishing NATS traffic."""
    import gateway

    write_route_state(tmp_path)
    monkeypatch.setattr(gateway, "ROOT", tmp_path)

    client = TestClient(gateway.app)
    hook = client.get("/api/direct-nats-session-hook")
    assert hook.status_code == 200
    assert hook.json()["mode"] == "dry-run"

    dry_run = client.post(
        "/api/direct-nats-session-hook/dry-run",
        json={"target": "echo", "message": "route this"},
    )
    assert dry_run.status_code == 200
    assert dry_run.json()["published"] is False
    assert dry_run.json()["subject"] == "nova.echo.direct"
