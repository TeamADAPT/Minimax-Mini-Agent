# Pipecat Direct NATS Session Hook

## 2026-05-19 22:29:33 — SIGNED_BY_AGENT

## Summary

Task 32 added the first guarded hook for exposing active NATS-backed session
targets to the pipecat voice gateway without changing the default voice path.
The hook is read-only plus dry-run by default. It does not publish to NATS unless
a later task explicitly enables live behavior and Task 22 validates end-to-end
voice turns.

## Files

- `direct_nats_session_hook.py`
- `gateway.py`
- `tests/test_direct_nats_session_hook.py`

## HTTP Surface

`GET /api/direct-nats-session-hook`

Returns:

- current mode: `dry-run` by default
- explicit guard env: `PIPECAT_DIRECT_NATS_SESSION_HOOK_ENABLED`
- default voice behavior: `preserved`
- route targets derived from `/api/session-state`
- per-target route posture, bridge owner, latest proof, reply mode, and blockers

`POST /api/direct-nats-session-hook/dry-run`

Input:

```json
{
  "target": "echo",
  "message": "operator text",
  "from": "pipecat"
}
```

Returns the NATS subject and envelope that would be sent, but with:

```json
{
  "published": false,
  "reply_to": "_DRY_RUN_REPLY_INBOX_"
}
```

## Guardrails

- No default voice route changed.
- No live NATS publish occurs in the dry-run endpoint.
- Live publishing remains disabled unless
  `PIPECAT_DIRECT_NATS_SESSION_HOOK_ENABLED` is explicitly set.
- The hook reads route/session state from existing runtime snapshots through
  `build_session_state`.
- Testova is surfaced as guarded with `operator-hold` while the hold remains
  active.
- Target names and empty messages are rejected before any publish path could be
  reached.
- Existing `echo-tui-nats-bridge.service` and `skipper-tui-nats-bridge.service`
  remain the live direct subject owners.

## Failure Classes

| Code | Meaning |
| --- | --- |
| `invalid target name` | Target name failed Nova route naming rules. |
| `unknown target` | Target is not present in current route-state targets. |
| `message must not be empty` | Dry-run request did not provide a usable prompt. |
| `bridge-not-active` | Route-state reports the bridge service is not active. |
| `route-health-<state>` | Route-state reports a non-healthy route. |
| `route-mode-<state>` | Route-state reports a non-visible-ready mode. |
| `operator-hold` | Target is held by operator instruction. |

## Verification

```bash
python3 -m py_compile gateway.py direct_nats_session_hook.py tests/test_direct_nats_session_hook.py
pytest -q tests/test_direct_nats_session_hook.py tests/test_session_state_api.py tests/test_gateway.py
```

Result:

```text
22 passed in 0.67s
```

Additional FastAPI TestClient smoke confirmed:

```text
GET /api/direct-nats-session-hook -> 200
POST /api/direct-nats-session-hook/dry-run -> 200, published=false, subject=nova.echo.direct
```

## Next Gate

Task 22 must validate real voice turns before this hook can become a default or
live-publishing path. Until then, it is an inspection and dry-run surface only.

**— SIGNED_BY_AGENT**
