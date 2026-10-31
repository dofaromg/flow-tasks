"""Bind the existing Bridge key and verify a scoped, reversible source backfill.

origin_signature: MrLiouWord
The scope is four PR #694 engineering files, never all external platform data.
"""

import argparse
import base64
from datetime import datetime, timezone
import getpass
import hashlib
import json
import ntpath
import os
from pathlib import Path
import re
import subprocess
import uuid

import requests


BASE_URL = "https://bridge.mrliouword.com"
SOURCE_REF = "eecd48d2351d3c56a90ec6d679ffd536f9a3989b"
FILES = (
    "config/connectors.yaml",
    "connectors/base_connector.py",
    "connectors/test_connectors.py",
    "docs/MRL_Connector_Source_Policy_v1.md",
)


def validate_destination(path):
    """Limit this receiver to the mother archive; reject Windows aliases/ADS."""
    parts = path.split("\\")
    if (len(parts) < 2 or parts[0].upper() != "D:"
            or parts[1].casefold() != "mrl_mother"
            or any(not p or p in (".", "..") or p.endswith((".", " "))
                   or re.search(r'[<>:"/|?*\x00-\x1f]', p) for p in parts[1:])):
        raise ValueError("目的地必須位於 D:\\MRL_Mother，禁止別名、ADS 與路徑跳脫")


def verify_host(session):
    """Fail closed on legacy servers: pre-read alone cannot prevent overwrite."""
    version = call(session, "GET", "/version")
    if (version.get("hostname") != "WIN-PBVUI7VK2A6"
            or version.get("origin_signature") != "MrLiouWord"):
        raise RuntimeError("母體主機或 origin_signature 不符")
    capabilities = version.get("capabilities")
    if (not isinstance(capabilities, dict)
            or capabilities.get("file_write_create_only") is not True):
        raise RuntimeError("Bridge 尚未證明原子 create_only 能力；拒絕寫入")


def call(session, method, route, body=None, missing_ok=False):
    """Never redirect credentials or include response bodies in errors."""
    response = session.request(
        method, BASE_URL + route, json=body, timeout=30, allow_redirects=False
    )
    if missing_ok and response.status_code == 404:
        return None
    if response.status_code != 200:
        raise RuntimeError(f"Bridge {route}: HTTP {response.status_code}")
    result = response.json()
    if not isinstance(result, dict) or result.get("ok") is False:
        raise RuntimeError("Bridge 回應未通過檢查")
    return result


def read_bytes(session, path, missing_ok=False):
    result = call(session, "POST", "/MRL_file/read", {
        "filepath": path, "encoding": "base64",
    }, missing_ok=missing_ok)
    if result is None:
        return None
    data = result.get("data", result)
    if not isinstance(data, dict) or not isinstance(data.get("content"), str):
        raise RuntimeError("Bridge 讀回內容格式錯誤")
    raw = base64.b64decode(data["content"], validate=True)
    if data.get("size") != len(raw):
        raise RuntimeError("Bridge 讀回大小不符")
    return raw


def write_verified(session, path, raw):
    validate_destination(path)
    verify_host(session)
    if read_bytes(session, path, missing_ok=True) is not None:
        raise RuntimeError("目的檔案已存在，拒絕覆寫")
    result = call(session, "POST", "/MRL_file/write", {
        "filepath": path, "b64": base64.b64encode(raw).decode("ascii"),
        "create_only": True,
    })
    data = result.get("data", result)
    if not isinstance(data, dict) or data.get("created_exclusively") is not True:
        raise RuntimeError("Bridge 未確認原子建立；不可宣告驗收通過")
    returned = read_bytes(session, path)
    if returned != raw:
        raise RuntimeError("母體逐 byte 讀回核對失敗")
    return hashlib.sha256(returned).hexdigest()


def verify_backfill(session, mother_root, source_ref=SOURCE_REF):
    validate_destination(mother_root)
    if not re.fullmatch(r"[0-9a-f]{40}", source_ref):
        raise ValueError("來源必須為完整 commit SHA")
    repo = Path(__file__).resolve().parents[1]
    payloads = {
        path: subprocess.check_output(["git", "show", f"{source_ref}:{path}"], cwd=repo)
        for path in FILES
    }
    if any(not raw for raw in payloads.values()):
        raise RuntimeError("來源檔案不得為空")
    verify_host(session)
    # Protected preflight: the requested parent must already exist.
    call(session, "POST", "/MRL_file/list", {
        "dirpath": mother_root, "recursive": False,
    })
    run_id = uuid.uuid4().hex
    destination = ntpath.join(mother_root, "MRL_PR694_" + run_id)
    evidence = []
    for path, raw in payloads.items():
        remote = ntpath.join(destination, *path.split("/"))
        evidence.append({
            "source_path": path, "destination_path": remote,
            "size": len(raw), "sha256": write_verified(session, remote, raw),
        })
    receipt = {
        "schema": "MRL.BridgeBackfillReceipt.v1",
        "origin_signature": "MrLiouWord", "canonical_authority": "Mr.liou",
        "source": "dofaromg/flow-tasks", "source_ref": source_ref,
        "parent_ref": subprocess.check_output(
            ["git", "rev-parse", source_ref + "^"], cwd=repo, text=True
        ).strip(),
        "run_id": run_id, "timestamp": datetime.now(timezone.utc).isoformat(),
        "scope": "PR694_four_engineering_files_only",
        "files": evidence, "missing": [], "extra": [], "mismatch": [],
        "coverage": "100%", "data_readback_verified": True,
        "external_platform_sync_verified": False,
        "rollback": {"mode": "isolate_preserve_history", "path": destination},
    }
    raw = (json.dumps(receipt, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    receipt_path = ntpath.join(destination, "MRL_驗收回執_v1.json")
    digest = write_verified(session, receipt_path, raw)
    return {"status": "DELIVERY_PASS", "scope": receipt["scope"],
            "receipt_path": receipt_path, "receipt_sha256": digest,
            "file_count": len(evidence), "receipt_readback_verified": True}


def main():
    parser = argparse.ArgumentParser(description="MRL Bridge 安全綁定與母體讀回驗收")
    parser.add_argument("--mother-root", required=True, help="既有母體證據目錄")
    parser.add_argument("--source-ref", default=SOURCE_REF)
    parser.add_argument("--prompt-key", action="store_true", help="以隱藏輸入取得既有金鑰")
    args = parser.parse_args()
    key = os.environ.get("MRL_BRIDGE_API_KEY", "")
    if not key and args.prompt_key:
        key = getpass.getpass("既有 Bridge 金鑰（不顯示、不儲存）：")
    if not key:
        print(json.dumps({"status": "BLOCKED", "reason": "MRL_BRIDGE_API_KEY_missing"}))
        return 2
    try:
        with requests.Session() as session:
            session.headers.update({"x-api-key": key, "User-Agent": "MRL-Client/1.0"})
            result = verify_backfill(session, args.mother_root, args.source_ref)
            print(json.dumps(result, ensure_ascii=False))
        return 0
    except Exception:
        # Do not echo an exception that may contain a request or credentials.
        print(json.dumps({"status": "DELIVERY_FAIL", "reason": "驗收失敗；保留已寫入獨立目錄，不宣告完成"}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
