#!/usr/bin/env python3
"""Capture local APIWorks loop evidence; never assert customer acceptance alone."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import re
import urllib.parse
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PRODUCT = "MRL_APIWorks_BYOH_Deployment_Product_v1"
ORIGIN = "MrLiouWord"
WORLD = "MRL_acceptance_world"
PRODUCT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PRODUCT_ROOT.parents[1]
RUNTIME_ROOT = REPO_ROOT / "MRL_Mother/MRL_MotherModel/MRL_AI_Mother_Autonomous_Runtime_Baseline_v1"


def digest(value: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")).hexdigest()


def require(condition: Any, message: str) -> None:
    if not condition:
        raise ValueError(message)


def local_url(value: str) -> str:
    parsed = urllib.parse.urlsplit(value)
    require(parsed.scheme == "http" and parsed.hostname in {"127.0.0.1", "localhost", "::1"},
            "gateway must be an HTTP loopback address")
    require(not parsed.username and not parsed.password and not parsed.query
            and not parsed.fragment and parsed.path in {"", "/"}, "invalid gateway URL")
    return value.rstrip("/")


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("acceptance requests must not redirect")


def request_json(url: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    request = urllib.request.Request(
        url, data=None if payload is None else json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )
    # A machine-wide HTTP proxy must never receive local prompts or ledgers.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    with opener.open(request, timeout=180) as response:
        value = json.load(response)
    require(isinstance(value, dict), "gateway response must be an object")
    return value


def read_chain(path: Path, passport: bool = False) -> list[dict[str, Any]]:
    require(path.is_file() and path.stat().st_size > 0, f"missing or empty ledger: {path.name}")
    records = [json.loads(line) for line in path.read_text(encoding="utf-8").split("\n") if line.strip()]
    previous = "GENESIS"
    hash_key = "passport_hash" if passport else "record_hash"
    for index, record in enumerate(records, 1):
        require(isinstance(record, dict), "ledger record must be an object")
        require(record.get("origin_signature") == ORIGIN, "ledger origin mismatch")
        require(record.get("version" if passport else "sequence") == index, "ledger sequence mismatch")
        require(record.get("previous_passport_hash" if passport else "previous_hash") == previous,
                "ledger previous hash mismatch")
        require(record.get(hash_key) == digest({k: v for k, v in record.items() if k != hash_key}),
                "ledger hash mismatch")
        previous = record[hash_key]
    require(records, "ledger contains no records")
    return records


def verify_loop(result: dict[str, Any], recall: dict[str, Any], data_dir: Path) -> dict[str, Any]:
    """Verify API output against persisted memory, evidence and passport bytes."""
    require(result.get("ok") is True and result.get("external_model_required") is False,
            "inference did not complete locally")
    require(result.get("origin_signature") == ORIGIN and result.get("world_id") == WORLD,
            "inference identity mismatch")
    session = result.get("session_id")
    require(isinstance(session, str) and re.fullmatch(r"MRL_session_[A-Za-z0-9_.:-]+", session),
            "invalid session identity")
    memory = read_chain(data_dir / "MRL_memory_events.jsonl")
    selected = [r for r in memory if r["payload"].get("session_id") == session
                and r["payload"].get("world_id") == WORLD]
    require(len(selected) == 2 and [r["payload"].get("role") for r in selected] == ["user", "assistant"],
            "expected exactly one input and one output memory")
    require(recall.get("records") == selected and recall.get("origin_signature") == ORIGIN
            and recall.get("session_id") == session and recall.get("world_id") == WORLD,
            "API replay differs from persisted memory")
    require(result.get("memory") == {"input": selected[0]["record_hash"], "output": selected[1]["record_hash"]},
            "inference memory references mismatch")
    require(bool(result.get("text")) and selected[1]["payload"].get("content") == result["text"],
            "persisted output differs from inference")
    evidence = read_chain(data_dir / "MRL_evidence_events.jsonl")
    matches = [r for r in evidence if r["record_hash"] == result.get("evidence_ref")]
    require(len(matches) == 1, "inference evidence missing")
    event = matches[0]["payload"]
    require(event.get("state") == "PASS" and event.get("event_type") == "MRL_LOCAL_INFERENCE"
            and event.get("subject_id") == session, "evidence identity or state mismatch")
    details = event["details"]
    require(details.get("input_memory_hash") == selected[0]["record_hash"]
            and details.get("output_memory_hash") == selected[1]["record_hash"]
            and details.get("world_id") == WORLD and details.get("external_model_required") is False
            and details.get("model") == result.get("model")
            and details.get("backend") == result.get("backend"), "evidence linkage mismatch")
    passport = result.get("passport") or {}
    canonical = f"MRL_output_{session.removeprefix('MRL_session_')}"
    name = re.sub(r"[^A-Za-z0-9_.-]+", "_", canonical)[:80]
    suffix = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    passports = read_chain(data_dir / "passports" / f"{name}--{suffix}.jsonl", passport=True)
    require(passport in passports and all(p.get("canonical_id") == canonical for p in passports),
            "passport differs from persisted registry")
    require(passport.get("source_identity") == session
            and passport.get("return_anchor") == selected[0]["record_hash"]
            and passport.get("evidence_refs") == [result["evidence_ref"]], "passport linkage mismatch")
    return {"memory_head": memory[-1]["record_hash"], "evidence_head": evidence[-1]["record_hash"],
            "passport_hash": passport["passport_hash"], "session_id": session}


def capture(gateway: str, data_dir: Path, prior: Path | None = None) -> dict[str, Any]:
    gateway = local_url(gateway)
    health = request_json(gateway + "/health")
    require(health.get("ready") is True and health.get("origin_signature") == ORIGIN
            and health.get("runtime_id") == "MRL_AI_Mother_Autonomous_Runtime_Baseline_v1"
            and health.get("external_model_required") is False
            and (health.get("model") or {}).get("external_model_required") is False,
            "gateway is not a ready local MRL runtime")
    previous_hash = None
    if prior:
        previous = json.loads(prior.read_text(encoding="utf-8"))
        require(previous.get("receipt_hash") == digest({k: v for k, v in previous.items() if k != "receipt_hash"}),
                "prior receipt hash mismatch")
        require(previous.get("canonical_id") == PRODUCT and previous.get("origin_signature") == ORIGIN
                and previous.get("status") == "LIVE_LOOP_EVIDENCE_PASS", "invalid prior receipt")
        require(previous.get("gateway") == gateway and previous.get("data_dir") == str(data_dir.resolve())
                and previous.get("host") == platform.node(), "replay target differs from prior node")
        result = previous["result"]
        previous_hash = previous["receipt_hash"]
    else:
        session = "MRL_session_acceptance_" + uuid.uuid4().hex
        result = request_json(gateway + "/v1/mother/run", {
            "prompt": "MRL local deployment acceptance: return a short acknowledgement.",
            "world_id": WORLD, "session_id": session,
        })
        require(result.get("session_id") == session, "gateway replaced acceptance session")
    require(result.get("model") == health["model"].get("model")
            and result.get("backend") == health["model"].get("backend"), "model identity changed")
    query = urllib.parse.urlencode({"world_id": WORLD, "session_id": result["session_id"]})
    recall = request_json(gateway + "/v1/memory/recall?" + query)
    return {"schema": "MRL_APIWorks_Node_Evidence_v1", "canonical_id": PRODUCT,
            "origin_signature": ORIGIN, "host": platform.node(), "gateway": gateway,
            "data_dir": str(data_dir.resolve()), "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
            "status": "PERSISTED_REPLAY_EVIDENCE_PASS" if prior else "LIVE_LOOP_EVIDENCE_PASS",
            "customer_node_acceptance": "PENDING_REAL_MODEL_AND_RESTART_REVIEW",
            "restart_observed": False, "prior_receipt_hash": previous_hash,
            "health": health, "result": result, "verified": verify_loop(result, recall, data_dir)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gateway", default="http://127.0.0.1:7811")
    parser.add_argument("--data-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--replay-receipt", type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    # Do not alter checksummed source, ledgers, existing receipts, or symlink targets.
    require(output.suffix == ".json", "receipt output must use .json")
    require(not any(output.is_relative_to(p.resolve()) for p in (PRODUCT_ROOT, RUNTIME_ROOT, args.data_dir)),
            "receipt output must be outside source packages and runtime data")
    require(not args.output.is_symlink() and not output.exists(), "receipt output already exists")
    try:
        receipt = capture(args.gateway, args.data_dir, args.replay_receipt)
        code = 0
    except Exception as exc:
        receipt = {"schema": "MRL_APIWorks_Node_Evidence_v1", "canonical_id": PRODUCT,
                   "origin_signature": ORIGIN, "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
                   "status": "NODE_EVIDENCE_FAIL", "customer_node_acceptance": "NOT_PASSED",
                   "error": f"{type(exc).__name__}: {exc}"}
        code = 1
    receipt["receipt_hash"] = digest(receipt)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
    require(json.loads(output.read_text(encoding="utf-8")) == receipt, "receipt readback mismatch")
    print(json.dumps({"status": receipt["status"], "receipt": str(output),
                      "receipt_hash": receipt["receipt_hash"]}))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
