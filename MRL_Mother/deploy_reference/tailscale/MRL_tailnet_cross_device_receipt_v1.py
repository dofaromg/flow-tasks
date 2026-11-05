#!/usr/bin/env python3
"""Read-only MRL-44 tailnet probes and private receipt reconciliation."""

import argparse
import base64
import binascii
import errno
import getpass
import hashlib
import http.client
import ipaddress
import json
import os
import platform
import re
import shutil
import socket
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = "MRL_Tailnet_Cross_Device_Receipt_v1"
ORIGIN = "MrLiouWord"
TAILNET = ipaddress.ip_network("100.64.0.0/10")
BRIDGE = "MRL_Bridge"
SERVICES = {
    BRIDGE: (7800, "/health", "service", "MRL_Bridge_API"),
    "MRL_RuntimeOS": (
        8790, "/api/mrl/health", "product",
        "MRL_RuntimeOS_EnterpriseRuntimePlatform_CoreExecutable_v1_4_0",
    ),
    "MRL_Inference": (7500, "/health", None, None),
    "MRL_FlowAgent_API": (7900, "/health", None, None),
    "MRL_3DScanner_ProductBridge": (3050, "/health", None, None),
}
DIGEST = re.compile(r"[0-9a-f]{64}")
PONG = re.compile(r"^pong from .+? \(([^)]+)\) via (\S+)", re.I | re.M)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def utc():
    return datetime.now(timezone.utc).isoformat()


def tailnet_ip(value):
    try:
        return ipaddress.ip_address(value) in TAILNET
    except ValueError:
        return False


def command(binary, args, timeout=15):
    if not binary:
        return {"result": "CLI_UNAVAILABLE", "exit_code": None, "stdout": "", "stderr": ""}
    try:
        proc = subprocess.run(
            [binary, *args], capture_output=True, encoding="utf-8",
            errors="replace", timeout=timeout, check=False,
        )
    except subprocess.TimeoutExpired:
        return {"result": "TIMEOUT", "exit_code": None, "stdout": "", "stderr": ""}
    except OSError:
        return {"result": "CLI_ERROR", "exit_code": None, "stdout": "", "stderr": ""}
    return {
        "result": "PASS" if proc.returncode == 0 else "COMMAND_FAILED",
        "exit_code": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr,
    }


def json_object(raw):
    try:
        value = json.loads(raw)
    except (ValueError, UnicodeError):
        return {}
    return value if isinstance(value, dict) else {}


def peer_state(status, target):
    if status.get("BackendState") != "Running":
        return "BACKEND_NOT_RUNNING" if status.get("BackendState") else "STATUS_UNKNOWN"
    peers = status.get("Peer") or {}
    matches = [p for p in peers.values() if target in (p.get("TailscaleIPs") or [])]
    if len(matches) != 1:
        return "PEER_NOT_IDENTIFIED"
    if matches[0].get("Online") is False:
        return "PEER_REPORTED_OFFLINE"
    return "PEER_IDENTIFIED"


def ping_result(raw, target):
    routes = []
    for peer, via in PONG.findall(raw["stdout"]):
        if peer != target:
            continue
        if via.upper().startswith("DERP("):
            route = "DERP"
        elif via.lower().startswith(("peer-relay", "peerrelay")):
            route = "PEER_RELAY"
        else:
            host, _, port = via.rpartition(":")
            try:
                ipaddress.ip_address(host.strip("[]"))
                route = "DIRECT" if port.isdecimal() else "UNKNOWN"
            except ValueError:
                route = "UNKNOWN"
        routes.append(route)
    if routes:
        return {"result": "PASS", "observed_routes": routes}
    output = (raw["stdout"] + raw["stderr"]).lower()
    result = raw["result"]
    if "timed out" in output or "timeout waiting" in output:
        result = "TIMEOUT"
    elif result == "PASS":
        result = "NO_MATCHING_PONG"
    return {"result": result, "observed_routes": []}


