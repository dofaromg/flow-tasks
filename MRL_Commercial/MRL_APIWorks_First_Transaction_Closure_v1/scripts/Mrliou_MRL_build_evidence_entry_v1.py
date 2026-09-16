#!/usr/bin/env python3
"""Build a private offline review for the existing APIWorks BYOH product."""

from __future__ import annotations

import argparse
import html
import json
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from Mrliou_MRL_verify_evidence_entry_v1 import (
    BUNDLE, MUTABLE, digest, safe_name, verify_directory, verify_zip,
)

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
RUNTIME = Path("MRL_Mother/MRL_MotherModel/MRL_AI_Mother_Autonomous_Runtime_Baseline_v1")
PRODUCT = Path("MRL_Products/MRL_APIWorks_BYOH_Deployment_Product_v1")
CLOSURE = ROOT.relative_to(REPO)
TEST_FILE = RUNTIME / "tests/test_MRL_autonomous_runtime_v1.py"
WORKFLOW = Path(".github/workflows/mrl-apiworks-production-delivery.yml")
CHECKS = [
    ("runtime_source", RUNTIME, ["scripts/MRL_verify_package_v1.py"]),
    ("runtime_tests", RUNTIME, ["-m", "unittest", "discover", "-s", "tests", "-v"]),
    ("product_source", PRODUCT, ["scripts/MRL_verify_product_source_v1.py"]),
    ("product_tests", PRODUCT, ["-m", "unittest", "discover", "-s", "tests", "-v"]),
    ("closure_source", CLOSURE, ["scripts/MRL_verify_commercial_closure_pack_v1.py"]),
    ("closure_tests", CLOSURE, ["-m", "unittest", "discover", "-s", "tests", "-v"]),
]
BASE_OUTPUT = [
    "index.html", "README.md", "DEPENDENCY_TREE.md", "EVIDENCE_LEDGER.json",
    "SOURCE_INVENTORY.json", "SOURCE_ROLES.json", "EXPECTED_PRODUCT_FILES.json",
    "Expected_File_List.txt", "SHA256SUMS.txt", "VERIFY_EVIDENCE.py", BUNDLE,
]


def write_json(path: Path, value: Any) -> None:
    """Write stable UTF-8 JSON for review, not a signature."""
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def git(*args: str) -> str:
    """Read local Git metadata without network operations."""
    return subprocess.check_output(["git", *args], cwd=REPO, text=True).strip()


def collect_sources() -> dict[str, dict[str, Any]]:
    """Freeze the expected inventory before invoking tests or the ZIP build."""
    inventory: dict[str, dict[str, Any]] = {}
    for package in (RUNTIME, PRODUCT, CLOSURE):
        names = [line.strip() for line in (REPO / package / "EXPECTED_FILE_LIST.txt").read_text().splitlines() if line.strip()]
        if not names or len(names) != len(set(names)) or any(not safe_name(name) for name in names):
            raise ValueError("invalid expected list: " + str(package))
        for name in names:
            relative = package / name
            path = REPO / relative
            if path.is_symlink() or not path.is_file() or not path.stat().st_size:
                raise ValueError("missing, linked, or empty source: " + str(relative))
            if not path.resolve().is_relative_to(REPO.resolve()):
                raise ValueError("source escapes repository")
            data = path.read_bytes()
            inventory[relative.as_posix()] = {"size_bytes": len(data), "sha256": digest(data)}
    workflow_bytes = (REPO / WORKFLOW).read_bytes()
    inventory[str(WORKFLOW)] = {"size_bytes": len(workflow_bytes), "sha256": digest(workflow_bytes)}
    return dict(sorted(inventory.items()))


def source_roles(paths: list[Path]) -> dict[str, Any]:
    """Keep declared origin, Git authors and committers in separate fields."""
    records = []
    for path in paths:
        rows = git("log", "--follow", "--format=%H%x1f%aI%x1f%an%x1f%cI%x1f%cn", "--", str(path)).splitlines()
        history = []
        for row in rows:
            commit, author_date, author, committer_date, committer = row.split("\x1f")
            history.append({"commit": commit, "author_date": author_date, "author": author,
                            "committer_date": committer_date, "committer": committer})
        records.append({"path": str(path), "history_newest_first": history,
                        "earliest_reachable_record": history[-1] if history else None})
    return {
        "declared_origin_signature": "MrLiouWord",
        "declaration_source": str(PRODUCT / "PRODUCT_SKU.json"),
        "interpretation": "Git actors describe recorded changes, not adjudicated conceptual authorship. Dates are Git metadata, not independently proved creation/publication dates. AI-looking names are not proof of autonomous invention.",
        "records": records,
    }


