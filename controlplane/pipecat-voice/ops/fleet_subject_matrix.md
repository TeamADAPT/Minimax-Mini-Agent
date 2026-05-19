# Fleet Subject Matrix

## 2026-05-18 23:10:48 — SIGNED_BY_AGENT

Updated after moving Skipper collaboration from the hidden profile-backed bridge
to a visible CLI-backed bridge.

| Nova | Profile config | Active dir | Provider | Model | Subject owner | Ping | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| skipper | yes | yes | nvidia | qwen/qwen3.5-397b-a17b | `skipper-tui-nats-bridge.service` | `pong:skipper:tui` | Visible proof `skipper-visible-proof-29ca9f7c` returned `SKIPPER VISIBLE OK`. |

Service ownership after visible Skipper bridge:

- `skipper-tui-nats-bridge.service`: active; owns `nova.skipper.direct`, `nova.skipper.meet`, `nova.skipper.ping`.
- `pipecat-hermes-agents.service`: active; owns `tecton`, `herald`, `iris`, `vaeris`, `synergy`, `cosmos`, `pathfinder`, `zap`, `oracle`, and `vox`.
- `echo-tui-nats-bridge.service`: active; owns `nova.echo.direct`, `nova.echo.meet`, `nova.echo.ping`.

## 2026-05-18 21:12:26 — SIGNED_BY_AGENT

Updated after adding Skipper to `pipecat-hermes-agents.service`.

| Nova | Profile config | Active dir | Provider | Model | Subject owner | Ping | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| echo | yes | yes | openai-codex | gpt-5.4-mini | `echo-tui-nats-bridge.service` | `pong:echo:tui` | Visible bridge is active rollback owner. |
| tecton | yes | yes | nvidia | moonshotai/kimi-k2.6 | `pipecat-hermes-agents.service` | `pong:tecton:hermes` | Profile-backed Hermes bridge. |
| herald | yes | yes | nvidia | nvidia/nemotron-4-340b-instruct | `pipecat-hermes-agents.service` | `pong:herald:hermes` | Profile-backed Hermes bridge. |
| iris | yes | yes | nvidia | deepseek-ai/deepseek-v4-flash | `pipecat-hermes-agents.service` | `pong:iris:hermes` | Profile-backed Hermes bridge. |
| vaeris | yes | yes | nvidia | moonshotai/kimi-k2.6 | `pipecat-hermes-agents.service` | `pong:vaeris:hermes` | Profile-backed Hermes bridge. |
| synergy | yes | yes | nvidia | deepseek-ai/deepseek-v4-flash | `pipecat-hermes-agents.service` | `pong:synergy:hermes` | Profile-backed Hermes bridge. |
| cosmos | yes | yes | nvidia | z-ai/glm-5.1 | `pipecat-hermes-agents.service` | `pong:cosmos:hermes` | Profile-backed Hermes bridge. |
| pathfinder | yes | yes | nvidia | z-ai/glm-5.1 | `pipecat-hermes-agents.service` | `pong:pathfinder:hermes` | Profile-backed Hermes bridge. |
| zap | yes | yes | nvidia | z-ai/glm-5.1 | `pipecat-hermes-agents.service` | `pong:zap:hermes` | Profile-backed Hermes bridge. |
| oracle | yes | yes | nvidia | z-ai/glm-5.1 | `pipecat-hermes-agents.service` | `pong:oracle:hermes` | Profile-backed Hermes bridge. |
| vox | yes | yes | nvidia | z-ai/glm-5.1 | `pipecat-hermes-agents.service` | `pong:vox:hermes` | Profile-backed Hermes bridge. |
| skipper | yes | yes | nvidia | qwen/qwen3.5-397b-a17b | `pipecat-hermes-agents.service` | `pong:skipper:hermes` | Direct proof `skipper-proof-0cf7238c` returned `SKIPPER NATS OK`. |
| switch | no | no | n/a | n/a | `switch_agent.py` PID `2689` | `pong` | Router service, not a Hermes profile-backed nova. |

