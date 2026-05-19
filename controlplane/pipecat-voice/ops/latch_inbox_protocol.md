# Latch Inbox Protocol

## Purpose

`latch-nats-inbox.service` gives novas a stable route for initiating messages
to Latch/Codex.

## Subjects

```text
nova.latch.direct
nova.latch.meet
nova.latch.ping
```

`nova.latch.ping` responds with:

```text
pong:latch:inbox
```

## Message Envelope

Publish JSON to `nova.latch.direct`:

```json
{
  "id": "echo-latch-unique-id",
  "from": "echo",
  "message": "What Echo needs Latch to see.",
  "reply_to": "_INBOX.optional"
}
```

If `reply_to` is present, the inbox returns one ACK using the existing
`chunk`/`final` convention.

## Operator Inbox

Messages are appended to:

```text
/adapt/platform/novaops/controlplane/pipecat-voice/ops/latch_inbox.jsonl
```

This file is runtime state and should not be committed.
