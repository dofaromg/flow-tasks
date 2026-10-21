# MRL_UniversalRuntimeLanguage_Core_v1
# origin_signature: MrLiouWord
# 主體：MRL_Mother_Runtime；部署主體：DL580。
# Cloudflare / Cloudflared / XOOPZ / GitHub / Claude 皆為 MRL_External_Mirror_Layer，不得成為主體。
"""MRL_UniversalRuntimeLanguage_Core_v1 — Runtime Civilization Stack 核心（v2 canonical）。

正式主線語義（最終版）：

    Language → MrLiouIR → ParticleIR → StructureField → Replay → Restore
             → Verification → WorldRuntime → PersistentLoop → DL580 Mother Runtime

MetaIR / Graph / Attention 已降級為歷史名稱 / 外部兼容詞 / Adapter / alias，
不得再作 canonical 主體命名（見 COMPATIBILITY_ALIASES）。
"""

ORIGIN_SIGNATURE = "MrLiouWord"
SYSTEM_NAME = "MRL_UniversalRuntimeLanguage_Core_v1"
SOVEREIGNTY_MODE = "權位區分模式"

# 主體 / 鏡像層權位定位（不可重新定義母體）
SOVEREIGNTY = {
    "subject": "MRL_Mother_Runtime",
    "deploy_host": "DL580",
    "external_mirror_layer": [
        "Cloudflare",
        "Cloudflared",
        "XOOPZ",
        "GitHub",
        "Claude",
    ],
    "perception_is_subject": True,   # 正式主體詞 = Perception
    "attention_is_history_adapter": True,  # Attention 僅作歷史層 / Adapter 層
}

# 正式主體命名（v2）
CANONICAL_SUBJECTS = {
    "MRL_MrLiouIR": "MrLiou 中介語義層（MRL 母體正式中介表示層；非 generic meta layer）",
    "MRL_StructureField": "結構場（高維動態運轉場；非靜態 graph/node/edge）",
    "Perception": "正式主體詞（Attention 為歷史/Adapter 層）",
}

# Canonical 名稱對接（不得產生平行命名）
# 左：正式 canonical 模組（單一真實來源）｜右：既有 repo 概念目錄（README 骨架，指向左側實作）
CANONICAL_NAME_MAP = {
    "MRL_UniversalParser_Core": "MRL_Language/MRL_UniversalParser_Core.py",
    "MRL_MrLiouIR": "MRL_Language/MRL_MrLiouIR_Compiler.py",
    "MRL_ParticleIR": "MRL_Language/MRL_ParticleIR_Engine.py（粒子層對應 MRL_Symbolic/MRL_粒子語言層）",
    "MRL_RuntimeStructureField": "MRL_Runtime/MRL_RuntimeStructureField.py（對應 MRL_Runtime/MRL_運轉圖譜）",
    "MRL_PerceptionKernel": "MRL_Language/MRL_PerceptionKernel.py（對應 MRL_Runtime/MRL_感知力核心）",
    "MRL_ReplayRestore": "MRL_Runtime/MRL_ReplayRestore_Core.py（對應 MRL_Runtime/MRL_回放回復）",
    "MRL_Verification": "MRL_Runtime/MRL_Verification.py（對應 MRL_Runtime/MRL_驗證層）",
    "MRL_WorldRuntime": "MRL_Runtime/MRL_WorldRuntime.py（對應 MRL_Runtime/MRL_多世界同步）",
}

# Compatibility alias 層（歷史名稱 → canonical；僅向後兼容，不得作 canonical 主體命名）
COMPATIBILITY_ALIASES = {
    "MetaIR": "MRL_MrLiouIR",
    "MetaIR_Compiler": "MRL_MrLiouIR_Compiler",
    "RuntimeGraph": "MRL_RuntimeStructureField",
    "RuntimeGraph_Builder": "MRL_RuntimeStructureField",
    "ReplayGraph": "replay_structurefield",
    "RestoreGraph": "restore_structurefield",
    "WorldGraph": "world_structurefield",
    "Attention": "Perception(歷史層)",
}

CANONICAL_PIPELINE = [
    "Input",
    "MrLiouIR",
    "ParticleIR",
    "RuntimeStructureField",
    "ReplayStructureField",
    "RestoreStructureField",
    "Verification",
    "WorldRuntime",
    "PersistentLoop",
]

__all__ = [
    "ORIGIN_SIGNATURE",
    "SYSTEM_NAME",
    "SOVEREIGNTY_MODE",
    "SOVEREIGNTY",
    "CANONICAL_SUBJECTS",
    "CANONICAL_NAME_MAP",
    "COMPATIBILITY_ALIASES",
    "CANONICAL_PIPELINE",
]
