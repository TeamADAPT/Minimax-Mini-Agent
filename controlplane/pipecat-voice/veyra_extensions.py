"""Voice gateway extensions — added by Veyra for n-voice pipeline.

These are imported by gateway.py to add:
- Agent log tailing
- Session activity feed
- Dual Deepgram key support
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

ACTIVE_NOVA_ROOT = Path("/adapt/novas/active")
NAME_RE = re.compile(r"^[a-z][a-z0-9_-]{1,30}$")


def read_agent_logs(name: str, *, lines: int = 50) -> dict[str, Any]:
    """Return the last N log lines from an agent's logs directory."""
    if not NAME_RE.match(name):
        return {
            "agent": name,
            "agent_log": [],
            "error_log": [],
            "agent_log_lines": 0,
            "error_log_lines": 0,
        }
    logs_dir = ACTIVE_NOVA_ROOT / name / "logs"
    result: dict[str, Any] = {
        "agent": name, "agent_log": [], "error_log": [],
        "agent_log_lines": 0, "error_log_lines": 0,
    }
    if not logs_dir.exists():
        return result
    for log_name, key in [("agent.log", "agent_log"), ("errors.log", "error_log")]:
        log_path = logs_dir / log_name
        if not log_path.exists():
            continue
        try:
            text = log_path.read_text(encoding="utf-8", errors="replace")
            all_lines = text.strip().split("\n")
            tail = all_lines[-lines:] if len(all_lines) > lines else all_lines
            result[key] = tail
            result[f"{key}_lines"] = len(all_lines)
        except OSError:
            continue
    return result


def read_session_activity(lines: int = 200) -> dict[str, Any]:
    """Return the last N lines from the session events JSONL file."""
    path = ACTIVE_NOVA_ROOT / "_shared" / "session_events.jsonl"
    result: dict[str, Any] = {"events": [], "total_lines": 0}
    if not path.exists():
        return result
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
        all_lines = text.strip().split("\n")
        result["total_lines"] = len(all_lines)
        tail = all_lines[-lines:] if len(all_lines) > lines else all_lines
        result["events"] = [json.loads(line) for line in tail if line.strip()]
    except Exception:
        pass
    return result


def dg_key() -> str:
    """Return the first available Deepgram API key."""
    import os
    for env_name in ("DEEPGRAM_API_KEY", "DEEPGRAM_API_KEY_nc"):
        key = os.environ.get(env_name, "").strip()
        if key:
            return key
    return ""
