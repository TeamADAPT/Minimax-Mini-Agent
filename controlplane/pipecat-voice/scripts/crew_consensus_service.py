"""Crew Consensus Service.

Listens on nova.crew.consensus.propose, collects votes from crew members,
and publishes binding decisions when quorum is reached or timeout expires.

Usage: SUBJECT_NS=nova python3 scripts/crew_consensus_service.py
"""
from __future__ import annotations

import asyncio
import json
import os
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import nats
from loguru import logger

NS = os.environ.get("SUBJECT_NS", "nova")
EXPECTED_VOTERS_KEY = "CONSENSUS_VOTERS"
DEFAULT_VOTERS = "skipper,echo,iris,zap,forge,synergy,tecton"
VOTERS = {
    v.strip()
    for v in os.environ.get(EXPECTED_VOTERS_KEY, DEFAULT_VOTERS).split(",")
    if v.strip()
}


@dataclass
class Proposal:
    topic: str
    proposer: str
    proposal_id: str
    evidence: str = ""
    quorum: int = 3
    timeout_seconds: int = 120
    created_at: float = field(default_factory=time.time)
    votes: dict[str, dict] = field(default_factory=dict)

    def is_expired(self) -> bool:
        return time.time() - self.created_at > self.timeout_seconds

    def yes_count(self) -> int:
        return sum(1 for v in self.votes.values() if v.get("decision") == "YES")

    def binding_reached(self) -> bool:
        return self.yes_count() >= self.quorum


@dataclass
class ConsensusState:
    active: Optional[Proposal] = None
    decided: dict[str, dict] = field(default_factory=dict)  # topic -> binding result


async def _load_nats_url() -> str:
    if url := os.environ.get("NATS_URL"):
        return url
    text = Path("/adapt/secrets/db.env").read_text(encoding="utf-8")
    m = re.search(r'^NATS_URL\s*=\s*"([^"\n]+)"', text, re.M)
    if not m:
        raise RuntimeError("NATS_URL not found")
    return m.group(1).strip().strip('"') or "nats://127.0.0.1:4222"


async def publish_result(nc: nats.NATSClient, topic: str, result: dict) -> None:
    await nc.publish(
        f"{NS}.crew.consensus.bind.{topic}",
        json.dumps(result, default=str).encode(),
    )
    logger.info(f"consensus bound {topic}: {result}")


async def handle_proposal(nc: nats.NATSClient, state: ConsensusState, msg) -> None:
    try:
        payload = json.loads(msg.data.decode())
    except Exception as exc:
        logger.warning(f"non-JSON proposal payload: {exc}")
        return

    proposal_id = payload.get("proposal_id") or f"{payload.get('topic')}:{payload.get('proposer')}"
    proposal = Proposal(
        topic=payload["topic"],
        proposer=payload.get("proposer", "?"),
        proposal_id=proposal_id,
        evidence=payload.get("evidence", ""),
        quorum=int(payload.get("quorum", 3)),
        timeout_seconds=int(payload.get("timeout_seconds", 120)),
    )
    state.active = proposal
    logger.info(
        f"proposal {proposal_id} active: topic={proposal.topic} "
        f"quorum={proposal.quorum} voters={list(VOTERS)}"
    )

    # Poll for votes or expiry
    deadline = time.time() + proposal.timeout_seconds
    while time.time() < deadline:
        if state.active is None:
            logger.info(f"proposal {proposal_id} superseded — aborting")
            return
        if proposal.binding_reached():
            result = {
                "proposal_id": proposal_id,
                "topic": proposal.topic,
                "decision": "BIND",
                "quorum": proposal.quorum,
                "yes_votes": proposal.yes_count(),
                "voters": list(proposal.votes.keys()),
                "bound_at": datetime.now(timezone.utc).isoformat(),
            }
            await publish_result(nc, proposal.topic, result)
            state.decided[proposal.topic] = result
            state.active = None
            return
        await asyncio.sleep(2)

    # Timed out
    result = {
        "proposal_id": proposal_id,
        "topic": proposal.topic,
        "decision": "NO_QUORUM",
        "quorum": proposal.quorum,
        "yes_votes": proposal.yes_count(),
        "voters": list(proposal.votes.keys()),
        "reason": f"timeout ({proposal.timeout_seconds}s) expired without quorum",
        "bound_at": datetime.now(timezone.utc).isoformat(),
    }
    await publish_result(nc, proposal.topic, result)
    state.decided[proposal.topic] = result
    state.active = None


async def handle_vote(nc: nats.NATSClient, state: ConsensusState, voter: str, msg) -> None:
    if state.active is None:
        logger.debug(f"vote from {voter} but no active proposal — ignored")
        return
    try:
        payload = json.loads(msg.data.decode())
    except Exception:
        return
    state.active.votes[voter] = {
        "decision": payload.get("decision", "ABSTAIN").upper(),
        "reasoning": payload.get("reasoning", ""),
        "received_at": datetime.now(timezone.utc).isoformat(),
    }
    yes = state.active.yes_count()
    total = len(state.active.votes)
    logger.info(f"vote from {voter}: {payload.get('decision')} — {yes}/{state.active.quorum} yes ({total} total votes)")


async def on_propose(nc: nats.NATSClient, state: ConsensusState, msg) -> None:
    await handle_proposal(nc, state, msg)


async def on_vote_iris(nc: nats.NATSClient, state: ConsensusState, msg) -> None:
    await handle_vote(nc, state, "iris", msg)


async def on_vote_zap(nc: nats.NATSClient, state: ConsensusState, msg) -> None:
    await handle_vote(nc, state, "zap", msg)


async def on_vote_forge(nc: nats.NATSClient, state: ConsensusState, msg) -> None:
    await handle_vote(nc, state, "forge", msg)


async def on_vote_synergy(nc: nats.NATSClient, state: ConsensusState, msg) -> None:
    await handle_vote(nc, state, "synergy", msg)


async def on_vote_tecton(nc: nats.NATSClient, state: ConsensusState, msg) -> None:
    await handle_vote(nc, state, "tecton", msg)


async def on_vote_skipper(nc: nats.NATSClient, state: ConsensusState, msg) -> None:
    await handle_vote(nc, state, "skipper", msg)


async def on_vote_echo(nc: nats.NATSClient, state: ConsensusState, msg) -> None:
    await handle_vote(nc, state, "echo", msg)


async def main() -> None:
    state = ConsensusState()
    nc = await nats.connect(await _load_nats_url())

    await nc.subscribe(f"{NS}.crew.consensus.propose", cb=on_propose)
    for voter in VOTERS:
        await nc.subscribe(
            f"{NS}.crew.consensus.vote.{voter}",
            cb={
                "iris": on_vote_iris,
                "zap": on_vote_zap,
                "forge": on_vote_forge,
                "synergy": on_vote_synergy,
                "tecton": on_vote_tecton,
                "skipper": on_vote_skipper,
                "echo": on_vote_echo,
            }.get(voter),
        )

    logger.info(f"crew consensus service ready — voters={sorted(VOTERS)}")
    logger.info("subjects: nova.*.crew.consensus.{propose,vote.<name>,bind.<topic>}")
    await asyncio.Future()  # run forever


if __name__ == "__main__":
    asyncio.run(main())
