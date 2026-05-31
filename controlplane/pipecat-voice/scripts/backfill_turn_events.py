#!/usr/bin/env python3
"""Backfill canonical CommsOps turn events from CX Pipe room history."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from turn_events import DEFAULT_TURN_EVENTS_PATH, backfill_room_history  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--room-history",
        type=Path,
        default=ROOT / "ops" / "cx-pipe" / "room_history.jsonl",
        help="Source CX Pipe room history JSONL path.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_TURN_EVENTS_PATH,
        help="Destination canonical turn event JSONL path.",
    )
    parser.add_argument("--limit", type=int, default=None, help="Only backfill newest N rows.")
    parser.add_argument("--dry-run", action="store_true", help="Count rows without writing.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    counts = backfill_room_history(
        args.room_history,
        args.output,
        limit=args.limit,
        dry_run=args.dry_run,
    )
    print(json.dumps(counts, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
