"""Tests for canonical CommsOps turn events."""

from __future__ import annotations

import json
from pathlib import Path

from turn_events import (
    SCHEMA,
    append_turn_event,
    backfill_room_history,
    build_turn_event,
    build_turn_event_from_room_event,
    read_turn_events,
    redact_text,
)


def test_redact_text_removes_common_secret_shapes() -> None:
    text = (
        "token=abc1234567899999 "
        "Authorization: Bearer abcdefghijklmnop "
        "nats://user:pass@localhost:18020"
    )

    clean, changed = redact_text(text)

    assert changed is True
    assert "abc1234567899999" not in clean
    assert "abcdefghijklmnop" not in clean
    assert "user:pass" not in clean
    assert "<redacted>" in clean


def test_build_turn_event_from_room_event_keeps_route_debug_metadata() -> None:
    event = {
        "turn_id": "direct-1",
        "ts": "2026-05-31T17:00:00+00:00",
        "kind": "direct",
        "agent": "iris",
        "runtime": "rust",
        "subject": "nova.iris.rust.direct",
        "route": {
            "event_id": "bridge-1",
            "runtime": "rust",
            "delivery": "api_session",
            "hermes_session_id": "nats_iris_chase",
        },
        "message": "reply text",
    }

    turn = build_turn_event_from_room_event(event)

    assert turn["schema"] == SCHEMA
    assert turn["actor"] == {"role": "agent", "name": "iris"}
    assert turn["target"]["agent"] == "iris"
    assert turn["route"]["subject"] == "nova.iris.rust.direct"
    assert turn["route"]["delivery"] == "api_session"
    assert turn["session"]["id"] == "nats_iris_chase"
    assert turn["content"]["text"] == "reply text"


def test_append_turn_event_writes_jsonl(tmp_path: Path) -> None:
    path = tmp_path / "turn_events.jsonl"
    event = build_turn_event(
        turn_id="turn-1",
        timestamp="2026-05-31T17:00:00+00:00",
        role="user",
        actor="chase",
        text="hello",
        source="test",
        channel="direct",
        direction="inbound",
        target_agent="iris",
    )

    append_turn_event(event, path)

    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    assert rows == [event]
    assert path.stat().st_mode & 0o777 == 0o600


def test_read_turn_events_skips_bad_json_and_bounds_limit(tmp_path: Path) -> None:
    path = tmp_path / "turn_events.jsonl"
    path.write_text(
        "\n".join(
            [
                '{"event_id":"one","status":"ok"}',
                'not json',
                '{"event_id":"two","status":"timeout"}',
            ]
        ),
        encoding="utf-8",
    )

    assert read_turn_events(10, path) == [
        {"event_id": "one", "status": "ok"},
        {"event_id": "two", "status": "timeout"},
    ]
    assert read_turn_events(1, path) == [{"event_id": "two", "status": "timeout"}]


def test_backfill_room_history_writes_canonical_events_and_skips_duplicates(
    tmp_path: Path,
) -> None:
    room_history = tmp_path / "room_history.jsonl"
    output = tmp_path / "turn_events.jsonl"
    room_history.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "turn_id": "room-1",
                        "ts": "2026-05-31T17:00:00+00:00",
                        "kind": "user",
                        "mode": "room",
                        "targets": ["iris"],
                        "message": "hello room",
                    }
                ),
                "not-json",
                json.dumps(
                    {
                        "turn_id": "room-1",
                        "ts": "2026-05-31T17:00:01+00:00",
                        "kind": "agent",
                        "agent": "iris",
                        "runtime": "rust",
                        "subject": "nova.iris.rust.meet",
                        "message": "hello chase",
                    }
                ),
            ]
        ),
        encoding="utf-8",
    )

    first = backfill_room_history(room_history, output)
    second = backfill_room_history(room_history, output)

    assert first == {"scanned": 3, "written": 2, "skipped": 0, "bad": 1}
    assert second == {"scanned": 3, "written": 0, "skipped": 2, "bad": 1}
    rows = read_turn_events(10, output)
    assert [row["schema"] for row in rows] == [SCHEMA, SCHEMA]
    assert [row["content"]["text"] for row in rows] == ["hello room", "hello chase"]
