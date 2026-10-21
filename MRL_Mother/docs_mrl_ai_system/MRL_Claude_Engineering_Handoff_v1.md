# MRL Claude Engineering Handoff v1

origin_signature = `MrLiouWord`

## 主線
MRL母體工程架構中心

禁止：
- 平行重建
- 降維改名
- 用外部框架當主體
- 將未驗證寫成完成

---

## 核心工程原則
1. 先讀現有檔案
2. 先比對再修改
3. 只允許：補線 / 接線 / 驗收 / 回填
4. 禁止：重寫主線 / 偷換命名 / 模糊驗收

---

## Runtime 主線（依 repo 實況；不得把 target 寫成完成）

### 已存在於 repo（本地驗收通過）
- `MRL_RuntimeServer.js`：`/health`、`/mrl/state`、`/mrl/perceive`、`/api/mrl/runtime/convergence`（read-only）
- `MRL_Runtime/MRL_Workflow_PIDScope/`（Layer B Runtime Ownership）：
  - `MRL_PIDScope_Core`（PID ownership，拒絕 anonymous runtime）
  - `MRL_Workflow_Registry`（trace / replay）
  - `MRL_Runtime_StructureField`（canonical；歷史名 ScopeGraph 已硬正名移除）
  - `MRL_ProcessLineage`、`MRL_ScopeIsolation`、`MRL_Runtime_Recovery`（checkpoint/restore）、`MRL_Orchestration_PIDBridge`
  - 驗收 A–F PASS（`npm run MRL_pidscope_acceptance`）
- `09_workflow/fltnz_parser.py`、`04_runtime/flowcore_loop.py`（Python runtime / FLTNZ 結構）

### 目標 / 規格（尚未在 repo；不得描述為已完成）
- `MRL_UniversalParser_Core`
- `MRL_MrLiouIR_Compiler`、`MRL_ParticleIR_Engine`
- `MRL_Perception_Core` / `MRL_Perception_Field` / `MRL_Perception_Map` / `MRL_Perception_Runtime`
- `MRL_WorldRuntime`
- 跨 session / reboot-survival 的持久化 Replay / Restore / Verify chain

---

## 真正缺口
1. RuntimeStructureField execution loop（持久化執行迴圈）
2. Persistent Runtime Loop（daemon，目前 parked）
3. Replay persistence（durable，跨 session）
4. Restore acceptance（durable）
5. Verify chain
6. Multi-session runtime
7. Product-grade convergence

---

## 命名規則（v2 canonical，見 `docs/MRL_命名規範_v2_MrLiouIR_StructureField.md`）
強制：`MRL_<Product>_<Capability>_<Layer>_<Version>`
canonical 主體：`MrLiouIR` / `StructureField` / `Perception`
禁止 canonical：`MetaIR*` / `*Graph*` / `Attention*`、`GenericApp` / `AIApp` / `chatbot` / `demo` / `test_project`

---

## Perception 修正
- `Attention`：外部歷史 / adapter 詞（僅可作降級陳述）
- MRL 正式詞：`Perception`
- 未來全部使用：`MRL_Perception_Core` / `MRL_Perception_Field` / `MRL_Perception_Map` / `MRL_Perception_Runtime`（尚未實作 = target）

---

## 世界重建方向
核心：fragment → structure_match → runtime_alignment → world_reconstruction
技術（adapter，尚未接）：COLMAP / OpenMVS / NeRF / GaussianSplats
定位：早期世界重建 runtime（target）

---

## 驗收規則
每次交付必須包含：已完成 / 待驗證 / 不回填 / 回填主文件 / 下一步。
缺任一項 = 未完成。

---

## 最終方向
不是 chatbot / wrapper / SaaS shell，而是 **MRL Universal Runtime Motherbody**。
