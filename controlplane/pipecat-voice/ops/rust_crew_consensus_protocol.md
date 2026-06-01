# Rust Crew Consensus Protocol

## 2026-05-31 17:15:18 — SIGNED_BY_AGENT

Task 39 is promoted to a Rust-owned systemd service.

## Service

- Source crate: `rust/nova-crew-consensus`
- Runtime binary: `/usr/local/bin/nova-crew-consensus`
- Unit: `nova-crew-consensus.service`
- Unit source: `systemd/nova-crew-consensus.service`
- Live namespace: `nova`
- Voters: `skipper,echo,iris,zap,forge,synergy,tecton`

## Subjects

- Propose: `nova.crew.consensus.propose`
- Vote: `nova.crew.consensus.vote.<voter>`
- Bind: `nova.crew.consensus.bind.<topic>`

## Resolution Rules

- `YES` votes count toward quorum.
- `NO` votes count against possible quorum.
- `ABSTAIN` votes are accepted but do not count toward quorum.
- The first valid vote from a voter is final for that proposal.
- `BIND` publishes immediately when `YES >= quorum`.
- `NO_BIND` publishes when quorum is mathematically impossible.
- `NO_QUORUM` publishes when timeout expires before quorum.

## Verification

- Rust gates passed:
  - `cargo fmt --check`
  - `cargo check`
  - `cargo test`
  - `cargo clippy -- -D warnings`
  - `cargo build --release`
- Real local NATS integration test passed in `tests/nats_flow.rs`.
- Live CLI proof with sourced NATS credentials:
  - `rust-live-bind-001` resolved `BIND`.
  - `rust-live-timeout-001` resolved `NO_QUORUM`.
- Live systemd service proof:
  - `rust-systemd-bind-20260531` resolved `BIND`.
  - `rust-systemd-timeout-20260531` resolved `NO_QUORUM`.

## Rollback

```bash
sudo systemctl disable --now nova-crew-consensus.service
```

No data is bound without an explicit proposal and vote flow. The service holds
active proposal state in memory only.
