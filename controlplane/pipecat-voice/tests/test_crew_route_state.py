"""Tests for the crew route-state snapshot writer."""

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from crew_route_state import classify_route, event_id_from_content  # noqa: E402


def test_classify_route_visible_ready():
    """Active bridge plus visible window is healthy visible routing."""
    assert classify_route(
        service_active="active",
        window_found=True,
        fallback_enabled=False,
    ) == ("visible-ready", "healthy", "bridge active and visible CLI window found")


def test_classify_route_bridge_down():
    """Inactive bridge is down even if a window exists."""
    mode, health, reason = classify_route(
        service_active="inactive",
        window_found=True,
        fallback_enabled=True,
    )
    assert mode == "bridge-down"
    assert health == "down"
    assert "not active" in reason


def test_classify_route_fallback_active():
    """Missing visible window with fallback enabled is degraded fallback routing."""
    mode, health, reason = classify_route(
        service_active="active",
        window_found=False,
        fallback_enabled=True,
    )
    assert mode == "fallback-active"
    assert health == "degraded"
    assert "fallback is enabled" in reason


def test_classify_route_visible_missing():
    """Missing visible window with no fallback is degraded visible routing."""
    mode, health, reason = classify_route(
        service_active="active",
        window_found=False,
        fallback_enabled=False,
    )
    assert mode == "visible-missing"
    assert health == "degraded"
    assert "fallback is disabled" in reason


def test_event_id_from_content_strips_sentence_period():
    """Prompt formatting may add punctuation after the event ID."""
    content = "Subject: nova.echo.direct. Event ID: echo-proof-abc123. Message: done."
    assert event_id_from_content(content) == "echo-proof-abc123"