def network_error(error):
    if isinstance(error, TimeoutError):
        return "TIMEOUT"
    if isinstance(error, OSError):
        if error.errno in (errno.ECONNREFUSED, 10061):
            return "CONNECTION_REFUSED"
        if error.errno in (errno.ENETUNREACH, errno.EHOSTUNREACH, 10051, 10065):
            return "NETWORK_UNREACHABLE"
    return "IO_ERROR"


def request(host, source, port, path, timeout, *, body=None, key=None):
    # HTTPConnection has no redirect following or environment proxy support.
    conn = http.client.HTTPConnection(host, port, timeout=timeout, source_address=source)
    headers = {"Accept": "application/json"}
    if body is not None:
        headers.update({"Content-Type": "application/json", "x-api-key": key})
    status = None
    try:
        conn.request("GET" if body is None else "POST", path, body=body, headers=headers)
        response = conn.getresponse()
        status = response.status
        data = response.read(65537) if 200 <= status < 300 else b""
        if len(data) > 65536:
            return status, {}, "BODY_TOO_LARGE"
        return status, json_object(data), "RESPONSE"
    except (OSError, http.client.HTTPException) as error:
        return status, {}, network_error(error)
    finally:
        conn.close()


def endpoint(host, source, name, timeout):
    port, path, field, expected = SERVICES[name]
    result = {
        "port": port, "path": path, "tcp": "UNRUN", "http": "UNRUN", "status": None,
        "health": "UNRUN", "identity": "UNKNOWN", "authorization": "UNVERIFIED",
    }
    try:
        with socket.create_connection((host, port), timeout, source_address=source):
            result["tcp"] = "PASS"
    except OSError as error:
        result["tcp"] = network_error(error)
        return result

    status, payload, detail = request(host, source, port, path, timeout)
    result.update(status=status, http="RESPONSE" if status is not None else detail)
    if status in (401, 403):
        result.update(health="UNKNOWN", authorization="REJECTED")
    elif status == 404:
        result["health"] = "ROUTE_NOT_FOUND"
    elif status is None or detail != "RESPONSE":
        result["health"] = detail
    elif not 200 <= status < 300:
        result["health"] = "HTTP_ERROR"
    elif field and payload.get(field) != expected:
        result.update(health="UNKNOWN", identity="IDENTITY_MISMATCH")
    elif field:
        result["identity"] = "MATCH"
        if name == BRIDGE:
            result["health"] = (
                "PASS" if all(payload.get(k) is True for k in ("api", "pg", "redis"))
                else "DEGRADED_OR_UNKNOWN"
            )
        else:
            result["health"] = "PASS" if payload.get("status") == "ok" else "UNKNOWN"
    else:
        result["health"] = "HTTP_2XX_IDENTITY_UNVERIFIED"
    return result


def readback(host, source, identity, filepath, expected_sha, timeout, key):
    result = {"result": "UNRUN", "authorization": "UNVERIFIED", "status": None}
    if identity != "MATCH":
        result["result"] = "BRIDGE_IDENTITY_UNVERIFIED"
    elif not key:
        result["result"] = "KEY_UNAVAILABLE"
    else:
        body = json.dumps({"filepath": filepath, "encoding": "base64"}).encode()
        status, payload, detail = request(
            host, source, SERVICES[BRIDGE][0], "/MRL_file/read", timeout, body=body, key=key,
        )
        result["status"] = status
        if status in (401, 403):
            result.update(result="AUTH_REJECTED", authorization="REJECTED")
        elif status == 200 and detail == "RESPONSE" and payload.get("ok") is True:
            try:
                data = base64.b64decode(payload["content"], validate=True)
                uuid.UUID(data.decode("ascii"))
                verified = sha(data) == expected_sha
            except (KeyError, TypeError, ValueError, binascii.Error):
                verified = False
            result.update(
                result="PASS" if verified else "READBACK_MISMATCH",
                authorization="ACCEPTED",
            )
        else:
            result["result"] = "HTTP_ERROR" if status and detail == "RESPONSE" else detail
    return result


def write_receipt(directory, name, value):
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    raw = (json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True) + "\n").encode()
    path = directory / (name + ".json")
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(raw)
    return {"file": str(path), "sha256": sha(path.read_bytes())}


