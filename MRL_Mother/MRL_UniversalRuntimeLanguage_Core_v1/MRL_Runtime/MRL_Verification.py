# MRL_Verification
# origin_signature: MrLiouWord
# layer: MRL_Runtime
"""驗證層：roundtrip / proof / trace / runtime / world consistency 驗證。

對 RuntimeResult 執行六項驗收（與 acceptance/§10 對齊），全通過輸出：
    MRL_RUNTIME_ACCEPTANCE_PASS
"""

from __future__ import annotations

from typing import Any, Dict, List

ORIGIN_SIGNATURE = "MrLiouWord"
ACCEPTANCE_TOKEN = "MRL_RUNTIME_ACCEPTANCE_PASS"
CANONICAL_NAMING_TOKEN = "MRL_CANONICAL_NAMING_VERIFICATION_PASS"


def verify(result: Dict[str, Any]) -> Dict[str, Any]:
    checks: List[Dict[str, Any]] = []

    def add(name: str, passed: bool, detail: str) -> None:
        checks.append({"check": name, "pass": bool(passed), "detail": detail})

    sf = result.get("structurefield", {})
    add(
        "A_RuntimeStructureField_build",
        sf.get("node_count", 0) > 0 and bool(sf.get("structurefield_hash")),
        f"node_count={sf.get('node_count')} structurefield_hash={str(sf.get('structurefield_hash'))[:8]}",
    )

    replay = result.get("replay", {})
    add("B_ReplayStructureField_exactness", replay.get("exact") is True, f"replay.hash={str(replay.get('hash'))[:8]}")

    restore = result.get("restore", {})
    add("C_RestoreStructureField_exactness", restore.get("exact") is True,
        f"from_step={restore.get('from_step')} restore.hash={str(restore.get('hash'))[:8]}")

    ploop = result.get("persistent_loop", {})
    add("D_PersistentLoop_survives_restart", ploop.get("survives_restart") is True,
        f"iteration={ploop.get('iteration')}")

    world = result.get("world", {})
    add("E_WorldRuntime_synchronization", world.get("synchronization_active") is True,
        f"world_count={world.get('world_count')}")

    rt = result.get("roundtrip", {})
    add("F_Verification_roundtrip_exact", rt.get("exact") is True,
        f"roundtrip checksum match={rt.get('exact')}")

    all_pass = all(c["pass"] for c in checks)
    return {
        "origin_signature": ORIGIN_SIGNATURE,
        "checks": checks,
        "passed": sum(1 for c in checks if c["pass"]),
        "total": len(checks),
        "acceptance": all_pass,
        "token": ACCEPTANCE_TOKEN if all_pass else "MRL_RUNTIME_ACCEPTANCE_FAIL",
    }


def verify_canonical_naming() -> Dict[str, Any]:
    """Canonical naming verification（v2）：主線無 canonical MetaIR/Graph/Attention；
    舊名僅允許作 compatibility alias 且指向單一 canonical 實作。"""
    import MRL_UniversalRuntimeLanguage_Core_v1 as core
    from MRL_UniversalRuntimeLanguage_Core_v1.MRL_Language import MRL_MetaIR, MRL_MrLiouIR_Compiler
    from MRL_UniversalRuntimeLanguage_Core_v1.MRL_Runtime import (
        MRL_RuntimeGraph,
        MRL_RuntimeGraph_Builder,
        MRL_RuntimeStructureField,
    )

    checks: List[Dict[str, Any]] = []

    def add(name: str, passed: bool, detail: str) -> None:
        checks.append({"check": name, "pass": bool(passed), "detail": detail})

    pipe = " ".join(core.CANONICAL_PIPELINE)
    add("pipeline_no_canonical_MetaIR", "MetaIR" not in pipe, pipe)
    add("pipeline_no_canonical_Graph", "Graph" not in pipe, pipe)
    add("pipeline_no_canonical_Attention", "Attention" not in pipe, pipe)

    name_map_keys = " ".join(core.CANONICAL_NAME_MAP.keys())
    add("namemap_no_canonical_MetaIR", "MetaIR" not in name_map_keys, name_map_keys)
    add("namemap_no_canonical_Graph", "Graph" not in name_map_keys, name_map_keys)

    subjects = core.CANONICAL_SUBJECTS
    add("canonical_subjects_present",
        all(k in subjects for k in ("MRL_MrLiouIR", "MRL_StructureField", "Perception")),
        ",".join(subjects.keys()))

    # 舊名僅作 compatibility alias 且委派至單一 canonical 實作（不平行）
    add("alias_MetaIR_points_canonical", MRL_MetaIR is MRL_MrLiouIR_Compiler, "MRL_MetaIR→MrLiouIR_Compiler")
    # MRL_RuntimeGraph → compat shim（保留 legacy graph_hash/edges 契約）；shim 委派 canonical
    add("alias_RuntimeGraph_is_compat_shim", MRL_RuntimeGraph is MRL_RuntimeGraph_Builder,
        "MRL_RuntimeGraph→MRL_RuntimeGraph_Builder(shim)")
    add("shim_delegates_single_canonical",
        getattr(MRL_RuntimeGraph_Builder, "_sf", None) is MRL_RuntimeStructureField,
        "shim viz 委派 MRL_RuntimeStructureField（單一真實來源）")
    add("compat_aliases_declared",
        core.COMPATIBILITY_ALIASES.get("MetaIR") == "MRL_MrLiouIR"
        and core.COMPATIBILITY_ALIASES.get("RuntimeGraph") == "MRL_RuntimeStructureField",
        "MetaIR/RuntimeGraph declared as alias")

    all_pass = all(c["pass"] for c in checks)
    return {
        "origin_signature": ORIGIN_SIGNATURE,
        "checks": checks,
        "passed": sum(1 for c in checks if c["pass"]),
        "total": len(checks),
        "acceptance": all_pass,
        "token": CANONICAL_NAMING_TOKEN if all_pass else "MRL_CANONICAL_NAMING_VERIFICATION_FAIL",
    }
