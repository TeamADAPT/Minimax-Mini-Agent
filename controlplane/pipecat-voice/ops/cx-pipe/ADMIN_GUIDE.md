# CX Pipe Admin Guide

## Purpose

This guide is for operating the live `pipe.adaptdev.ai` voice/text bridge and
its NATS-to-Hermes agent path.

## Services

Check the live service state:

```bash
systemctl is-active pipecat-voice.service cloudflared.service nats-server.service switch-agent.service
systemctl --user is-active pipecat-hermes-agents.service pipecat-roster-agents.service
```

Expected state:

- `pipecat-voice.service`: active
- `cloudflared.service`: active
- `nats-server.service`: active
- `switch-agent.service`: active
- `pipecat-hermes-agents.service`: active
- `pipecat-roster-agents.service`: inactive

## Live URLs

- App: `https://pipe.adaptdev.ai`
- Health: `https://pipe.adaptdev.ai/healthz`
- Roster: `https://pipe.adaptdev.ai/api/roster`
- Presence: `https://pipe.adaptdev.ai/api/presence`
- Profile health: `https://pipe.adaptdev.ai/api/profile-health`

## Runtime Config

The pipe service loads:

- `/adapt/secrets/db.env`
- `/adapt/secrets/m2.env`
- `/adapt/platform/novaops/controlplane/pipecat-voice/.env`

Do not print secret values into logs or docs.

Important knobs:

- `UMBRELLA_PEER=__disabled__` keeps Vox from using the old umbrella fast path.
- `NATS_REPLY_TIMEOUT=300` gives real Hermes CLI and visible Echo turns enough time.
- `GROUP_AGENT_NAMES=tecton,herald,iris,echo,vaeris,synergy,cosmos,pathfinder,zap,oracle,vox` defines the stable room roster.
- `DEFAULT_PEER=echo` routes single-agent phone/chat turns to Echo unless the caller selects another peer.
- Echo is currently served by `echo-tui-nats-bridge.service`, which serializes visible CLI delivery and returns Echo's actual assistant text to the gateway reply inbox.

## NATS Subjects

Direct routing:

```text
nova.<agent>.direct
```

Room routing:

```text
nova.<agent>.meet
```

Health checks:

```text
nova.<agent>.ping
```

The gateway publishes each room turn to each configured target and listens on a
private `_INBOX.*` reply subject for each response.

## Smoke Tests

Health:

```bash
curl -fsS https://pipe.adaptdev.ai/healthz
```

Presence:

```bash
curl -fsS https://pipe.adaptdev.ai/api/presence | python3 -m json.tool
```

Hermes-backed ping:

```bash
python3 - <<'PY'
import asyncio, re
from pathlib import Path
import nats

txt = Path('/adapt/secrets/db.env').read_text()
url = re.search(r'^NATS_URL\s*=\s*"?([^"\n]+)"?', txt, re.M).group(1).strip().strip('"')

async def main():
    nc = await nats.connect(url, name='cx-pipe-admin-smoke')
    for agent in ['tecton', 'herald', 'iris', 'echo']:
        msg = await nc.request(f'nova.{agent}.ping', b'ping', timeout=2)
        print(agent, msg.data.decode())
    await nc.drain()

asyncio.run(main())
PY
```

Group route:

```bash
curl -fsS --max-time 180 -N \
  'https://pipe.adaptdev.ai/v1/chat/completions?peer=all&channel=meet' \
  -H 'content-type: application/json' \
  --data '{"messages":[{"role":"user","content":"brief live room check"}]}'
```

Selected pair route:

```bash
curl -fsS --max-time 180 -N \
  'https://pipe.adaptdev.ai/v1/chat/completions?peer=all&channel=meet&agents=iris,echo&mode=pair' \
  -H 'content-type: application/json' \
  --data '{"messages":[{"role":"user","content":"brief pair check"}]}'
```

Moderated room route:

```bash
curl -fsS --max-time 240 -N \
  'https://pipe.adaptdev.ai/v1/chat/completions?peer=all&channel=meet&mode=moderated&moderator=echo' \
  -H 'content-type: application/json' \
  --data '{"messages":[{"role":"user","content":"brief room check, then moderator summarize"}]}'
```

## Logs

Gateway:

```bash
journalctl -u pipecat-voice.service --since '15 min ago' --no-pager
```

Hermes bridge:

```bash
journalctl --user -u pipecat-hermes-agents.service --since '15 min ago' --no-pager
```

NATS subscriptions:

```bash
python3 - <<'PY'
import json, urllib.request
j = json.load(urllib.request.urlopen('http://127.0.0.1:8223/connz?subs=1', timeout=5))
for c in j.get('connections', []):
    subs = [s for s in c.get('subscriptions_list', []) if isinstance(s, str) and s.startswith('nova.')]
    if subs:
        print(c.get('cid'), c.get('name'), sorted(subs))
PY
```

## Adding Agents Back

Only add an agent to `GROUP_AGENT_NAMES` after:

- Its Hermes profile exists under `/home/x/.hermes/profiles/<agent>`.
- `hermes -p <agent> chat -q "identify yourself" -Q --yolo --source pipe-test`
  returns successfully.
- `nova.<agent>.ping` returns `pong:<agent>:hermes`.
- The profile can answer within `HERMES_TURN_TIMEOUT`.

After editing `.env` and the user service environment, restart:

```bash
systemctl --user daemon-reload
systemctl --user restart pipecat-hermes-agents.service
sudo -n systemctl restart pipecat-voice.service
```

## Failure Modes

- **Profile says unauthorized:** AgentOps must fix provider credentials for that
  Hermes profile.
- **Request payload too large:** reduce profile context, session history, or
  prompt size before re-adding it to the room.
- **All Agents feels slow:** real Hermes CLI turns are slower than fallback
  model calls. Use selected pair or moderated mode for shorter spoken output.
- **Phone mic fails:** use the command bar; text fallback uses the same NATS
  route.

## Safety

- Do not re-enable MCP listeners for the live pipe path.
- Do not re-enable the simulated roster fallback unless explicitly testing.
- Keep the roster honest: offline profiles should show offline until AgentOps
  brings them online.