def collect(args):
    system = platform.system()
    if (args.role, system) not in (("mac", "Darwin"), ("dl580", "Windows")):
        raise ValueError("role does not match operating system")
    started = utc()
    binary = args.tailscale or shutil.which("tailscale")
    if not binary:
        candidate = (
            Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "Tailscale/tailscale.exe"
            if system == "Windows" else Path("/Applications/Tailscale.app/Contents/MacOS/Tailscale")
        )
        if candidate.is_file():
            binary = str(candidate)
    raw = {
        "status": command(binary, ["status", "--json"]),
        "ip4": command(binary, ["ip", "-4"]),
        "netcheck": command(binary, ["netcheck"]),
        "serve": command(binary, ["serve", "status"]),
    }
    status = json_object(raw["status"]["stdout"]) if raw["status"]["result"] == "PASS" else {}
    self_ip = raw["ip4"]["stdout"].strip()
    self_ips = (status.get("Self") or {}).get("TailscaleIPs") or []
    if raw["ip4"]["result"] != "PASS" or not tailnet_ip(self_ip) or self_ip not in self_ips:
        self_ip = None
    target = args.peer_ip
    peer = peer_state(status, target)
    usable = self_ip and self_ip != target and peer in ("PEER_IDENTIFIED", "PEER_REPORTED_OFFLINE")
    ping = {"result": "UNRUN", "observed_routes": []}
    if usable:
        raw["ping"] = command(binary, ["ping", "--c=3", "--timeout=3s", target])
        ping = ping_result(raw["ping"], target)

    results = {}
    bridge = {"result": "UNRUN", "authorization": "UNVERIFIED", "status": None}
    if args.role == "dl580":
        results = {name: endpoint("127.0.0.1", None, name, args.timeout) for name in SERVICES}
    elif usable:
        source = (self_ip, 0)
        results = {name: endpoint(target, source, name, args.timeout) for name in SERVICES}
        if args.bridge_canary:
            identity = results[BRIDGE]["identity"]
            if identity != "MATCH":
                # /health can be denied or degraded. /version is an independent identity check.
                code, payload, detail = request(target, source, 7800, "/version", args.timeout)
                if code == 200 and detail == "RESPONSE" and payload.get("service") == "MRL_Bridge_API":
                    identity = "MATCH"
            key = getpass.getpass("MRL_Bridge API key: ") if identity == "MATCH" else None
            if key and not re.fullmatch(r"[!-~]+", key):
                raise ValueError("Bridge key must be a single printable ASCII header value")
            bridge = readback(
                target, source, identity, args.bridge_canary, args.canary_sha256, args.timeout, key,
            )

    receipt = {
        "schema": SCHEMA, "origin_signature": ORIGIN, "run_id": str(args.run_id),
        "role": args.role, "started_at_utc": started, "observed_at_utc": utc(),
        "collector_sha256": sha(Path(__file__).read_bytes()),
        "self_ip": self_ip, "peer_ip": target, "peer_state": peer,
        "ping": ping, "services": results, "bridge_readback": bridge, "raw": raw,
        "canary_sha256": args.canary_sha256,
    }
    return write_receipt(args.out_dir, f"MRL_Tailnet_{args.role}_{args.run_id}", receipt)


def verified_json(path, digest):
    raw = path.read_bytes()
    if sha(raw) != digest:
        raise ValueError("receipt SHA-256 mismatch")
    result = json_object(raw)
    if not result:
        raise ValueError("receipt is not a JSON object")
    return result


NETWORK_STATES = {
    "TIMEOUT", "CONNECTION_REFUSED", "NETWORK_UNREACHABLE", "IO_ERROR", "BODY_TOO_LARGE",
}


def safe_fields(row, fields):
    result = {field: row[field] if row.get(field) in allowed else "UNKNOWN"
              for field, allowed in fields.items()}
    status = row.get("status")
    result["status"] = status if type(status) is int and 100 <= status <= 599 else None
    return result


