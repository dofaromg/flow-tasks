"""On-host, fail-closed acceptance of the existing MRL bridge and Python runtime.

origin_signature: MrLiouWord. No service, port, credential or runtime is created.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import time
import urllib.error
import urllib.request

SCHEMA = "MRL.BridgeTranslationCenter.v1"
RUNTIME_FILES = (
    "MRL_Bridge/translation_center.py", "connectors/base_connector.py",
    "MRL_Mother/09_workflow/MRL_Mobius_Closure_Engine_v1.py",
)
BRIDGE_FILES = ("MRL_Bridge/server.js", "MRL_Bridge/mrl_bridge_translation_center.cjs")


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def utc(value):
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError("timezone required")
    return result.astimezone(timezone.utc)


def on_d(path):
    return Path(path).resolve().drive.upper() == "D:"


def read_chain(path, retain=None):
    """Read only a fixed-size prefix; a concurrent unfinished append is retried."""
    previous = "GENESIS"
    records = []
    sequence = 0
    with Path(path).open("rb") as stream:
        remaining = os.fstat(stream.fileno()).st_size
        while remaining:
            line = stream.readline(remaining)
            remaining -= len(line)
            if not line.endswith(b"\n"):
                raise ValueError("ledger append in progress or truncated")
            record = json.loads(line)
            unsigned = {k: v for k, v in record.items() if k != "record_sha256"}
            if (record["sequence"] != sequence
                    or record["previous_sha256"] != previous
                    or digest(canonical(unsigned)) != record["record_sha256"]):
                raise ValueError("ledger chain mismatch")
            if (record["schema"] != SCHEMA or record["mrl_affiliation"] != "MRL"
                    or record["origin_signature"] != "MrLiouWord"
                    or record["canonical_authority"] != "Mr.liou"
                    or record["storage"] != "append-only-file"):
                raise ValueError("ledger metadata mismatch")
            previous = record["record_sha256"]
            sequence += 1
            if retain is None or retain(record):
                records.append(record)
    return records


def check_trace(records, trace, incoming, outgoing, status, artifact=None):
    group = [r for r in records if r["trace_id"] == trace]
    expected = ["started", "received", "tagged", "sent"] if artifact is not None else ["started", "received", "sent"]
    if [r["status"] for r in group] != expected:
        raise ValueError("incomplete live HTTP trace")
    for parent, child in zip(group, group[1:]):
        if child["parent_ref"] != parent["event_id"]:
            raise ValueError("HTTP parent mismatch")
    if (group[1]["payload_sha256"] != digest(incoming)
            or group[-1]["payload_sha256"] != digest(outgoing)
            or group[-1]["http_status"] != status):
        raise ValueError("HTTP byte/status mismatch")
    if artifact is not None:
        if group[2]["event_id"] != artifact["event_id"]:
            raise ValueError("artifact event mismatch")
    return {"trace_id": trace, "event_ids": [r["event_id"] for r in group],
            "request_sha256": digest(incoming), "response_sha256": digest(outgoing),
            "http_status": status}


def python_evidence(records, processes, expected_hash, expected_path, since, now):
    """Require actual post-deploy service activity, not a new acceptance subprocess."""
    live = {int(p["pid"]): p for p in processes}
    accepted = []
    for record in records:
        proof = record.get("runtime_evidence", {})
        process = live.get(proof.get("process_id"))
        if not process or process.get("service_owned") is not True:
            continue
        try:
            created = utc(process["created_at"])
            loaded = utc(proof["module_loaded_at"])
            observed = utc(record["timestamp"])
            valid = (since <= created <= loaded <= observed <= now
                     and proof["module_sha256_lf"] == expected_hash
                     and Path(proof["module_path"]).resolve() == Path(expected_path).resolve()
                     and Path(proof["executable"]).resolve() == Path(process["executable"]).resolve())
        except (KeyError, TypeError, ValueError):
            valid = False
        if valid:
            accepted.append(record)
    connector = False
    for trace in {r["trace_id"] for r in accepted}:
        group = [r for r in accepted if r["trace_id"] == trace]
        if (len(group) >= 2 and group[0]["source_ref"] == "MRL.connector"
                and group[0]["status"] == "dispatching"
                and group[-1]["destination_ref"] == "MRL.connector"
                and group[-1]["status"] in {"received", "transport_error"}
                and all(b["parent_ref"] == a["event_id"] for a, b in zip(group, group[1:]))):
            connector = True
    mobius = any(r["source_ref"].startswith("MRL.Mobius.") for r in accepted)
    # At least one complete successful Mobius route/collapse/lift round trip.
    closed = False
    for trace in {r["trace_id"] for r in accepted}:
        group = [r for r in accepted if r["trace_id"] == trace]
        if ([r["source_ref"] for r in group] == ["MRL.Mobius.R", "MRL.Mobius.route", "MRL.Mobius.collapse", "MRL.Mobius.A"]
                and all(b["parent_ref"] == a["event_id"] for a, b in zip(group, group[1:]))):
            closed = True
    return {"pass": connector and mobius and closed,
            "connector_observed": connector, "mobius_roundtrip_observed": closed,
            "event_ids": [r["event_id"] for r in accepted],
            "process_ids": sorted({r["runtime_evidence"]["process_id"] for r in accepted})}


def request(port, route, key=None, payload=None):
    raw = canonical(payload) if payload is not None else b""
    headers = {"Content-Type": "application/json"}
    if key:
        headers["x-api-key"] = key
    req = urllib.request.Request(f"http://127.0.0.1:{port}{route}",
                                 data=raw if payload is not None else None, headers=headers)
    # Never send credentials through configured proxies, or follow a redirect.
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *args, **kwargs):
            return None
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    try:
        response = opener.open(req, timeout=10)
    except urllib.error.HTTPError as error:
        response = error
    with response:
        body = response.read(2 * 1024 * 1024 + 1)
        if len(body) > 2 * 1024 * 1024:
            raise ValueError("unexpected acceptance response size")
        if response.headers.get("X-MRL-Affiliation") != "MRL":
            raise ValueError("live response missing MRL label")
        trace = response.headers.get("X-MRL-Trace-Id")
        if not trace:
            raise ValueError("live response missing trace")
        return response.code, trace, raw, body


def run(args):
    inventory = json.loads(Path(args.inventory).read_text(encoding="utf-8-sig"))
    if platform.system() != "Windows" or platform.node().upper() != "WIN-PBVUI7VK2A6":
        raise ValueError("requires actual DL580 Windows host")
    paths = (args.inventory, args.output, args.runtime_root, args.bridge_directory,
             args.node_ledger_dir, args.python_ledger_dir, args.source_root)
    if not all(on_d(p) for p in paths):
        raise ValueError("all deployment data must remain on D:")
    now = datetime.now(timezone.utc)
    since = utc(inventory["deployment_started_at"])
    captured = utc(inventory["captured_at"])
    if (inventory["computer"] != platform.node() or not since <= captured <= now
            or (now - captured).total_seconds() > 120):
        raise ValueError("inventory is stale or target differs")
    source = Path(args.source_root)
    audit = json.loads((source / "docs/MRL_Bridge_Translation_Center_v1.audit.json").read_text())
    entries = {e["path"]: e for e in audit["files"]}
    files = []
    for rel in RUNTIME_FILES + BRIDGE_FILES:
        target = Path(args.runtime_root) / rel if rel in RUNTIME_FILES else Path(args.bridge_directory) / Path(rel).name
        raw = target.read_bytes()
        actual = digest(raw.replace(b"\r\n", b"\n"))
        if actual != entries[rel]["sha256_lf"]:
            raise ValueError("installed module differs from source audit")
        files.append({"path": str(target), "size": len(raw), "sha256": digest(raw), "sha256_lf": actual})
    receipt = {"schema": "MRL.BridgeTranslationAcceptance.v1", "origin_signature": "MrLiouWord",
               "canonical_authority": "Mr.liou", "computer": platform.node(),
               "source_commit": inventory["source_commit"], "deployment_started_at": since.isoformat(),
               "timestamp": now.isoformat(), "files": files,
               "node_bridge": {"pass": False}, "python_runtime": {"pass": False}}
    try:
        key = os.environ.get("MRL_BRIDGE_API_KEY")
        if not key:
            raise ValueError("existing MRL_BRIDGE_API_KEY environment required")
        probes = []
        fixture = {"filename": "MRL_acceptance_module.py", "version": "acceptance-v1",
                   "code": "# MRL acceptance fixture; never executed\n", "origin_signature": "external-acceptance-fixture"}
        for route, auth, payload, expected in (
                ("/version", None, None, 200),
                ("/MRL_bridge_translation/status", None, None, 401),
                ("/MRL_bridge_translation/status", key, None, 200),
                ("/MRL_bridge_translation/tag", key, {"payload": fixture}, 200),
                ("/MRL_bridge_translation/tag", key, {}, 400)):
            status, trace, raw, body = request(args.port, route, auth, payload)
            if status != expected:
                raise ValueError("live HTTP status mismatch")
            value = json.loads(body)
            artifact = None
            if route == "/version":
                if value.get("bridge_translation", {}).get("schema") != SCHEMA:
                    raise ValueError("live Bridge schema mismatch")
            elif route.endswith("/status") and auth:
                if value.get("storage") != "append-only-file" or value.get("audit_error"):
                    raise ValueError("live Bridge not durably recording")
            elif route.endswith("/tag") and payload:
                artifact = value["mrl_bridge"]
                if (value["payload"] != fixture
                        or artifact["payload_origin_signature"] != fixture["origin_signature"]
                        or artifact["payload_sha256"] != digest(canonical(fixture))):
                    raise ValueError("artifact content or provenance changed")
            probes.append((trace, raw, body, status, artifact))
        node_pid = int(inventory["node"]["pid"])
        if inventory["node"].get("service_owned") is not True or utc(inventory["node"]["created_at"]) < since:
            raise ValueError("Node listener not owned by restarted existing service")
        ledger = Path(args.node_ledger_dir) / f"MRL_bridge_translation-{node_pid}.jsonl"
        for attempt in range(10):
            try:
                records = read_chain(ledger, lambda r: r["trace_id"] in {p[0] for p in probes})
                proofs = [check_trace(records, *p) for p in probes]
                break
            except (ValueError, FileNotFoundError):
                if attempt == 9:
                    raise
                time.sleep(0.2)
        receipt["node_bridge"] = {"pass": True, "ledger": str(ledger), "probes": proofs,
                                  "pid": node_pid}
    except (OSError, ValueError, KeyError, TypeError):
        receipt["node_bridge"]["blocker"] = "LIVE_HTTP_OR_LEDGER_ACCEPTANCE_FAILED"
    try:
        records = []
        ledgers = []
        for path in Path(args.python_ledger_dir).glob("*.jsonl"):
            # Node, historic and unrelated files are excluded from Python replay.
            if not re.fullmatch(r"(?:mobius|connector)-\d+\.jsonl", path.name):
                continue
            group = read_chain(path, lambda r: since <= utc(r["timestamp"]) <= now)
            records.extend(group)
            ledgers.append({"path": str(path), "observed_event_ids": [r["event_id"] for r in group]})
        proof = python_evidence(records, inventory.get("python_processes", []),
                                entries[RUNTIME_FILES[0]]["sha256_lf"],
                                Path(args.runtime_root) / RUNTIME_FILES[0], since, now)
        receipt["python_runtime"] = dict(proof, ledgers=ledgers)
        if not proof["pass"]:
            receipt["python_runtime"]["blocker"] = "NEED_RELOADED_EXISTING_SERVICE_CONNECTOR_AND_MOBIUS_ACTIVITY"
    except (OSError, ValueError, KeyError, TypeError):
        receipt["python_runtime"]["blocker"] = "PYTHON_LEDGER_ACCEPTANCE_FAILED"
    receipt["status"] = "DELIVERY_PASS" if all(receipt[k]["pass"] for k in ("node_bridge", "python_runtime")) else "DELIVERY_FAIL"
    target = Path(args.output)
    # Never overwrite prior acceptance history.
    with target.open("x", encoding="utf-8") as handle:
        json.dump(receipt, handle, ensure_ascii=False, indent=2)
        handle.flush()
        os.fsync(handle.fileno())
    print(json.dumps({"status": receipt["status"], "node_bridge_pass": receipt["node_bridge"]["pass"],
                      "python_runtime_pass": receipt["python_runtime"]["pass"], "receipt": str(target)}))
    return 0 if receipt["status"] == "DELIVERY_PASS" else 2


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("inventory", "output", "runtime-root", "bridge-directory", "node-ledger-dir", "python-ledger-dir", "source-root"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--port", type=int, default=7800)
    args = parser.parse_args()
    try:
        return run(args)
    except (OSError, ValueError, KeyError, TypeError):
        print(json.dumps({"status": "DELIVERY_FAIL", "blocker": "HOST_PATH_INVENTORY_OR_INSTALLED_SOURCE_PREFLIGHT_FAILED"}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
