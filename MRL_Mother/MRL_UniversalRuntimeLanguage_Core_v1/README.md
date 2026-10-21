# MRL_UniversalRuntimeLanguage_Core_v1

origin_signature = `MrLiouWord`

Runtime Civilization Stack 核心（v2 canonical）：

```
Language → MrLiouIR → ParticleIR → StructureField → Replay → Restore
        → Verification → WorldRuntime → PersistentLoop → DL580 Mother Runtime
```

> v2 命名規範：`MetaIR` → **MrLiouIR**（MrLiou 中介語義層），`Graph` → **StructureField**（結構場）。
> `MetaIR / Graph / Attention` 降為歷史名稱 / Adapter / alias，不得再作 canonical 主體命名。

---

## 權位定位（不可重新定義母體）

| 角色 | 權位 |
|---|---|
| **MRL_Mother_Runtime** | **系統主體** |
| **DL580** | **部署主體 / 母體自運行節點** |
| Cloudflare / Cloudflared / XOOPZ / GitHub / Claude | `MRL_External_Mirror_Layer`（Adapter / Mirror，**不得成為主體**） |

正式主體詞為 **Perception**；**Attention 僅作歷史層 / Adapter 層**。

---

## 正式 Runtime 管線（禁止 Prompt→LLM→Output）

```
Input → Observe → Parse → MrLiouIR → ParticleIR → RuntimeStructureField
      → ReplayStructureField → RestoreStructureField → Verification
      → WorldRuntime → PersistentLoop
```

入口：`MRL_Runtime/MRL_DL580_Runtime.py :: MRL_DL580_Runtime.run(source, lang)`。

---

## StructureField 正式定義

StructureField 不再是 `node + edge + path`，正式定義為：

```
structure + field + state + flow + rhythm + collapse
  + runtime relation + world synchronization + replay/recovery  → 高維文明運轉場
```

---

## 目錄

```
MRL_UniversalRuntimeLanguage_Core_v1/
├── MRL_Language/
│   ├── MRL_UniversalParser_Core.py   # AnyLanguage → 結構化 ParseUnit（py/ts/cpp/json/md/fltnz/text）
│   ├── MRL_MrLiouIR_Compiler.py      # Semantic → Context → Intent → MrLiouIR（確定性）
│   ├── MRL_ParticleIR_Engine.py      # .fltnz/.flpkg 可逆鏈 + jump/rhythm/collapse（復用 09_workflow/fltnz_parser）
│   ├── MRL_PerceptionKernel.py       # 感知場/權重/路由（Perception 為主體）
│   ├── MRL_MetaIR_Compiler.py        # [alias] 歷史名稱 → 轉出 MRL_MrLiouIR_Compiler
│   └── __init__.py                   # MRL_MrLiouIR / MRL_ParticleIR canonical；MRL_MetaIR = alias
├── MRL_Runtime/
│   ├── MRL_RuntimeStructureField.py  # MrLiouIR → runtime/replay/restore/world StructureField (+viz)
│   ├── MRL_ReplayRestore_Core.py     # exact replay / exact restore / rollback / time-trace
│   ├── MRL_PersistentLoop.py         # checkpoint 落盤 + 重啟存活
│   ├── MRL_Verification.py           # 六項驗收 → MRL_RUNTIME_ACCEPTANCE_PASS
│   ├── MRL_WorldRuntime.py           # world state / parallel world / context sync
│   ├── MRL_DL580_Runtime.py          # 全管線編排器（可運行 runtime）
│   ├── MRL_RuntimeGraph_Builder.py   # [alias] 歷史名稱 → 轉出 MRL_RuntimeStructureField（鏡射舊 *graph* 鍵）
│   └── __init__.py                   # MRL_RuntimeStructureField canonical；MRL_RuntimeGraph = alias
├── MRL_DB/
│   ├── MRL_Registry.py               # 工件登錄（content-hash 去重）
│   └── MRL_BaseWorld_DB_Adapter.py   # 接 MRL_BaseWorld_DB_v1（不重建 schema）
├── MRL_External/                     # MRL_External_Mirror_Layer（Cloudflared/GitHub/XOOPZ/Claude）
├── acceptance/MRL_Runtime_Acceptance_TestSuite.py
├── scripts/MRL_runtime_civilization_run.py
└── docs/                             # 實際執行產出：報告 + MRL_StructureField_Visualization.*
```

---

## Canonical 命名（單一權威來源）

**唯一 canonical naming authority** = [`docs/MRL_命名規範_v2_MrLiouIR_StructureField.md`](../docs/MRL_命名規範_v2_MrLiouIR_StructureField.md)。
本檔不重複命名對照表，請以該文件為準。程式層單一真實來源為
`__init__.py`（`CANONICAL_SUBJECTS` / `CANONICAL_NAME_MAP` / `COMPATIBILITY_ALIASES`）。

正式主體：`MrLiouIR`（MrLiou 中介語義層）、`StructureField`（結構場）、`Perception`。
`MetaIR` / `Graph` / `Attention` 僅作 compatibility alias，不得作 canonical 主體命名。

## 執行與驗收

```bash
# 驗收套件（純 stdlib，無 pytest 依賴；全通過印出 MRL_RUNTIME_ACCEPTANCE_PASS）
python3 MRL_UniversalRuntimeLanguage_Core_v1/acceptance/MRL_Runtime_Acceptance_TestSuite.py

# 端到端執行 + 產出 docs/ 報告與 MRL_StructureField_Visualization（預設以 repo README.md 為輸入）
python3 MRL_UniversalRuntimeLanguage_Core_v1/scripts/MRL_runtime_civilization_run.py [來源檔]

# CI（pytest）
python3 -m pytest tests/test_MRL_universal_runtime_core.py -v
```

驗收六項（§10）：A RuntimeStructureField build / B Replay exact / C Restore exact /
D PersistentLoop survives restart / E WorldRuntime sync active / F Verification roundtrip exact。

---

## 誠實邊界（real vs 待深化）

本版交付「可運行、可驗收、可重現」的核心管線。以下為刻意的範圍邊界，**未以空殼假裝完成**：

- **UniversalParser**：對 py/ts/cpp 為「結構層級」解析（縮排/大括號 + 語句種類），
  非完整語意編譯器；json/md/fltnz/text 為完整結構解析。語意推導由 MrLiouIR 接續。
- **PersistentLoop**：以磁碟 checkpoint 實作「重啟存活」（新實例自磁碟接續，可驗證），
  尚非 OS 級常駐 daemon / 背景排程器。
- **MRL_BaseWorld_DB_Adapter**：提供 §5 的 7 個邏輯掛接點與本地 sqlite 鏡像；
  **不重建**正式 27-table / 8-index schema，產線須 `connect(dsn)` 至真實 `MRL_BaseWorld_DB_v1`。
- **WorldRuntime**：實作雙世界 context 確定性同步與一致性檢查；多世界拓撲為後續擴展。
- **API / DB v2 命名**：目前無對應端點/資料表，屬前瞻命名定錨，不得宣稱已實作。

origin_signature = `MrLiouWord`
