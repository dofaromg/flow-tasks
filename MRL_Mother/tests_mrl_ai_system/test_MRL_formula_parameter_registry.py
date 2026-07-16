"""MRL_Formula_Parameter_Registry_v1 驗收測試。

驗證 scripts/MRL_formula_parameter_registry_check.js：
- 預設 registry 全部核心公式參數有 record，輸出 impact report 並 PASS。
- 缺少核心參數或高影響參數自動放行時必須 FAIL。
"""
import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECK_SCRIPT = ROOT / "scripts" / "MRL_formula_parameter_registry_check.js"
REGISTRY = ROOT / "data" / "MRL_formula_parameter_registry.json"


def run_check(registry_path=None):
    cmd = ["node", str(CHECK_SCRIPT)]
    if registry_path is not None:
        cmd.append(str(registry_path))
    return subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)


def test_registry_check_passes_and_outputs_impact_report():
    result = run_check()
    assert result.returncode == 0, result.stderr
    assert "MRL_FORMULA_PARAMETER_REGISTRY_PASS" in result.stdout
    report_text = result.stdout.rsplit("MRL_FORMULA_PARAMETER_REGISTRY_PASS", 1)[0]
    report = json.loads(report_text)
    assert report["report_name"] == "MRL_Formula_Parameter_Impact_Report_v1"
    assert report["origin_signature"] == "MrLiouWord"
    assert report["total_parameters"] == 23
    assert report["impact_summary"]["high"] > 0
    assert len(report["formulas"]) == 6


def test_registry_check_fails_when_core_parameter_missing(tmp_path):
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    registry["records"] = [
        r for r in registry["records"] if r["parameter_name"] != "eta_k"
    ]
    broken = tmp_path / "registry.json"
    broken.write_text(json.dumps(registry), encoding="utf-8")
    result = run_check(broken)
    assert result.returncode == 1
    assert "eta_k" in result.stderr
    assert "MRL_FORMULA_PARAMETER_REGISTRY_FAIL" in result.stderr


def test_registry_check_fails_when_high_impact_auto_released(tmp_path):
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    for record in registry["records"]:
        if record["impact_scope"] == "high":
            record["verification_status"] = "pending"
            break
    broken = tmp_path / "registry.json"
    broken.write_text(json.dumps(registry), encoding="utf-8")
    result = run_check(broken)
    assert result.returncode == 1
    assert "parameter_review" in result.stderr
    assert "MRL_FORMULA_PARAMETER_REGISTRY_FAIL" in result.stderr
