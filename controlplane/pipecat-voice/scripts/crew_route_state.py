from __future__ import annotations

from pathlib import Path

from ops_loop_common import (
    ensure_runtime_dir,
    latest_open_cli_session,
    now_utc,
    service_env_flag,
    systemctl_state,
    window_present,
    write_json,
)

OUTPUT_PATH = Path(ensure_runtime_dir()) / "crew_route_state.json"

AGENTS = (
    {
        "name": "echo",
        "unit": "echo-tui-nats-bridge.service",
        "window": "Echo CLI",
        "profile_root": Path("/home/x/.hermes/profiles/echo"),
    },
    {
        "name": "skipper",
        "unit": "skipper-tui-nats-bridge.service",
        "window": "Skipper CLI",
        "profile_root": Path("/home/x/.hermes/profiles/skipper"),
    },
    {
        "name": "testova",
        "unit": "testova-tui-nats-bridge.service",
        "window": "Testova CLI",
        "profile_root": Path("/home/x/.hermes/profiles/testova"),
    },
)


def route_mode(unit: str, window_name: str) -> str:
    if window_present(window_name):
        return "visible"
    if service_env_flag(unit, "ECHO_TUI_ALLOW_CLI_FALLBACK") == "1":
        return "fallback-cli"
    return "degraded"


def main() -> None:
    agents: list[dict[str, object]] = []
    for agent in AGENTS:
        unit = str(agent["unit"])
        window_name = str(agent["window"])
        profile_root = Path(agent["profile_root"])
        agents.append(
            {
                "name": agent["name"],
                "subject": f"nova.{agent['name']}.direct",
                "service": {"unit": unit, **systemctl_state(unit, user=True)},
                "window": {
                    "name": window_name,
                    "present": window_present(window_name),
                },
                "route_mode": route_mode(unit, window_name),
                "fallback_enabled": service_env_flag(unit, "ECHO_TUI_ALLOW_CLI_FALLBACK") == "1",
                "delivery_timeout_seconds": service_env_flag(unit, "ECHO_TUI_DELIVERY_TIMEOUT"),
                "latest_open_cli_session": latest_open_cli_session(profile_root),
            }
        )

    latch_unit = "latch-nats-inbox.service"
    payload = {
        "generated_at": now_utc(),
        "agents": agents,
        "operator_inbox": {
            "name": "latch",
            "subject": "nova.latch.direct",
            "service": {"unit": latch_unit, **systemctl_state(latch_unit, user=True)},
            "route_mode": "inbox",
        },
    }
    write_json(OUTPUT_PATH, payload)


if __name__ == "__main__":
    main()
