# Secret Guardrail

## 2026-05-18 21:34:03 — SIGNED_BY_AGENT

`scripts/scan_tracked_secrets.py` is the local branch guardrail after the scrub.
It scans tracked files only, never prints matched values, and exits non-zero on
high-risk secret classes such as provider keys, GitHub tokens, authenticated
NATS/Redis URLs, bearer headers, and tracked symlinks into `/adapt/secrets/`.

Usage:

```bash
python3 /adapt/platform/novaops/controlplane/pipecat-voice/scripts/scan_tracked_secrets.py \
  --repo /adapt/platform/novaops/controlplane
```

Policy:

- Run before commits that touch configs, docs, profile exports, or ops scripts.
- Treat any finding as a stop condition until the file is redacted or removed.
- Do not use this as credential rotation proof; rotation remains a separate task.

— SIGNED_BY_AGENT
