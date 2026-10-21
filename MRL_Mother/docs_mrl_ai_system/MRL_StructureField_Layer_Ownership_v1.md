# MRL_StructureField 層責任界定 v1（Node 擁有層 vs Python IR 核心層）

origin_signature: `MrLiouWord`

> 平台級產品決策（option 3）：**保留兩個 StructureField 實作，但以「層責任」消歧**，
> 不選單一語言贏家、不刪除任一實作（除非審計證明責任重複）。
> 命名權威見 `docs/MRL_命名規範_v2_MrLiouIR_StructureField.md`。

---

## 1. 兩個 StructureField 不是平行重複，而是不同層

| 層 | 實作（路徑唯一） | 語言 | 責任 |
|---|---|---|---|
| **Ownership / Process StructureField** | `MRL_Runtime/MRL_Workflow_PIDScope/MRL_Runtime_StructureField/runtime_structurefield.js` | Node | 程序歸屬、PID 範圍、process lineage、orchestration、runtime recovery（PIDScope 擁有層） |
| **Language / IR Core StructureField** | `MRL_UniversalRuntimeLanguage_Core_v1/MRL_Runtime/MRL_RuntimeStructureField.py` | Python | 由 MrLiouIR 收斂之執行結構場、replay/restore/world 子場、verification（語言/IR 核心執行層） |

兩者**位於不同套件命名空間、不同語言生態**，無 import/symbol 字面衝突；
「RuntimeStructureField」為共用概念短名，**以完整路徑/層前綴消歧**：

- 擁有層 canonical 全名：`MRL_Workflow_PIDScope :: RuntimeStructureField`（process/ownership）
- 核心層 canonical 全名：`MRL_UniversalRuntimeLanguage_Core_v1 :: MRL_RuntimeStructureField`（IR/execution）

---

## 2. 責任非重複（審計結論）

- Node 擁有層 **不**做 MrLiouIR 編譯、不做 IR→場 收斂；它做 PID/scope/lineage/recovery。
- Python 核心層 **不**做 process/PID 歸屬；它做 MrLiouIR → StructureField → replay/restore/verify。
- 故**不刪除任一實作**；兩者於主線各司其層。

---

## 3. 收斂位置（主線語義鏈）

```
Language → MrLiouIR → ParticleIR → (Core)RuntimeStructureField → Replay → Restore → Verification → WorldRuntime
                                                                                   ↘ (Ownership)RuntimeStructureField：PID/scope/lineage/recovery 包覆執行
        → PersistentLoop → DL580 Mother Runtime
```

- 核心層產出「執行結構場」；擁有層在其上提供「程序歸屬與存活」包覆。
- 兩層交會點為未來 `MRL_PersistentLoop_Daemon` 之 ownership reload + structurefield reload（規格見
  `MRL_UniversalRuntimeLanguage_Core_v1/MRL_PersistentLoop_Daemon_v1_SPEC.md`）。

---

## 4. 規則

- 不得把兩層其一宣稱為「唯一 StructureField」；平台級引用須帶層前綴。
- 不得為消歧而 scaffold 空殼或刪除可運行實作。
- 既有相容 alias（`RuntimeScopeGraph` / `RuntimeGraph` / `.graph`）維持為 alias，不升為 canonical。
