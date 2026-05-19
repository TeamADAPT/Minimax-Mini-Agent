from __future__ import annotations

from pathlib import Path

from ops_loop_common import ensure_runtime_dir, http_json, now_utc, systemctl_state, write_json

OUTPUT_PATH = Path(ensure_runtime_dir()) / "pipecat_health.json"

SYSTEM_UNITS = (
    "pipecat-voice.service",
    "nats-server.service",
    "cloudflared.service",
)

USER_UNITS = (
    "pipecat-hermes-agents.service",
    "echo-tui-nats-bridge.service",
    "skipper-tui-nats-bridge.service",
    "testova-tui-nats-bridge.service",
    "latch-nats-inbox.service",
)


def main() -> None:
    system_services = {unit: systemctl_state(unit) for unit in SYSTEM_UNITS}
    user_services = {unit: systemctl_state(unit, user=True) for unit in USER_UNITS}
    payload = {
        "generated_at": now_utc(),
        "services": {
            "system": system_services,
            "user": user_services,
        },
        "gateway_health": http_json("http://127.0.0.1:18085/healthz"),
        "ops_status": http_json("http://127.0.0.1:18085/api/ops/status"),
        "nats_subscriptions": http_json("http://127.0.0.1:8223/subsz?subs=1"),
    }
    write_json(OUTPUT_PATH, payload)


if __name__ == "__main__":
    main()