def content_mappings() -> list[dict[str, Any]]:
    """Map actual operations to implementation symbols and exercised tests."""
    definitions = RUNTIME / "README.md"
    rows = [
        ("本機模型邊界", "loopback only", "MRL_local_model_adapter_v1.py", "require_loopback_endpoint", "test_rejects_external_model_endpoint"),
        ("輸入到記憶／證據／Passport", "append-only", "MRL_mother_runtime_v1.py", "self.memory.remember", "test_full_runtime_loop_persists_memory_evidence_and_passport"),
        ("記憶完整性", "SHA-256 chain", "MRL_hash_chain_v1.py", "class MRLHashChain", "test_hash_chain_detects_tampering"),
        ("來源版本追加", "additive, versioned passports", "MRL_passport_registry_v1.py", "class MRLPassportRegistry", "test_passport_versions_are_additive"),
        ("使用者同意後選檔回傳", "never uploads automatically", "MRL_return_bundle_v1.py", "def build_return_bundle", "test_return_bundle_requires_explicit_consent"),
    ]
    result = []
    for operation, definition_anchor, filename, code_anchor, test in rows:
        implementation = RUNTIME / "runtime" / filename
        checks = [(definitions, definition_anchor), (implementation, code_anchor), (TEST_FILE, "def " + test)]
        for path, anchor in checks:
            if anchor not in (REPO / path).read_text():
                raise ValueError(f"content anchor missing: {path}: {anchor}")
        result.append({"operation": operation, "definition": str(definitions),
                       "definition_anchor": definition_anchor, "implementation": str(implementation),
                       "implementation_anchor": code_anchor, "test_file": str(TEST_FILE),
                       "test": test, "test_log": "logs/runtime_tests.txt",
                       "basis": "FILE_CONTENT_ANCHORS_AND_EXECUTED_TEST_SUITE"})
    return result


def render_index(ledger: dict[str, Any], expected: list[str]) -> str:
    """Render a self-contained, escaped, script-free review entrance."""
    def link(path: str, label: str | None = None) -> str:
        return f'<a href="{html.escape(path, quote=True)}">{html.escape(label or path)}</a>'
    rows = "".join(
        "<tr><td>" + html.escape(row["operation"]) + "</td><td>"
        + link("source/" + row["definition"], row["definition_anchor"]) + "</td><td>"
        + link("source/" + row["implementation"], row["implementation_anchor"]) + "</td><td>"
        + link("source/" + row["test_file"], row["test"]) + "</td></tr>"
        for row in ledger["content_mappings"]
    )
    layers = "".join("<li>" + html.escape(row["name"] + "：" + row["status"]) + "</li>" for row in ledger["layers"])
    log_links = " · ".join(link(check["log"], check["id"]) for check in ledger["checks"])
    return f'''<!doctype html>
<html lang="zh-Hant"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>MRL APIWorks｜可驗證入口</title>
<style>body{{font:16px/1.7 system-ui,sans-serif;max-width:1120px;margin:40px auto;padding:0 24px;color:#14283b;background:#f5f8fa}}h1,h2{{line-height:1.3}}section{{background:white;padding:22px;margin:20px 0;border:1px solid #d7e2e9;border-radius:12px}}table{{border-collapse:collapse;width:100%;font-size:14px}}td,th{{border:1px solid #d7e2e9;padding:10px;text-align:left;overflow-wrap:anywhere}}a{{color:#075b9a}}code{{overflow-wrap:anywhere}}.scroll{{overflow:auto}}</style>
<h1>MRL APIWorks｜可驗證入口</h1>
<p>觀測紀錄 → 定義 → 程式 → 驗證 → 實際交付。origin_signature: MrLiouWord</p>
<section><h2>01｜這個產品實際交付什麼</h2><p>既有 BYOH 單節點本機模型部署，含 Memory／Evidence／Passport 記錄與 30 天安裝穩定支援。模型權重、硬體與付款處理不包含在 ZIP 中。</p>
<p>{link('source/' + str(PRODUCT / 'docs/MRL_PRODUCT_SPEC_v1.md'), '商品規格')} · {link('source/' + str(PRODUCT / 'docs/MRL_DELIVERY_ACCEPTANCE_v1.md'), '安裝與驗收')} · {link(BUNDLE, '下載本次重建商品 ZIP')}</p>
<p>版本 {html.escape(ledger['product_version'])}；工程驗證 {html.escape(ledger['engineering_gate'])}；<strong>客戶現場驗收與收入：本輪未觀測，不推定完成。</strong></p></section>
<section><h2>02｜內容交叉比對</h2><p>逐項對照操作、定義原文、實作與測試，不以名稱相似代替內容。</p><div class="scroll"><table><tr><th>操作</th><th>定義依據</th><th>實作錨點</th><th>測試</th></tr>{rows}</table></div></section>
<section><h2>03｜五層證據與邊界</h2><ul>{layers}</ul><p>{link('EVIDENCE_LEDGER.json', '完整台帳')} · {link('SOURCE_ROLES.json', '來源角色／Git 時間紀錄')} · {link('SOURCE_INVENTORY.json', '源碼尺寸與 SHA-256')}</p></section>
<section><h2>04｜自行重跑</h2><p><code>python VERIFY_EVIDENCE.py .</code></p><p>此指令只核對入口完整性；重新執行工程測試請依 {link('README.md')} 操作。歷史測試紀錄不是現在客戶設備已通過。</p><p>{log_links}</p><p>{link('Expected_File_List.txt')} · {link('DEPENDENCY_TREE.md')} · {link('SHA256SUMS.txt')}</p></section>
<section><h2>05｜尚待真實輸入</h2><p>客戶簽署訂單、已確認款項、授權節點與模型、現場驗收、撥款對帳及收入紀錄。這些是獨立狀態；不以缺少下游事件否認已完成工程，也不以工程通過虛構交易。</p><p>完整 MRL 歷史原件與外部來源鏈尚未在本產品入口全面閉合。</p></section>
<footer><p>本機私人審閱包 · {len(expected)} 個預期檔案 · 無追蹤器、外部字型或自動上傳。<br>觀測時間 {html.escape(ledger['observed_at_utc'])}；Git HEAD <code>{html.escape(ledger['source_head'])}</code>。封包雜湊須另外保存在可信紀錄；雜湊不是作者身分簽章。</p></footer></html>'''


