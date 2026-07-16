"""
test_MRL_universal_runtime_core.py — MRL_UniversalRuntimeLanguage_Core_v1 驗收
origin_signature: MrLiouWord

涵蓋：parser 多語言、MrLiouIR 確定性、ParticleIR 可逆、Replay/Restore exact、
PersistentLoop 重啟存活、WorldRuntime 同步、Verification 六項 PASS、DB adapter、
v2 canonical 命名與 compatibility alias。
"""
from __future__ import annotations

import pytest

from MRL_UniversalRuntimeLanguage_Core_v1 import (
    CANONICAL_PIPELINE,
    COMPATIBILITY_ALIASES,
    ORIGIN_SIGNATURE,
    SOVEREIGNTY,
)
from MRL_UniversalRuntimeLanguage_Core_v1.MRL_Language import (
    MRL_MrLiouIR_Compiler,
    MRL_ParticleIR_Engine,
    MRL_UniversalParser_Core,
)
from MRL_UniversalRuntimeLanguage_Core_v1.MRL_DB.MRL_BaseWorld_DB_Adapter import (
    ATTACHMENT_POINTS,
    MRL_BaseWorld_DB_Adapter,
)
from MRL_UniversalRuntimeLanguage_Core_v1.MRL_Runtime.MRL_DL580_Runtime import MRL_DL580_Runtime

SAMPLE_PY = (
    "import os\n\n"
    "def greet(name):\n"
    "    msg = 'hi ' + name\n"
    "    return msg\n\n"
    "class World:\n"
    "    def spin(self):\n"
    "        for i in range(3):\n"
    "            print(i)\n"
)


def test_sovereignty_constants():
    assert ORIGIN_SIGNATURE == "MrLiouWord"
    assert SOVEREIGNTY["subject"] == "MRL_Mother_Runtime"
    assert SOVEREIGNTY["deploy_host"] == "DL580"
    assert "Cloudflare" in SOVEREIGNTY["external_mirror_layer"]
    assert SOVEREIGNTY["perception_is_subject"] is True


@pytest.mark.parametrize("lang,src", [
    ("python", "def f(x):\n    return x\n"),
    ("typescript", "export function f() {\n  return 1;\n}\n"),
    ("cpp", "#include <x>\nint main(){\n return 0;\n}\n"),
    ("json", '{"a":1,"b":[1,2]}'),
    ("markdown", "# H\n\n- a\n\ntext\n"),
])
def test_parser_multilang(lang, src):
    r = MRL_UniversalParser_Core.parse(src, lang)
    assert r["lang"] == lang
    assert r["unit_count"] >= 1
    assert r["origin_signature"] == "MrLiouWord"


def test_mrliouir_deterministic():
    parsed = MRL_UniversalParser_Core.parse(SAMPLE_PY, "python")
    a = MRL_MrLiouIR_Compiler.compile_mrliouir(parsed)
    b = MRL_MrLiouIR_Compiler.compile_mrliouir(parsed)
    assert a["mrliouir_hash"] == b["mrliouir_hash"]
    assert a["node_count"] > 0


def test_v2_canonical_pipeline():
    # 主線 canonical 不得使用 MetaIR / Graph / Attention
    joined = " ".join(CANONICAL_PIPELINE)
    assert "MrLiouIR" in joined and "StructureField" in joined
    assert "MetaIR" not in joined
    assert "Graph" not in joined


def test_compatibility_aliases():
    import MRL_UniversalRuntimeLanguage_Core_v1.MRL_Language as L
    import MRL_UniversalRuntimeLanguage_Core_v1.MRL_Runtime as R
    # 舊名仍可用：MetaIR→canonical compiler；RuntimeGraph→compat shim（保留 legacy 契約）
    assert L.MRL_MetaIR is L.MRL_MrLiouIR_Compiler
    assert R.MRL_RuntimeGraph is R.MRL_RuntimeGraph_Builder           # 指向 shim，非 canonical 模組
    assert R.MRL_RuntimeGraph_Builder._sf is R.MRL_RuntimeStructureField  # shim 委派單一 canonical
    # 舊 compile_metair 鏡射舊鍵供兼容
    parsed = MRL_UniversalParser_Core.parse(SAMPLE_PY, "python")
    legacy = L.MRL_MetaIR_Compiler.compile_metair(parsed)
    assert legacy["metair_hash"] == legacy["mrliouir_hash"]
    # 宣告層：COMPATIBILITY_ALIASES 標明 MetaIR/Graph 降級
    assert COMPATIBILITY_ALIASES["MetaIR"] == "MRL_MrLiouIR"
    assert COMPATIBILITY_ALIASES["RuntimeGraph"] == "MRL_RuntimeStructureField"


