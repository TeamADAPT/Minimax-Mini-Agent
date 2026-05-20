"""Tests for the crew route-state snapshot writer."""

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import ops_loop_common  # noqa: E402
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


def test_window_present_prefers_class_when_available(monkeypatch):
    """Class-addressed terminals should count as visible even if the title changes."""
    calls = []

    class Result:
        def __init__(self, returncode: int, stdout: str = "") -> None:
            self.returncode = returncode
            self.stdout = stdout

    def fake_run_command(args, *, timeout=10.0, check=False):
        calls.append(args)
        if args[:3] == ["xdotool", "search", "--class"]:
            return Result(0, "12345\n")
        return Result(1, "")

    monkeypatch.setattr(ops_loop_common, "run_command", fake_run_command)

    assert ops_loop_common.window_present("Testova CLI", "TestovaCLI") is True
    assert calls == [["xdotool", "search", "--class", "TestovaCLI"]]
