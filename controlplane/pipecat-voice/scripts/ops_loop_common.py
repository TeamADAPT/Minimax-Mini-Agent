from __future__ import annotations

import json
import re
import sqlite3
import subprocess
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OPS_RUNTIME_DIR = ROOT / "ops" / "runtime"
USER_SYSTEMD_DIR = Path.home() / ".config" / "systemd" / "user"


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_runtime_dir() -> Path:
    OPS_RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    return OPS_RUNTIME_DIR


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(f"{path.suffix}.tmp")
    temp_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    temp_path.replace(path)


def load_nats_url() -> str:
    text = Path("/adapt/secrets/db.env").read_text(encoding="utf-8")
    match = re.search(r'^NATS_URL\s*=\s*"?([^"\n]+)"?', text, re.M)
    if not match:
        raise RuntimeError("NATS_URL not found in /adapt/secrets/db.env")
    return match.group(1).strip().strip('"')


def run_command(
    args: list[str],
    *,
    timeout: float = 10.0,
    check: bool = False,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=check,
    )


def systemctl_state(unit: str, *, user: bool = False) -> dict[str, str]:
    base = ["systemctl"]
    if user:
        base.append("--user")
    active = run_command([*base, "is-active", unit], timeout=10)
    enabled = run_command([*base, "is-enabled", unit], timeout=10)
    return {
        "active": (active.stdout or active.stderr or "unknown").strip().splitlines()[0],
        "enabled": (enabled.stdout or enabled.stderr or "unknown").strip().splitlines()[0],
    }


def service_file_text(unit: str) -> str:
    service_path = USER_SYSTEMD_DIR / unit
    if not service_path.exists():
        return ""
    return service_path.read_text(encoding="utf-8")


def service_env_flag(unit: str, key: str) -> str | None:
    text = service_file_text(unit)
    if not text:
        return None
    for line in text.splitlines():
        if not line.startswith("Environment="):
            continue
        body = line.removeprefix("Environment=").strip().strip('"')
        if "=" not in body:
            continue
        env_key, value = body.split("=", 1)
        if env_key == key:
            return value.strip().strip('"')
    return None


def window_present(window_name: str, window_class: str | None = None) -> bool:
    if window_class:
        proc = run_command(["xdotool", "search", "--class", window_class], timeout=10)
        if proc.returncode == 0 and proc.stdout.strip():
            return True
    proc = run_command(["xdotool", "search", "--name", window_name], timeout=10)
    return proc.returncode == 0 and bool(proc.stdout.strip())


def latest_open_cli_session(profile_root: Path) -> dict[str, Any] | None:
    db_path = profile_root / "state.db"
    if not db_path.exists():
        return None
    with sqlite3.connect(str(db_path), timeout=10) as conn:
        row = conn.execute(
            """
            SELECT id, started_at, message_count
            FROM sessions
            WHERE source = 'cli' AND ended_at IS NULL
            ORDER BY started_at DESC
            LIMIT 1
            """
        ).fetchone()
    if not row:
        return None
    return {
        "id": str(row[0]),
        "started_at": row[1],
        "message_count": int(row[2] or 0),
    }


def http_json(url: str, *, timeout: float = 5.0) -> dict[str, Any]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return {
                "ok": True,
                "status": response.status,
                "payload": json.loads(response.read().decode("utf-8")),
            }
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return {"ok": False, "status": exc.code, "error": body[:1000]}
    except Exception as exc:
        return {"ok": False, "status": None, "error": str(exc)}


def snapshot_age_seconds(path: Path) -> float | None:
    if not path.exists():
        return None
    return max(0.0, datetime.now(timezone.utc).timestamp() - path.stat().st_mtime)
