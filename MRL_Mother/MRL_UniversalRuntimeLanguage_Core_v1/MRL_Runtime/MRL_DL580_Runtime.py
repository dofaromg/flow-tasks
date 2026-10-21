# MRL_DL580_Runtime
# origin_signature: MrLiouWord
# layer: MRL_Runtime (母體自運行節點 = DL580)
"""DL580 Runtime 編排器：執行正式 Runtime 全管線（v2 canonical）。

    Input → MrLiouIR → ParticleIR → RuntimeStructureField → ReplayStructureField
          → RestoreStructureField → Verification → WorldRuntime → PersistentLoop

對外語義：Input → Observe → Parse → MrLiouIR → ParticleIR → StructureField
          → Verification → Replay → Restore → WorldRuntime → PersistentLoop。
禁止 Prompt→LLM→Output。run() 回傳 RuntimeResult，供 MRL_Verification 驗收。
"""

from __future__ import annotations

import tempfile
from typing import Any, Dict, Optional

from MRL_UniversalRuntimeLanguage_Core_v1 import CANONICAL_PIPELINE, ORIGIN_SIGNATURE
from MRL_UniversalRuntimeLanguage_Core_v1.MRL_Language import (
    MRL_MrLiouIR_Compiler,
    MRL_ParticleIR_Engine,
    MRL_PerceptionKernel,
    MRL_UniversalParser_Core,
)
from MRL_UniversalRuntimeLanguage_Core_v1.MRL_Runtime import (
    MRL_PersistentLoop,
    MRL_ReplayRestore_Core,
    MRL_RuntimeStructureField,
    MRL_Verification,
    MRL_WorldRuntime,
)


class MRL_DL580_Runtime:
    def __init__(self, runtime_dir: Optional[str] = None) -> None:
        self.runtime_dir = runtime_dir or tempfile.mkdtemp(prefix="mrl_dl580_runtime_")

    def run(self, source: str, lang: str = "text", loop_id: str = "run") -> Dict[str, Any]:
        stages: list = []

        # 1. Input
        stages.append("Input")

        # 2. Parse
        parse_result = MRL_UniversalParser_Core.parse(source, lang)
        stages.append("Parse")

        # 3. MrLiouIR
        mrliouir = MRL_MrLiouIR_Compiler.compile_mrliouir(parse_result)
        stages.append("MrLiouIR")

        # 4. Observe (Perception)
        perception = MRL_PerceptionKernel.observe(mrliouir)
        stages.append("Observe")

        # 5. ParticleIR (可逆鏈 + 粒子對映 + roundtrip)
        trace = MRL_ParticleIR_Engine.to_particles(source, label=lang)
        restored_text = MRL_ParticleIR_Engine.from_particles(trace)
        roundtrip = {"exact": restored_text == source, "rhythm": MRL_ParticleIR_Engine.rhythm(source)}
        particle_map = MRL_ParticleIR_Engine.map_particles(mrliouir)
        stages.append("ParticleIR")

        # 6. RuntimeStructureField
        structurefield = MRL_RuntimeStructureField.build(mrliouir, perception["observation_order"])
        stages.append("RuntimeStructureField")

        # 7. Replay + Restore（消費 replay_structurefield）
        rr = MRL_ReplayRestore_Core.MRL_ReplayRestore_Core(structurefield["replay_structurefield"])
        rr.execute()
        replay = rr.replay()
        restore = rr.restore()
        stages.append("ReplayStructureField")
        stages.append("RestoreStructureField")

        # 8. WorldRuntime（雙世界 + context 同步）
        world = MRL_WorldRuntime.MRL_WorldRuntime()
        world.spawn_world("world_alpha", structurefield["world_structurefield"])
        world.spawn_world("world_beta", structurefield["world_structurefield"])
        world.set_context("world_alpha", "mrliouir_hash", mrliouir["mrliouir_hash"])
        world.set_context("world_beta", "structurefield_hash", structurefield["structurefield_hash"])
        sync = world.synchronize("world_alpha", "world_beta")
        world_report = world.report()
        world_report["sync"] = sync
        stages.append("WorldRuntime")

        # 9. PersistentLoop（落盤 + 重啟存活）
        ploop = MRL_PersistentLoop.MRL_PersistentLoop(self.runtime_dir, loop_id=loop_id)
        ploop.run(3, payload_fn=lambda: {"structurefield_hash": structurefield["structurefield_hash"]})
        persistent = {"iteration": ploop.iteration, "survives_restart": ploop.survives_restart()}
        stages.append("PersistentLoop")

        result = {
            "origin_signature": ORIGIN_SIGNATURE,
            "canonical_pipeline": CANONICAL_PIPELINE,
            "stages_executed": stages,
            "parse": {"lang": parse_result["lang"], "unit_count": parse_result["unit_count"]},
            "mrliouir": {"node_count": mrliouir["node_count"], "mrliouir_hash": mrliouir["mrliouir_hash"]},
            "perception": perception["field_summary"],
            "particles": {"trace_checksum": trace.get("bundle_checksum"), "map": particle_map},
            "roundtrip": roundtrip,
            "structurefield": structurefield,
            "replay": replay,
            "restore": restore,
            "world": world_report,
            "persistent_loop": persistent,
        }

        # 10. Verification
        result["verification"] = MRL_Verification.verify(result)
        stages.append("Verification")
        return result
