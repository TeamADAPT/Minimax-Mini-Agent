from __future__ import annotations

from pathlib import Path

from ops_loop_common import (
    ensure_runtime_dir,
    now_utc,
    run_command,
    snapshot_age_seconds,
    systemctl_state,
    write_json,
)

OUTPUT_PATH = Path(ensure_runtime_dir()) / "crew_watchdog.json"

TIMERS = (
    "nova-crew-heartbeat.timer",
    "nova-crew-route-state.timer",
    "nova-pipecat-health.timer",
)

SERVICES = (
    "echo-tui-nats-bridge.service",
    "skipper-tui-nats-bridge.service",
    "testova-tui-nats-bridge.service",
    "latch-nats-inbox.service",
)

SNAPSHOTS = (
    ("crew_heartbeat.json", "nova-crew-heartbeat.service", 900),
    ("crew_route_state.json", "nova-crew-route-state.service", 900),
    ("pipecat_health.json", "nova-pipecat-health.service", 600),
)


def ensure_timer(unit: str, actions: list[str]) -> None:
    state = systemctl_state(unit, user=True)
    if state["enabled"] != "enabled":
        run_command(["systemctl", "--user", "enable", unit], timeout=15)
        actions.append(f"enabled {unit}")
    if state["active"] != "active":
        run_command(["systemctl", "--user", "start", unit], timeout=15)
        actions.append(f"started {unit}")


def ensure_service(unit: str, actions: list[str]) -> None:
    state = systemctl_state(unit, user=True)
    if state["active"] in {"inactive", "failed", "deactivating"}:
        run_command(["systemctl", "--user", "restart", unit], timeout=30)
        actions.append(f"restarted {unit}")


def ensure_snapshot(
    filename: str,
    service_unit: str,
    max_age_seconds: int,
    actions: list[str],
) -> None:
    snapshot_path = ensure_runtime_dir() / filename
    age = snapshot_age_seconds(snapshot_path)
    if age is None or age > max_age_seconds:
        run_command(["systemctl", "--user", "start", service_unit], timeout=30)
        actions.append(f"refreshed {filename}")


def main() -> None:
    actions: list[str] = []
    for timer in TIMERS:
        ensure_timer(timer, actions)
    for service in SERVICES:
        ensure_service(service, actions)
    for filename, service_unit, max_age_seconds in SNAPSHOTS:
        ensure_snapshot(filename, service_unit, max_age_seconds, actions)

    payload = {
        "generated_at": now_utc(),
        "actions": actions,
        "summary": "steady" if not actions else "corrected",
    }
    write_json(OUTPUT_PATH, payload)


if __name__ == "__main__":
    main()