def test_runtime_structurefield_alias_keys():
    from MRL_UniversalRuntimeLanguage_Core_v1.MRL_Runtime import (
        MRL_RuntimeGraph_Builder,
        MRL_RuntimeStructureField,
    )
    parsed = MRL_UniversalParser_Core.parse(SAMPLE_PY, "python")
    mr = MRL_MrLiouIR_Compiler.compile_mrliouir(parsed)
    sf = MRL_RuntimeStructureField.build(mr)
    assert "structurefield_hash" in sf and "relations" in sf
    # alias shim 鏡射舊 *graph* 鍵
    legacy = MRL_RuntimeGraph_Builder.build(mr)
    assert legacy["graph_hash"] == sf["structurefield_hash"]
    assert legacy["edges"] == sf["relations"]
    assert legacy["replay_graph"] == sf["replay_structurefield"]
    # 回歸：legacy graph 物件（僅 nodes/edges/graph_hash，如舊存檔）餵入 shim viz 不得 KeyError
    legacy_obj = {"nodes": sf["nodes"], "edges": sf["relations"], "graph_hash": sf["structurefield_hash"]}
    assert isinstance(MRL_RuntimeGraph_Builder.to_mermaid(legacy_obj), str)
    assert isinstance(MRL_RuntimeGraph_Builder.to_dot(legacy_obj), str)
    assert isinstance(MRL_RuntimeGraph_Builder.to_json(legacy_obj), str)


def test_particle_chain_reversible():
    text = "alpha beta\nbeta alpha gamma\n"
    trace = MRL_ParticleIR_Engine.to_particles(text)
    assert MRL_ParticleIR_Engine.from_particles(trace) == text
    env = MRL_ParticleIR_Engine.collapse(text)
    assert MRL_ParticleIR_Engine.expand(env) == text
    jumped, perm = MRL_ParticleIR_Engine.jump(text)
    assert MRL_ParticleIR_Engine.unjump(jumped, perm) == text


def test_db_adapter_local_emulation():
    db = MRL_BaseWorld_DB_Adapter().local_emulation()
    db.attach("Trace", "h1", "trace", "{}", 1)
    assert db.count("Trace") == 1
    assert set(ATTACHMENT_POINTS) == {
        "Canon", "Registry", "FLTNZ_Asset", "Memory_Sphere", "Proof", "Trace", "Mirror"
    }
    assert db.status()["prod_schema"]["tables"] == 27


def test_canonical_naming_verification():
    from MRL_UniversalRuntimeLanguage_Core_v1.MRL_Runtime.MRL_Verification import (
        verify_canonical_naming,
    )
    naming = verify_canonical_naming()
    assert naming["acceptance"] is True, naming["checks"]
    assert naming["token"] == "MRL_CANONICAL_NAMING_VERIFICATION_PASS"


def test_full_pipeline_acceptance_pass(tmp_path):
    runtime = MRL_DL580_Runtime(runtime_dir=str(tmp_path))
    result = runtime.run(SAMPLE_PY, lang="python", loop_id="pytest")
    v = result["verification"]
    # 全部六項
    assert v["total"] == 6
    assert v["passed"] == 6, v["checks"]
    assert v["acceptance"] is True
    assert v["token"] == "MRL_RUNTIME_ACCEPTANCE_PASS"
    # 個別保證
    assert result["replay"]["exact"] is True
    assert result["restore"]["exact"] is True
    assert result["persistent_loop"]["survives_restart"] is True
    assert result["world"]["synchronization_active"] is True
    assert result["roundtrip"]["exact"] is True