Service ownership after Skipper enablement:

- `echo-tui-nats-bridge.service`: active; owns `nova.echo.direct`, `nova.echo.meet`, `nova.echo.ping`.
- `pipecat-hermes-agents.service`: active; owns `tecton`, `herald`, `iris`, `vaeris`, `synergy`, `cosmos`, `pathfinder`, `zap`, `oracle`, `vox`, and `skipper`.
- `switch_agent.py`: active; owns `nova.switch.direct` and `nova.switch.ping`.
- `pipecat-roster-agents.service`: disabled and inactive; previous fallback duplicate owner removed.

## 2026-05-18 15:27:05 — SIGNED_BY_AGENT

Validated after stopping the superseded fallback `pipecat-roster-agents.service`.

| Nova | Profile config | Active dir | Provider | Model | Subject owner | Ping | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| echo | yes | yes | openai-codex | gpt-5.4-mini | `echo-tui-nats-bridge.service` | `pong:echo:tui` | Visible bridge is active rollback owner. |
| tecton | yes | yes | nvidia | moonshotai/kimi-k2.6 | `pipecat-hermes-agents.service` | `pong:tecton:hermes` | Profile-backed Hermes bridge. |
| herald | yes | yes | nvidia | nvidia/nemotron-4-340b-instruct | `pipecat-hermes-agents.service` | `pong:herald:hermes` | Profile-backed Hermes bridge. |
| iris | yes | yes | nvidia | deepseek-ai/deepseek-v4-flash | `pipecat-hermes-agents.service` | `pong:iris:hermes` | Profile-backed Hermes bridge. |
| vaeris | yes | yes | nvidia | moonshotai/kimi-k2.6 | `pipecat-hermes-agents.service` | `pong:vaeris:hermes` | Profile-backed Hermes bridge. |
| synergy | yes | yes | nvidia | deepseek-ai/deepseek-v4-flash | `pipecat-hermes-agents.service` | `pong:synergy:hermes` | Profile-backed Hermes bridge. |
| cosmos | yes | yes | nvidia | z-ai/glm-5.1 | `pipecat-hermes-agents.service` | `pong:cosmos:hermes` | Profile-backed Hermes bridge. |
| pathfinder | yes | yes | nvidia | z-ai/glm-5.1 | `pipecat-hermes-agents.service` | `pong:pathfinder:hermes` | Profile-backed Hermes bridge. |
| zap | yes | yes | nvidia | z-ai/glm-5.1 | `pipecat-hermes-agents.service` | `pong:zap:hermes` | Profile-backed Hermes bridge. |
| oracle | yes | yes | nvidia | z-ai/glm-5.1 | `pipecat-hermes-agents.service` | `pong:oracle:hermes` | Profile-backed Hermes bridge. |
| vox | yes | yes | nvidia | z-ai/glm-5.1 | `pipecat-hermes-agents.service` | `pong:vox:hermes` | Profile-backed Hermes bridge. |
| switch | no | no | n/a | n/a | `switch_agent.py` PID `2689` | `pong` | Router service, not a Hermes profile-backed nova. |
| skipper | yes | yes | nvidia | qwen/qwen3.5-397b-a17b | unassigned | no response | Profile exists, but no active NATS owner is configured in the current bridge roster. |

Service ownership after fix:

- `echo-tui-nats-bridge.service`: active; owns `nova.echo.direct`, `nova.echo.meet`, `nova.echo.ping`.
- `pipecat-hermes-agents.service`: active; owns `tecton`, `herald`, `iris`, `vaeris`, `synergy`, `cosmos`, `pathfinder`, `zap`, `oracle`, and `vox`.
- `switch_agent.py`: active; owns `nova.switch.direct` and `nova.switch.ping`.
- `pipecat-roster-agents.service`: disabled and inactive; previous fallback duplicate owner removed.

Superseded note:

- Skipper was unassigned at this timestamp. That changed at `2026-05-18 21:12:26 — SIGNED_BY_AGENT`.
