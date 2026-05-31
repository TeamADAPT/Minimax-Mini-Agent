# pipecat-voice

CommsOps control plane for speech, text, room routing, NATS delivery, and Hermes
agent sessions behind **https://pipe.adaptdev.ai**.

```
Browser/Phone -> Voice Gateway -> STT/TTS provider
                         |
                         v
                     NATS request/reply
                         |
                         v
        nova.<agent>.<runtime>.<channel> -> Hermes/Nova agent
                         |
                         v
              transcript, metrics, memory handoff
```

## Subjects

| Subject                              | Direction | Purpose |
| ------------------------------------ | --------- | ------- |
| `nova.<agent>.<runtime>.direct`      | publish   | 1:1 turn to one agent/runtime |
| `nova.<agent>.<runtime>.meet`        | publish   | room or group turn to one agent/runtime |
| `nova.<agent>.<runtime>.ping`        | request   | health check for one runtime owner |
| `_INBOX.<nuid>`                      | subscribe | per-request streaming reply inbox |

Runtime labels are `tui`, `hermes`, `fresh`, and `rust`. The browser can also
request `auto`, which lets the gateway select the configured default for the
chosen agent.

Default peer selection is controlled by gateway configuration and the roster.
The phone/browser can override peer, channel, and runtime through the UI or
query parameters.

## Reply contract (agent side)

The agent receives this envelope on its runtime subject:

```json
{
  "from": "chase",
  "to":   "echo",
  "type": "voice",
  "message": "hello echo",
  "timestamp": "2026-05-07T09:42:00Z",
  "reply_to": "_INBOX.abc123"
}
```

To stream a spoken reply, publish chunks on `reply_to`:

```json
{"chunk": "Hi! ",        "final": false}
{"chunk": "How can I... ", "final": false}
{"chunk": "",            "final": true}
```

Streaming replies should publish chunks on `reply_to`. Legacy non-runtime
subjects are historical compatibility paths and should not be used for new
CommsOps promotion work.

## CommsOps Ownership

CommsOps owns the voice, text, NATS routing, Hermes session delivery,
transcript, and communication observability surfaces for this repo. The charter
and current promotion gates live in:

- `ops/COMMSOPS_CHARTER.md`
- `ops/COMMSOPS_STATUS.md`

## Service ops

```bash
# status / logs
systemctl status pipecat-voice
journalctl -u pipecat-voice -f

# restart after editing bot.py
sudo systemctl restart pipecat-voice

# disable
sudo systemctl disable --now pipecat-voice
```

The unit reads env from `/adapt/secrets/db.env`, `/adapt/secrets/m2.env`,
and `./.env` (in that order; later wins). Required:

| Var                | Source            | Notes                                  |
| ------------------ | ----------------- | -------------------------------------- |
| `NATS_URL`         | `db.env`          | full URL incl. user:pass               |
| `DEEPGRAM_API_KEY` | `m2.env`          | primary STT + TTS                      |
| `GROQ_API_KEY`     | `m2.env` (opt)    | fallback STT (Whisper)                 |
| `ELEVENLABS_API_KEY` | `m2.env` (opt)  | fallback TTS                           |
| `SELF_AGENT`       | `.env`            | default `chase`                        |
| `DEFAULT_PEER`     | `.env`            | default `echo` if URL has no `?to=`    |

## Cloudflare

Tunnel `vertex-ai` (UUID `66dd75ad-6556-4d1f-8a57-bc4d15e890f9`) routes
`pipe.adaptdev.ai` → `localhost:18085`. Ingress lives in
`~/.cloudflared/config.yml`; DNS CNAME `pipe → <tunnel>.cfargotunnel.com`
(proxied) was created via the Global API key.

## Health & smoke test

```bash
curl https://pipe.adaptdev.ai/healthz                  # {"status":"ok"}
python3 -m http.test_echo_agent                        # see scripts/echo_test.py
```

A reference echo agent that demonstrates the streaming contract is in
`scripts/echo_agent.py`.

## Overnight control loops

The control plane includes low-cost overnight loops managed through
`systemd --user`:

- `nova-crew-heartbeat.timer` writes `ops/runtime/crew_heartbeat.json`
- `nova-crew-route-state.timer` writes `ops/runtime/crew_route_state.json`
- `nova-pipecat-health.timer` writes `ops/runtime/pipecat_health.json`
- `nova-crew-watchdog.timer` restarts timers and bridge services if they drift

Install the unit files from `systemd/` into `~/.config/systemd/user/`, then run:

```bash
systemctl --user daemon-reload
systemctl --user enable --now \
  nova-crew-heartbeat.timer \
  nova-crew-route-state.timer \
  nova-pipecat-health.timer \
  nova-crew-watchdog.timer
```
