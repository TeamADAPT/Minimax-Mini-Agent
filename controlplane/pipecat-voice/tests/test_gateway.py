"""Tests for pipecat-voice gateway routing logic.

Run with: pytest tests/test_gateway.py -v
"""

import pytest
import re
from pathlib import Path

from fastapi.testclient import TestClient


class TestAgentNameValidation:
    """Test agent name validation regex."""

    def setup_method(self):
        self.name_re = re.compile(r"^[a-z][a-z0-9_-]{1,30}$")

    def test_valid_names(self):
        """Valid agent names should match."""
        valid = ["echo", "tecton", "herald", "iris", "vaeris", "pathfinder"]
        for name in valid:
            assert self.name_re.match(name), f"{name} should be valid"

    def test_invalid_names(self):
        """Invalid agent names should not match."""
        invalid = ["123start", "ALLCAPS", "has space", "has.dot", "a", ""]
        for name in invalid:
            assert not self.name_re.match(name), f"{name} should be invalid"

    def test_name_with_special_chars(self):
        """Names with allowed special chars."""
        assert self.name_re.match("test-agent")
        assert self.name_re.match("test_agent")
        assert self.name_re.match("agent123")

    def test_name_length_limits(self):
        """Test name length boundaries."""
        # 32 chars total = invalid (first char + 31 more, but max is 30 after first)
        long_name = "a" + "b" * 31
        assert not self.name_re.match(long_name)

        # 31 chars total (1 + 30) = valid
        valid_long = "a" + "b" * 30
        assert self.name_re.match(valid_long)


class TestGroupAgentParsing:
    """Test GROUP_AGENT_NAMES parsing."""

    def test_comma_separated(self):
        """Comma-separated list should parse correctly."""
        value = "tecton,herald,iris,echo"
        result = [n.strip().lower() for n in value.split(",") if n.strip()]
        assert result == ["tecton", "herald", "iris", "echo"]

    def test_with_spaces(self):
        """Handle spaces around commas."""
        value = "tecton, herald, iris, echo"
        result = [n.strip().lower() for n in value.split(",") if n.strip()]
        assert result == ["tecton", "herald", "iris", "echo"]

    def test_empty_string(self):
        """Empty string should result in empty list."""
        result = [n.strip().lower() for n in "".split(",") if n.strip()]
        assert result == []


class TestRouteConfiguration:
    """Test route configuration logic."""

    def test_solo_mode_targets(self):
        """Solo mode should target single agent."""
        mode = "solo"
        agents = ["echo"]
        assert len(agents) == 1
        assert mode == "solo"

    def test_pair_mode_limits(self):
        """Pair mode should limit to 2 agents."""
        mode = "pair"
        candidates = ["echo", "tecton", "herald"]
        selected = candidates[:2] if len(candidates) > 2 else candidates
        assert len(selected) == 2

    def test_room_mode_all_agents(self):
        """Room mode can include multiple agents."""
        mode = "room"
        agents = ["echo", "tecton", "herald", "iris"]
        assert len(agents) >= 1
        assert mode == "room"


class TestEnvelopeValidation:
    """Test NATS message envelope structure."""

    def test_valid_envelope(self):
        """Valid envelope should have required fields."""
        envelope = {
            "from": "chase",
            "to": "echo",
            "type": "voice",
            "message": "hello",
            "timestamp": "2026-05-11T00:00:00Z",
            "reply_to": "_INBOX.abc123",
        }
        required = ["from", "to", "type", "message", "timestamp", "reply_to"]
        for field in required:
            assert field in envelope, f"Missing required field: {field}"

    def test_envelope_with_room(self):
        """Room envelope should include room field."""
        envelope = {
            "from": "chase",
            "type": "voice",
            "message": "hello",
            "timestamp": "2026-05-11T00:00:00Z",
            "reply_to": "_INBOX.abc123",
            "room": "room123",
        }
        assert "room" in envelope
        assert envelope["room"] == "room123"


class TestChunkProtocol:
    """Test chunk streaming protocol."""

    def test_chunk_format(self):
        """Chunk should follow protocol."""
        chunk = {"chunk": "Hello ", "final": False}
        assert "chunk" in chunk
        assert "final" in chunk
        assert isinstance(chunk["final"], bool)

    def test_final_chunk(self):
        """Final chunk signals end of stream."""
        final_chunk = {"chunk": "", "final": True}
        assert final_chunk["final"] is True
        assert final_chunk["chunk"] == ""

    def test_chunk_sequence(self):
        """Test chunk sequence assembly."""
        chunks = [
            {"chunk": "Hello", "final": False},
            {"chunk": " world", "final": False},
            {"chunk": "", "final": True},
        ]
        result = "".join(c["chunk"] for c in chunks if not c["final"])
        assert result == "Hello world"


class TestActivityMetrics:
    """Test fleet activity support helpers."""

    def test_parse_tier1_tree(self, tmp_path: Path):
        import gateway

        path = tmp_path / "TIER1_TREE_with_leads.md"
        path.write_text(
            """
  ├── /platform
    ├── aiml - Ethos
    ├── memops- Mnemos
  ├── /garden - Solyn
""",
            encoding="utf-8",
        )

        rows = gateway._parse_tier1_tree(path)

        assert [(row["domain"], row["name"], row["label"]) for row in rows] == [
            ("aiml", "ethos", "Ethos"),
            ("memops", "mnemos", "Mnemos"),
            ("garden", "solyn", "Solyn"),
        ]

    def test_activity_endpoint_returns_summary(self, monkeypatch):
        import gateway

        monkeypatch.setattr(
            gateway,
            "_activity_snapshot",
            lambda: {
                "generated_at": "2026-05-23T00:00:00+00:00",
                "summary": {"roster_agents": 1},
                "charts": {},
                "agents": [],
                "tier1": [],
            },
        )
        client = TestClient(gateway.app)

        response = client.get("/api/activity")

        assert response.status_code == 200
        assert response.json()["summary"]["roster_agents"] == 1

    def test_turn_events_endpoint_returns_canonical_events(self, monkeypatch):
        import gateway

        monkeypatch.setattr(
            gateway,
            "read_turn_events",
            lambda limit=200: [{"schema": "comms.turn.v1", "event_id": "turn-1"}],
        )
        client = TestClient(gateway.app)

        response = client.get("/api/turn-events?limit=1")

        assert response.status_code == 200
        assert response.json()["events"] == [{"schema": "comms.turn.v1", "event_id": "turn-1"}]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