def build(output: Path) -> dict[str, Any]:
    """Fail closed and preserve incomplete output for diagnosis on failure."""
    output = output.resolve()
    if output.is_relative_to(REPO.resolve()) or REPO.resolve().is_relative_to(output):
        raise ValueError("output must be outside the repository and not its ancestor")
    if output.exists():
        raise ValueError("output already exists; choose a new directory")
    inventory = collect_sources()
    mappings = content_mappings()
    expected_zip = {name: identity for name, identity in inventory.items()
                    if name.startswith(str(RUNTIME) + "/") or name.startswith(str(PRODUCT) + "/")}
    expected_zip[MUTABLE] = inventory[str(RUNTIME / "config/MRL_runtime.local.example.json")]
    expected = sorted(BASE_OUTPUT + ["source/" + name for name in inventory]
                      + [f"logs/{name}.txt" for name, _, _ in CHECKS])
    output.mkdir(parents=True)
    (output / "logs").mkdir()
    (output / "Expected_File_List.txt").write_text("\n".join(expected) + "\n")
    checks = []
    for name, package, arguments in CHECKS:
        command = [sys.executable, *arguments]
        completed = subprocess.run(command, cwd=REPO / package, capture_output=True,
                                   text=True, timeout=300, check=False)
        log = f"logs/{name}.txt"
        (output / log).write_text(completed.stdout + completed.stderr, encoding="utf-8")
        checks.append({"id": name, "cwd": str(package), "argv": ["python", *arguments],
                       "returncode": completed.returncode, "log": log})
        print(f"{name}: exit={completed.returncode}", flush=True)
        if completed.returncode:
            raise RuntimeError(f"{name} failed; inspect {output / log}")
    if collect_sources() != inventory:
        raise RuntimeError("source changed during validation")
    for name in inventory:
        target = output / "source" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO / name, target)
    shutil.copy2(REPO / PRODUCT / "dist" / BUNDLE, output / BUNDLE)
    zip_failures = verify_zip(output / BUNDLE, expected_zip)
    if zip_failures:
        raise RuntimeError("ZIP inventory verification: " + repr(zip_failures))
    roles = source_roles([PRODUCT / "PRODUCT_SKU.json", RUNTIME / "runtime/MRL_mother_runtime_v1.py",
                          RUNTIME / "runtime/MRL_hash_chain_v1.py", Path(__file__).relative_to(REPO)])
    manifest = json.loads((REPO / PRODUCT / "MANIFEST.json").read_text())
    blob = (output / BUNDLE).read_bytes()
    dirty = git("status", "--porcelain", "--", str(RUNTIME), str(PRODUCT), str(CLOSURE), str(WORKFLOW))
    ledger = {
        "schema": "Mrliou_MRL_APIWorks_Evidence_Entry_v1",
        "scope": "EXISTING_APIWORKS_BYOH_PRODUCT_PRIVATE_REVIEW",
        "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_head": git("rev-parse", "HEAD"), "source_worktree_changes": dirty.splitlines(),
        "source_is_exact_head_for_reviewed_packages": not bool(dirty),
        "source_inventory_sha256": digest(json.dumps(inventory, sort_keys=True).encode()),
        "environment": {"python": platform.python_version(), "system": platform.system()},
        "product_version": manifest["version"], "canonical_id": manifest["canonical_id"],
        "origin_signature": manifest["origin_signature"],
        "engineering_gate": "LOCAL_PRODUCT_REVIEW_PASS",
        "global_mrl_completion": "NOT_ASSERTED",
        "artifact": {"path": BUNDLE, "size_bytes": len(blob), "sha256": digest(blob)},
        "checks": checks, "content_mappings": mappings,
        "layers": [
            {"name": "原始材料", "status": "已保留選定檔案的可達 Git 歷史；不是全部 MRL 原件或最初創作時間證明"},
            {"name": "定義", "status": "已保存商品規格／驗收／資料邊界及內容對照；未改寫母體定義"},
            {"name": "程式與測試", "status": "本輪本機測試通過；模型使用測試替身，非客戶真實模型驗收"},
            {"name": "來源角色", "status": "產品宣告來源與 Git 作者／提交者分欄；不由提交角色推定概念作者"},
            {"name": "產品與客戶價值", "status": "本輪商品 ZIP 可驗證；未取得真實交易、客戶驗收或收入證據"},
        ],
        "commercial_observation": {key: "NOT_OBSERVED_THIS_RUN" for key in (
            "signed_order", "payment", "customer_deployment", "real_model_acceptance",
            "customer_acceptance", "payout", "realized_revenue")},
    }
    write_json(output / "SOURCE_INVENTORY.json", inventory)
    write_json(output / "SOURCE_ROLES.json", roles)
    write_json(output / "EXPECTED_PRODUCT_FILES.json", expected_zip)
    write_json(output / "EVIDENCE_LEDGER.json", ledger)
    shutil.copy2(ROOT / "scripts/Mrliou_MRL_verify_evidence_entry_v1.py", output / "VERIFY_EVIDENCE.py")
    (output / "README.md").write_text(
        "# MRL APIWorks offline evidence review\n\nOpen index.html.\n\n"
        "Integrity only: `python VERIFY_EVIDENCE.py .`\n\n"
        "Rerun tests from each source package using argv/cwd in EVIDENCE_LEDGER.json "
        "(cwd is relative to source/). Git provenance needs the original repository. "
        "Local test fixtures are not real-model acceptance.\n\n"
        "The product ZIP is for private staging; follow its product acceptance "
        "document on an authorized node. No customer, payment or deployment has "
        "been inferred. Pin the outer ZIP SHA-256 independently.\n", encoding="utf-8")
    (output / "DEPENDENCY_TREE.md").write_text(
        "# Expected dependency structure\n\n"
        "| Consumer | Required dependency | Validation |\n| --- | --- | --- |\n"
        "| Offline index | Ledger, source copies, role record, logs | Exact file/hash inventory |\n"
        "| Product ZIP | Runtime 32 files, product 13 files, external mutable config, manifest | Pre-build inventory + ZIP manifest checks |\n"
        "| Runtime | Python standard library, user-owned model service | Loopback integration fixtures only here |\n"
        "| Evidence builder | Python 3.10+, Git, existing three source packages | Six verifier/test commands |\n"
        "| Customer acceptance | Authorized node, installed model, customer configuration | Requires separate real evidence |\n"
        "| Transaction closure | Signed order, payment, deployment, acceptance, payout, ledger | Not observed in this build |\n",
        encoding="utf-8")
    (output / "index.html").write_text(render_index(ledger, expected), encoding="utf-8")
    sums = [digest((output / name).read_bytes()) + "  " + name
            for name in expected if name != "SHA256SUMS.txt"]
    (output / "SHA256SUMS.txt").write_text("\n".join(sums) + "\n")
    result = verify_directory(output)
    if result["integrity_gate"] != "PASS":
        raise RuntimeError(json.dumps(result))
    return result


def main() -> int:
    """Build to a new private directory and print its actual audit result."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(build(args.output), ensure_ascii=False, indent=2))
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        print(f"EVIDENCE_ENTRY_BUILD_FAIL: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
