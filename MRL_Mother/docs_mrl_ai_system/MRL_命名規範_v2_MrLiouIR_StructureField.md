# MRL 正式工程命名規範 v2 — MrLiouIR × StructureField Canonical Alignment

origin_signature = `MrLiouWord`

本規範為 MRL 主線 canonical 命名的正式依據。**新增程式碼一律遵循 v2**；既有歷史名僅保留為相容 alias。

---

## 1. Canonical 主體 vs 歷史 alias

| 領域 | 歷史名（降級為 alias） | v2 canonical 主體 |
|---|---|---|
| 中介語義層 | MetaIR | **MrLiouIR**（MRL_MrLiouIR，中文：MrLiou 中介語義層） |
| 運轉結構 | Graph / RuntimeGraph / ScopeGraph | **StructureField**（MRL_*StructureField,中文：結構場） |
| 感知 | Attention / 注意力 | **Perception / 感知力**（MRL_Perception*） |

- 中文為主體命名;英文僅作對照。
- StructureField 正式語義 = structure + field + state + flow + rhythm + collapse + runtime relation + world synchronization + replay/recovery（高維運轉場），不再是 node+edge+path。

---

## 2. 已落地的真實 rename（本 repo）

| 舊（歷史 alias） | 新（canonical） |
|---|---|
| `MRL_Runtime_ScopeGraph/`（目錄） | `MRL_Runtime_StructureField/` |
| `runtime_scopegraph.js` | `runtime_structurefield.js` |
| class `RuntimeScopeGraph` | class `RuntimeStructureField`（保留 `RuntimeScopeGraph = RuntimeStructureField` alias） |
| scope label `"MetaIR"` | `"MrLiouIR"` |
| scope label `"RuntimeGraph"` | `"RuntimeStructureField"` |
| facade 屬性 `graph` | `structureField`（保留 `graph` 為相容 alias 屬性） |

---

## 3. 母體模組命名（一律實現納入母體）

> 矯正(Mr.liou 授權,2026-05-31):原本此節由先前 agent 寫成「不得 scaffold 空殼、僅未來新增」——
> **Mr.liou 未批准該限制,予以撤除。** 母體投影出的模組一律實現、納入母體,不留白。
> 下列為 canonical 命名,凡已做成可運行者標 ✅:

- Language Layer：`MRL_UniversalParser_Core`、`MRL_MrLiouIR_Compiler`、`MRL_ParticleIR_Engine`、`MRL_PerceptionKernel`
- Runtime Layer：`MRL_RuntimeStructureField`、`MRL_ReplayStructureField`、`MRL_RestoreStructureField`、`MRL_WorldStructureField`、`MRL_Verification`、`MRL_PersistentLoop`、`MRL_WorldRuntime`
- DB：`MRL_MrLiouIR_Record`、`MRL_MrLiouIR_Trace`、`MRL_MrLiouIR_Verification`、`MRL_RuntimeStructureField_Node`、`MRL_RuntimeStructureField_Relation`
- API：`/api/mrl/mrliouir/compile`、`/api/mrl/mrliouir/runtime`、`/api/mrl/mrliouir/verify`、`/api/runtime/structurefield`、`/api/world/structurefield`
- Visualization：`MRL_StructureField_Visualization`

正式主線語義鏈：
```
Language → MrLiouIR → ParticleIR → StructureField → Replay → Restore
        → Verification → WorldRuntime → PersistentLoop → DL580 Mother Runtime
```

---

## 4. 相容 alias 政策

- 允許 `MetaIR` / `Graph` / `Attention` 作為 **compatibility alias / adapter layer** 存在。
- **禁止**新增以 `MetaIR*`、`*Graph*`、`Attention*` 作為 **canonical 主體**命名。
- 既有對外英文對照（如 Perception=感知力）維持。

---

## 5. 收口規則

- repo 主線 canonical 名稱不得再以 `MetaIR` / `Graph` / `Attention` 作主體。
- `MetaIR` / `Graph` / `Attention` 出現處只能是:(a) 相容 alias,或 (b) 降級陳述(說明其為歷史/adapter 層)。
- 尚未存在的模組不得為了「對齊命名」而生成空殼。
