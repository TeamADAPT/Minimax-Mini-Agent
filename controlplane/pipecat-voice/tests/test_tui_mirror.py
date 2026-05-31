"""Tests for the read-only Hermes TUI mirror payload."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import tui_mirror
from tui_mirror import build_tui_mirror


def _write_config(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    (path / "config.yaml").write_text(
        """
model:
  base_url: https://api.deepseek.com/v1
  default: deepseek-v4-flash
  provider: deepseek
""".lstrip(),
        encoding="utf-8",
    )


def _write_state_db(path: Path) -> None:
    db_path = path / "state.db"
    with sqlite3.connect(str(db_path)) as conn:
        conn.execute(
            """
            CREATE TABLE sessions (
                id TEXT PRIMARY KEY,
                source TEXT NOT NULL,
                model TEXT,
                started_at REAL NOT NULL,
                ended_at REAL,
                message_count INTEGER DEFAULT 0,
                title TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE messages (
                id INTEGER PRIMARY KEY,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT,
                timestamp REAL NOT NULL
            )
            """
        )
        conn.execute(
            """
            INSERT INTO sessions
                (id, source, model, started_at, ended_at, message_count, title)
            VALUES ('s1', 'cli', 'deepseek-v4-flash', 1000, NULL, 2, 'Iris voice')
            """
        )
        conn.execute(
            """
            INSERT INTO messages (id, session_id, role, content, timestamp)
            VALUES
                (1, 's1', 'user', 'hello from phone', 1001),
                (2, 's1', 'assistant', 'visible reply from iris', 1002)
            """
        )


def _write_json_session(path: Path) -> None:
    session_dir = path / "sessions"
    session_dir.mkdir(parents=True, exist_ok=True)
    (session_dir / "session_20260523_010000_test.json").write_text(
        """
{
  "session_id": "json-session",
  "model": "deepseek-v4-flash",
  "platform": "cli",
  "session_start": "2026-05-23T01:00:00",
  "last_updated": "2026-05-23T01:01:00",
  "message_count": 3,
  "messages": [
    {
      "role": "user",
      "content": "Voice message from chase: status check Internal trace abc."
    },
    {
      "role": "assistant",
      "content": "iris standing by"
    }
  ]
}
""".lstrip(),
        encoding="utf-8",
    )


def test_build_tui_mirror_redacts_config_and_reads_latest_session(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    profile_root = tmp_path / "profiles"
    active_root = tmp_path / "active"
    iris_profile = profile_root / "iris"
    (active_root / "iris").mkdir(parents=True)
    _write_config(iris_profile)
    _write_state_db(iris_profile)
    monkeypatch.setattr(tui_mirror, "PROFILE_ROOT", profile_root)
    monkeypatch.setattr(tui_mirror, "ACTIVE_ROOT", active_root)

    payload = build_tui_mirror(tmp_path, "iris")

    assert payload["agent"] == "iris"
    assert payload["model"] == {"provider": "deepseek", "model": "deepseek-v4-flash"}
    assert payload["controls"] == {
        "read_only": True,
        "remote_input": False,
        "desktop_stream": False,
    }
    assert "api_key" not in str(payload).lower()
    assert payload["latest_session"]["id"] == "s1"
    assert [m["role"] for m in payload["latest_session"]["recent_messages"]] == [
        "user",
        "assistant",
    ]


def test_build_tui_mirror_reads_json_session_without_state_db(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    profile_root = tmp_path / "profiles"
    active_root = tmp_path / "active"
    iris_profile = profile_root / "iris"
    (active_root / "iris").mkdir(parents=True)
    _write_config(iris_profile)
    _write_json_session(iris_profile)
    monkeypatch.setattr(tui_mirror, "PROFILE_ROOT", profile_root)
    monkeypatch.setattr(tui_mirror, "ACTIVE_ROOT", active_root)

    payload = build_tui_mirror(tmp_path, "iris")

    assert payload["latest_session"]["id"] == "json-session"
    assert payload["latest_session"]["recent_messages"] == [
        {
            "id": 1,
            "role": "user",
            "speaker": "chase",
            "content": "status check",
            "timestamp": "2026-05-23T01:01:00+00:00",
        },
        {
            "id": 2,
            "role": "assistant",
            "speaker": "iris",
            "content": "iris standing by",
            "timestamp": "2026-05-23T01:01:00+00:00",
        },
    ]


def test_display_turn_content_removes_cron_wrapper() -> None:
    content = (
        '[IMPORTANT: You are running as a scheduled cron job. DELIVERY: final. '
        'SILENT: respond with exactly "[SILENT]" if quiet.] '
        "Append a heartbeat entry to /adapt/logs/fleet-activity.log."
    )

    assert (
        tui_mirror._display_turn_content(content)
        == "Append a heartbeat entry to /adapt/logs/fleet-activity.log."
    )


def test_build_tui_mirror_rejects_invalid_agent_name(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="invalid agent name"):
        build_tui_mirror(tmp_path, "../iris")


def test_gateway_exposes_tui_mirror_endpoint(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import gateway

    profile_root = tmp_path / "profiles"
    iris_profile = profile_root / "iris"
    _write_config(iris_profile)
    _write_state_db(iris_profile)
    monkeypatch.setattr(tui_mirror, "PROFILE_ROOT", profile_root)
    monkeypatch.setattr(gateway, "ROOT", tmp_path)

    client = TestClient(gateway.app)
    response = client.get("/api/tui-mirror/iris")

    assert response.status_code == 200
    payload = response.json()
    assert payload["agent"] == "iris"
    assert payload["model"]["model"] == "deepseek-v4-flash"
    assert payload["controls"]["read_only"] is True


def test_gateway_rejects_invalid_tui_mirror_agent() -> None:
    import gateway

    client = TestClient(gateway.app)
    response = client.get("/api/tui-mirror/Bad%20Agent")

    assert response.status_code == 400