def safe_ping(ping):
    fields = {"PASS", "UNRUN", "TIMEOUT", "CLI_UNAVAILABLE", "CLI_ERROR",
              "COMMAND_FAILED", "NO_MATCHING_PONG"}
    routes = [r for r in ping["observed_routes"] if r in ("DIRECT", "DERP", "PEER_RELAY", "UNKNOWN")]
    state = ping["result"]
    return {"result": state if state in fields and (state != "PASS" or routes) else "UNKNOWN",
            "observed_routes": routes}


def safe_services(rows):
    output = {}
    for name, (port, path, _, _) in SERVICES.items():
        row = rows.get(name)
        if not row:
            continue
        if (row["port"], row["path"]) != (port, path):
            raise ValueError("service port or health route mismatch")
        output[name] = {
            "port": port, "path": path,
            **safe_fields(row, {
                "tcp": {"PASS", "UNRUN", *NETWORK_STATES},
                "http": {"RESPONSE", "UNRUN", *NETWORK_STATES},
                "health": {"PASS", "UNRUN", "UNKNOWN", "ROUTE_NOT_FOUND", "HTTP_ERROR",
                           "DEGRADED_OR_UNKNOWN", "HTTP_2XX_IDENTITY_UNVERIFIED", *NETWORK_STATES},
                "identity": {"MATCH", "UNKNOWN", "IDENTITY_MISMATCH"},
                "authorization": {"UNVERIFIED", "REJECTED"},
            }),
        }
    return output


