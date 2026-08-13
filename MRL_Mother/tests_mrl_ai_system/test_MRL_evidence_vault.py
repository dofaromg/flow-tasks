from __future__ import annotations

import importlib.util
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "06_trace" / "MRL_EvidenceVault_v1.py"
spec = importlib.util.spec_from_file_location("MRL_EvidenceVault_v1", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)

MRL_EvidenceVault = module.MRL_EvidenceVault
verify_ledger = module.verify_ledger


def test_append_only_evidence_chain(tmp_path: Path):
    ledger = tmp_path / "evidence.jsonl"
    vault = MRL_EvidenceVault(ledger)

    r1 = vault.append(
        source_type="github",
        source_name="dofaromg/flow-tasks",
        source_ref="commit:before",
        actor="external",
        canonical_name="FlowAgent",
        external_name="VendorRenamedAgent",
        event_type="rename_observed",
        before={"name": "FlowAgent"},
        after={"name": "VendorRenamedAgent"},
        payload={"note": "external presentation changed"},
        observed_at="2026-08-13T05:12:00Z",
    )
    r2 = vault.append(
        source_type="github",
        source_name="dofaromg/flow-tasks",
        source_ref="commit:after",
        actor="external",
        canonical_name="FlowAgent",
        external_name="AnotherAlias",
        event_type="second_observation",
        before={"name": "VendorRenamedAgent"},
        after={"name": "AnotherAlias"},
        observed_at="2026-08-13T05:13:00Z",
    )

    result = verify_ledger(ledger)
    assert result["valid"] is True
    assert result["records"] == 2
    assert r2.previous_record_hash == r1.record_hash()
    assert r1.canonical_name == "FlowAgent"
    assert r2.canonical_name == "FlowAgent"


def test_tamper_is_detected(tmp_path: Path):
    ledger = tmp_path / "evidence.jsonl"
    vault = MRL_EvidenceVault(ledger)
    vault.append(
        source_type="test",
        source_name="test",
        source_ref="1",
        actor="test",
        canonical_name="MRL",
        external_name="external",
        event_type="observe",
        before=None,
        after={"x": 1},
        observed_at="2026-08-13T05:12:00Z",
    )
    vault.append(
        source_type="test",
        source_name="test",
        source_ref="2",
        actor="test",
        canonical_name="MRL",
        external_name="external2",
        event_type="observe",
        before={"x": 1},
        after={"x": 2},
        observed_at="2026-08-13T05:13:00Z",
    )

    lines = ledger.read_text(encoding="utf-8").splitlines()
    lines[0] = lines[0].replace('"external_name": "external"', '"external_name": "tampered"')
    ledger.write_text("\n".join(lines) + "\n", encoding="utf-8")
    result = verify_ledger(ledger)
    assert result["valid"] is False
