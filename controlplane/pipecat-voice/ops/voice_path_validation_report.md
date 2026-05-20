# Voice Path Validation Report

## 2026-05-19 22:52:13 — SIGNED_BY_AGENT

## Summary

Task `22-voice-path-validation` passed the three-turn end-to-end voice
acceptance gate after refreshing the stale gateway service and using a browser-
equivalent continuous microphone stream.

Validated path:

```text
synthetic PCM speech -> /ws/voice -> Deepgram STT -> public HTTPS think endpoint
-> /v1/chat/completions -> NATS -> Vox reply -> Deepgram TTS -> binary audio
```

## Service State

- `pipecat-voice.service`: active after targeted restart.
- Gateway bind: `127.0.0.1:18085`.
- NATS connected on startup.
- `/healthz`: `200`.
- `/token`: `200`, token present.
- `/api/session-state`: `200` after restart.
- `/api/direct-nats-session-hook`: `200`, dry-run mode.

## Successful Voice Turns

All three turns used synthesized `espeak` audio converted to 16 kHz mono
linear16 PCM and streamed through the live `/ws/voice` proxy with continuous
silence frames, matching browser microphone behavior.

| Turn | Peer | Result | Latency | STT/assistant evidence | TTS evidence |
| --- | --- | --- | --- | --- | --- |
| 1 | `vox` | pass | `32.25s` | User `ConversationText`; assistant: `Voice class validation confirmed, Vox online and clear.` | `226` binary frames, `216960` bytes, `AgentAudioDone` |
| 2 | `vox` | pass | `16.63s` | User `ConversationText`; assistant: `Voice mask validation two confirmed, signal is clean.` | `186` binary frames, `178560` bytes, `AgentAudioDone` |
| 3 | `vox` | pass | `39.80s` | User `ConversationText`; assistant: `Voice mask is clear, all channels open and ready.` | `182` binary frames, `174720` bytes, `AgentAudioDone` |

Summary:

```text
successful_voice_turns=3 total=3
```

## Failure Classes Found

| Class | Evidence | Root cause | Recovery |
| --- | --- | --- | --- |
| `stale-gateway-code` | `/api/session-state` returned `404` while committed code had the endpoint. | Live `pipecat-voice.service` had not been restarted after recent gateway changes. | Restarted only `pipecat-voice.service`; endpoint returned `200`. |
| `deepgram-invalid-local-think-endpoint` | Deepgram error: `Endpoints must use https or wss. Invalid endpoint: http://127.0.0.1:18085/...` | Voice Agent rejects local `http` think endpoints. | Use public `https://pipe.adaptdev.ai/v1/chat/completions?...` in settings. |
| `client-audio-stream-ended-before-think` | Deepgram emitted `CLIENT_MESSAGE_TIMEOUT` after user transcription when the script stopped sending audio frames. | Test harness did not behave like a live browser microphone stream. | Continue sending silence frames while waiting for agent/TTS completion. |
| `slow-think-request` | Deepgram warnings at 5s intervals on all accepted voice turns. | NATS-backed nova reply latency often exceeds Deepgram's fast-response threshold. | The path still completed, but latency should be tracked; faster voice-specific responder or shorter prompts would reduce warning churn. |

## Non-Audio Think-Step Checks

Before full audio validation, the OpenAI-compatible think endpoint passed three
bounded SSE turns:

| Turn | Peer | Latency | Reply |
| --- | --- | --- | --- |
| 1 | `iris` | `9.62s` | `Voicepath-one confirmed on the bridge.` |
| 2 | `iris` | `32.96s` | `Voicepath-two confirmed on the Iris channel.` |
| 3 | `vox` | `19.10s` | `Voicepath-three confirmed, Vox is live on the bridge.` |

## Notes

- Echo and Skipper remain ping-healthy but assignment reply capture degraded from
  the earlier team dispatch. Task 22 used `vox`/`iris` routes for reliable voice
  acceptance and did not change live direct subject ownership.
- Testova remains held/degraded; no Testova proof prompts were sent.
- No Docker or venv was used.

**— SIGNED_BY_AGENT**