def reconcile(args):
    mac = verified_json(args.mac, args.mac_sha256)
    dl = verified_json(args.dl580, args.dl580_sha256)
    for role, value in (("mac", mac), ("dl580", dl)):
        if value["schema"] != SCHEMA or value["origin_signature"] != ORIGIN or value["role"] != role:
            raise ValueError("receipt role, schema or origin mismatch")
    if mac["collector_sha256"] != dl["collector_sha256"]:
        raise ValueError("collector versions differ")
    if mac["run_id"] != dl["run_id"] or str(uuid.UUID(mac["run_id"])) != mac["run_id"]:
        raise ValueError("receipt run IDs differ")
    times = [datetime.fromisoformat(v[k]) for v in (mac, dl)
             for k in ("started_at_utc", "observed_at_utc")]
    if any(t.utcoffset() is None for t in times) or not (
        times[0] <= times[1] and times[2] <= times[3]
    ) or (max(times) - min(times)).total_seconds() > 1800:
        raise ValueError("collection times are invalid or more than 30 minutes apart")
    identities_match = bool(
        tailnet_ip(mac["self_ip"]) and tailnet_ip(dl["self_ip"])
        and mac["self_ip"] != dl["self_ip"]
        and mac["peer_ip"] == dl["self_ip"] and dl["peer_ip"] == mac["self_ip"]
    )
    windows = verified_json(args.windows_receipt, args.windows_sha256)
    stamp = datetime.fromisoformat(windows["observed_at_utc"])
    if (
        windows["schema"] != "MRL_Tailnet_Bridge_Receipt_v1"
        or windows["origin_signature"] != ORIGIN or stamp.utcoffset() is None
        or abs((stamp - times[2]).total_seconds()) > 1800
    ):
        raise ValueError("Windows collector schema, origin or time mismatch")
    windows_match = (
        windows["host_match"] is True and dl["self_ip"] is not None
        and dl["self_ip"] in windows["tailscale"]["self_ips"]
    )
    paired = identities_match and windows_match
    if not DIGEST.fullmatch(mac["collector_sha256"]):
        raise ValueError("invalid collector digest")
    pings = {"mac_to_dl580": safe_ping(mac["ping"]), "dl580_to_mac": safe_ping(dl["ping"])}
    bridge = {"result": "UNVERIFIED"}
    if paired:
        bridge = safe_fields(mac["bridge_readback"], {
            "result": {"UNRUN", "KEY_UNAVAILABLE", "AUTH_REJECTED", "PASS", "READBACK_MISMATCH",
                       "BRIDGE_IDENTITY_UNVERIFIED", "HTTP_ERROR", *NETWORK_STATES},
            "authorization": {"UNVERIFIED", "ACCEPTED", "REJECTED"},
        })
        if bridge["result"] == "PASS":
            if not args.canary or sha(args.canary.read_bytes()) != mac["canary_sha256"]:
                bridge["result"] = "LOCAL_CANARY_NOT_VERIFIED"
    reach = (
        "UNKNOWN" if not paired else
        "PASS" if all(p["result"] == "PASS" for p in pings.values()) else "NOT_VERIFIED"
    )
    # The exported schema is an allowlist. Raw commands, hosts and addresses stay private.
    result = {
        "schema": "MRL_Tailnet_Cross_Device_Summary_v1", "origin_signature": ORIGIN,
        "run_id": mac["run_id"], "observed_at_utc": max(times).isoformat(),
        "source_sha256": {
            "mac": args.mac_sha256, "dl580": args.dl580_sha256,
            "windows_collector": args.windows_sha256, "collector": mac["collector_sha256"],
        },
        "passport_network_evidence": {
            "passport_sha256": sha(args.passport.read_bytes()) if args.passport else None,
            "link": "SUPPLEMENTAL_DIGEST_ONLY" if args.passport else "UNRUN",
        },
        "peer_identity": "CORRELATED" if paired else "UNKNOWN",
        "ping": pings, "bidirectional_tailnet_ping": reach,
        "service_scope": "CORRELATED" if paired else "UNVERIFIED",
        "windows_services": {
            s["name"]: s["status"] for s in windows["services"]
            if s["name"] in (*SERVICES, "MRL_Inference_v5", "MRL_Tunnel", "MRL_Tailscale", "Tailscale")
            and s["status"] in ("Running", "Stopped", "Paused", "StartPending", "StopPending",
                                "ContinuePending", "PausePending", "NOT_FOUND")
        },
        "windows_listener_present": {
            s["name"]: s["listening"] for s in windows["ports"]
            if s["name"] in SERVICES and s["port"] == SERVICES[s["name"]][0]
            and type(s["listening"]) is bool
        },
        "mac_to_dl580": safe_services(mac["services"]),
        "dl580_loopback": safe_services(dl["services"]),
        "bridge_readback": bridge,
        "iphone_to_dl580": "UNRUN", "tailnet_grants": "UNKNOWN", "deployment": "UNRUN",
    }
    return write_receipt(args.out_dir, f"MRL_Tailnet_Summary_{mac['run_id']}", result)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_subparsers(dest="mode", required=True)
    probe = modes.add_parser("collect")
    probe.add_argument("--role", choices=("mac", "dl580"), required=True)
    probe.add_argument("--run-id", required=True, type=uuid.UUID)
    probe.add_argument("--peer-ip", required=True)
    probe.add_argument("--tailscale")
    probe.add_argument("--timeout", type=int, choices=range(1, 11), default=3)
    probe.add_argument("--bridge-canary")
    probe.add_argument("--canary-sha256")
    pair = modes.add_parser("reconcile")
    for name in ("mac", "dl580", "windows-receipt"):
        pair.add_argument(f"--{name}", required=True, type=Path)
    for name in ("mac", "dl580", "windows"):
        pair.add_argument(f"--{name}-sha256", required=True)
    pair.add_argument("--passport", type=Path)
    pair.add_argument("--canary", type=Path)
    for mode in (probe, pair):
        mode.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.mode == "collect":
            if not tailnet_ip(args.peer_ip):
                raise ValueError("peer must be a current Tailscale IPv4 address")
            if args.bridge_canary or args.canary_sha256:
                if (
                    args.role != "mac" or not args.bridge_canary
                    or not DIGEST.fullmatch(args.canary_sha256 or "")
                    or not sys.stdin.isatty()
                    or not re.fullmatch(
                        r"[A-Za-z]:\\(?:[^\\/:\x00-\x1f]+\\)*MRL_Tailnet_Canary\.txt",
                        args.bridge_canary,
                    )
                ):
                    raise ValueError("canary requires its dedicated DL580 path, SHA-256 and an interactive Mac terminal")
            print(json.dumps(collect(args)))
        else:
            print(json.dumps(reconcile(args)))
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"Receipt error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
