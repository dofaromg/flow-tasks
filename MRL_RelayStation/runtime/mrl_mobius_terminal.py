#!/usr/bin/env python3
"""Deterministic MRL Möbius 3D terminal.

The module stores append-only relay events with reversible links. It does not call
external models or services. Canonical promotion is restricted to `dofaromg`.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Iterable

ORIGIN = "mrl"
AUTHORITY_ACCOUNT = "dofaromg"
DOMAINS = {"authority", "knowledge", "event", "model", "product"}
LEVELS = {"L0", "L1", "L2", "L3", "L4", "L5"}


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class MobiusEvent:
    trace_id: str
    sequence: int
    operation: str
    domain: str
    authority_level: str
    depth: int
    twist: int
    payload_hash: str
    previous_hash: str
    origin: str = ORIGIN
    authority_account: str = AUTHORITY_ACCOUNT
    reversible: bool = True
    record_hash: str = ""

    def with_hash(self) -> "MobiusEvent":
        raw = asdict(self)
        raw["record_hash"] = ""
        return MobiusEvent(**{**raw, "record_hash": sha256_text(canonical_json(raw))})


def validate_name(name: str) -> None:
    lowered = name.strip().lower()
    if not (lowered.startswith("mrl.") or lowered.startswith("mrl_")):
        raise ValueError("generated name must use the mrl. or MRL_ namespace")


def create_event(
    *,
    name: str,
    sequence: int,
    operation: str,
    domain: str,
    authority_level: str,
    depth: int,
    twist: int,
    payload: Any,
    previous_hash: str,
) -> MobiusEvent:
    validate_name(name)
    if domain not in DOMAINS:
        raise ValueError(f"unsupported domain: {domain}")
    if authority_level not in LEVELS:
        raise ValueError(f"unsupported authority level: {authority_level}")
    if twist not in {0, 1}:
        raise ValueError("twist must be 0 or 1")
    if sequence < 0 or depth < 0:
        raise ValueError("sequence and depth must be non-negative")

    event = MobiusEvent(
        trace_id=name,
        sequence=sequence,
        operation=operation,
        domain=domain,
        authority_level=authority_level,
        depth=depth,
        twist=twist,
        payload_hash=sha256_text(canonical_json(payload)),
        previous_hash=previous_hash,
    )
    return event.with_hash()


def append_event(path: Path, event: MobiusEvent) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(canonical_json(asdict(event)) + "\n")


def read_events(path: Path) -> list[MobiusEvent]:
    if not path.exists():
        return []
    events: list[MobiusEvent] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            events.append(MobiusEvent(**json.loads(line)))
        except (TypeError, json.JSONDecodeError) as exc:
            raise ValueError(f"invalid ledger line {line_number}: {exc}") from exc
    return events


def verify_chain(events: Iterable[MobiusEvent]) -> list[str]:
    errors: list[str] = []
    previous_hash = "GENESIS"
    expected_sequence = 0

    for event in events:
        if event.origin != ORIGIN:
            errors.append(f"origin mismatch at sequence {event.sequence}")
        if event.authority_account != AUTHORITY_ACCOUNT:
            errors.append(f"authority mismatch at sequence {event.sequence}")
        if event.sequence != expected_sequence:
            errors.append(f"sequence discontinuity at {event.sequence}")
        if event.previous_hash != previous_hash:
            errors.append(f"previous_hash mismatch at sequence {event.sequence}")
        recalculated = event.with_hash().record_hash
        if event.record_hash != recalculated:
            errors.append(f"record_hash mismatch at sequence {event.sequence}")
        if not event.reversible:
            errors.append(f"event is not reversible at sequence {event.sequence}")
        previous_hash = event.record_hash
        expected_sequence += 1

    return errors


def replay(events: list[MobiusEvent], reverse: bool = False) -> list[dict[str, Any]]:
    ordered = reversed(events) if reverse else events
    return [asdict(event) for event in ordered]


def promote(events: list[MobiusEvent], approver: str) -> dict[str, Any]:
    if approver != AUTHORITY_ACCOUNT:
        raise PermissionError("only dofaromg may promote this MRL product")
    errors = verify_chain(events)
    if errors:
        raise ValueError("; ".join(errors))
    return {
        "product_id": "MRL_MOBIUS_3D_TERMINAL_v1",
        "origin": ORIGIN,
        "authority_account": AUTHORITY_ACCOUNT,
        "status": "approved",
        "construction_allowed": True,
        "event_count": len(events),
        "head_hash": events[-1].record_hash if events else "GENESIS",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="MRL Möbius 3D terminal")
    sub = parser.add_subparsers(dest="command", required=True)

    ingest = sub.add_parser("ingest")
    ingest.add_argument("ledger", type=Path)
    ingest.add_argument("--name", required=True)
    ingest.add_argument("--operation", default="ingest")
    ingest.add_argument("--domain", choices=sorted(DOMAINS), required=True)
    ingest.add_argument("--level", choices=sorted(LEVELS), default="L0")
    ingest.add_argument("--depth", type=int, default=0)
    ingest.add_argument("--twist", type=int, choices=[0, 1], default=0)
    ingest.add_argument("--payload", default="{}")

    verify = sub.add_parser("verify")
    verify.add_argument("ledger", type=Path)

    replay_cmd = sub.add_parser("replay")
    replay_cmd.add_argument("ledger", type=Path)
    replay_cmd.add_argument("--reverse", action="store_true")

    promote_cmd = sub.add_parser("promote")
    promote_cmd.add_argument("ledger", type=Path)
    promote_cmd.add_argument("--approver", required=True)

    args = parser.parse_args()

    if args.command == "ingest":
        events = read_events(args.ledger)
        previous_hash = events[-1].record_hash if events else "GENESIS"
        payload = json.loads(args.payload)
        event = create_event(
            name=args.name,
            sequence=len(events),
            operation=args.operation,
            domain=args.domain,
            authority_level=args.level,
            depth=args.depth,
            twist=args.twist,
            payload=payload,
            previous_hash=previous_hash,
        )
        append_event(args.ledger, event)
        print(json.dumps(asdict(event), ensure_ascii=False, indent=2))
        return 0

    events = read_events(args.ledger)
    if args.command == "verify":
        errors = verify_chain(events)
        print(json.dumps({"passed": not errors, "errors": errors}, ensure_ascii=False, indent=2))
        return 0 if not errors else 1
    if args.command == "replay":
        print(json.dumps(replay(events, args.reverse), ensure_ascii=False, indent=2))
        return 0
    if args.command == "promote":
        print(json.dumps(promote(events, args.approver), ensure_ascii=False, indent=2))
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
