# Completion Report

## 2026-05-18 15:13:33 — SIGNED_BY_AGENT

Completed `03-echo-reply-capture-session-watcher`.

Changes:

- Added Echo CLI session state capture before visible delivery:
  - active CLI session id
  - session `message_count`
  - max message row id for the active session
- Flattened NATS prompt envelopes into a single visible TUI input line so Hermes stores one user row containing the subject, sender, event id, and message instead of splitting multiline input into separate rows.
- Added bounded post-turn assistant polling with `ECHO_TUI_REPLY_CAPTURE_TIMEOUT`, default `30` seconds.
- Extracted the assistant row from `/home/x/.hermes/profiles/echo/state.db` after the stamped NATS prompt.
- Changed `reply_to` publishing from delivery acknowledgement to Echo's actual assistant text.
- Added `reply_captured` trace events with session id, assistant message id, and response character count.
- Added `scripts/smoke_echo_tui_reply_capture.py` for short and long reply-capture proofs.

Verification:

- `python3 -m py_compile scripts/echo_tui_nats_bridge.py scripts/smoke_echo_tui_reply_capture.py`: passed.
- `systemctl --user restart echo-tui-nats-bridge.service`: succeeded.
- `systemctl --user is-active echo-tui-nats-bridge.service`: `active`.
- Short proof event `reply-short-6576abbfdf` returned Echo's actual answer text containing `REPLY SHORT DONE`.
- Long proof event `reply-long-56f8817852` returned Echo's actual 1,607-character answer text containing `REPLY LONG DONE`.
- Echo DB evidence:
  - user row `960` contains event id `reply-short-6576abbfdf`
  - assistant row `961` contains the short returned answer
  - user row `962` contains event id `reply-long-56f8817852`
  - assistant row `963` contains the long returned answer
- Bridge journal showed `reply_captured` and `completed` for both proof events.
- Logs for the successful proof window showed no `Interrupted during API call`, `HTTP 401`, provider fallback, token revocation, warning, or error.
- Screenshot captured at `/tmp/echo-reply-capture-20260518-1514.png`.

Failure found and fixed:

- First long proof attempt showed multiline xdotool input could split the envelope into multiple user rows. The bridge now compacts whitespace before typing, and the successful proof confirmed the full event id and message are stored in one user row.

Residual risk:

- This is still an X11/TUI bridge. The native Hermes NATS adapter in `04-native-hermes-nats-adapter-spike` remains the target for a non-desktop production path.
