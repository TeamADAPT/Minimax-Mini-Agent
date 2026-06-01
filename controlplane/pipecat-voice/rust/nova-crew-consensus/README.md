# Nova Crew Consensus

Rust NATS service for the Nova crew `propose -> vote -> bind` protocol.

## Subjects

- `nova.crew.consensus.propose`
- `nova.crew.consensus.vote.<voter>`
- `nova.crew.consensus.bind.<topic>`

## Runtime

The service is systemd-managed and system-level. It does not use Docker or a
Python virtual environment.

```bash
cargo build --release
/usr/local/bin/nova-crew-consensus --namespace nova serve
```

## Bounded Proof

```bash
/usr/local/bin/nova-crew-consensus --namespace testnova prove \
  --topic deploy-rust-bridge-v1 \
  --proposal-id rust-proof-001 \
  --quorum 2 \
  --yes-voters skipper,echo,synergy
```

The proof publishes proposal/vote envelopes over real NATS and prints the bind
resolution JSON. No credentials are printed.
