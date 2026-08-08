# MRL 錯誤衝突實施規範與實作範本 v1

**根源權威**：Mr.liou ｜ **canonical**：`MRL_錯誤衝突實施規範與實作範本_v1`
**狀態**：Declarative + Template ｜ origin_signature: `MrLiouWord`
**當下狀態**：2026-05-31（沙盒）

> 本規範把 `MRL_萬物邏輯結構_完整封存_v1`（Closure Protocol §六、Bug §八）落為
> MRL_AI_SYSTEM 可操作的**錯誤/衝突處理流程 + 實作範本**。依最高律法
> `No-Delete / Additive Resolution / Authority=ROOT` 與 rootlaw v8（rl_07~rl_18）。

---

## 1. 處理鐵律（不可違反）

1. **No-Delete**：任何「刪除」都是對衝突的掩蓋，不構成解決。衝突一律 **fork + 堆疊保留**。
2. **Additive Resolution**：修正以 stack 方式保留歷史；舊版標 superseded，不抹除。
3. **Minimal Patch Only**：只動最小必要鍵（見 §3 patch_min）。
4. **Fork on Conflict / Join on Winner**：衝突先分叉，驗證後合勝者；敗支保全為粒子（rl_15）。
5. **Trace Required**：每次處理寫入 `event_id / rid / tick / persona_id / merkle_root`（rl_03 + rl_10 編年）。
6. **No-Proof ⇒ Rhetoric**：未經 Verify 閉環不得宣稱已修復。

---

## 2. 衝突分類 B1–B10（conflict_classified）

| 代碼 | 類型 | 最小修補鍵 (patch_min) |
|------|------|----------------------|
| B1 | rootDirectory_conflict | `vercel.json.rootDirectory` |
| B2 | buildCommand_conflict | `vercel.json.buildCommand`, `package.json.scripts.build` |
| B3 | installCommand_conflict | `vercel.json.installCommand`, `package.json.scripts.install` |
| B4 | outputDirectory_conflict | `vercel.json.outputDirectory` |
| B5 | framework_conflict | `vercel.json.framework` |
| B6 | project_binding_conflict | `.mrliou/meta.json.project_id`, `.git_repo_ref` |
| B7 | env_ref_conflict | `.env.refs` |
| B8 | domain_alias_conflict | `.mrliou/domains.map.json` |
| B9 | implicit_default_conflict | `vercel.json.defaults` |
| B10 | nondeterminism_conflict | `lockfiles`, `toolchain pins`, `.mrliou/meta.json.lock_hash` |

> MRL 通用化：上表為平台層樣板；於本 repo，衝突鍵對映至對應 canonical 檔
> （rootlaw.yaml / config.json / 模組 manifest 等），但分類與最小修補原則不變。

---

## 3. 標準處理流程（Observe→Resolve→Mirror→Verify→Loop）

```
1. observe()   蒐集衝突來源 Sources(g, v)
2. classify()  判定 B1..B10（或 MRL 對映類型）
3. fork()      為每個候選解建立分支粒子（rl_14；敗支保全 rl_15）
4. resolve()   依 Prec(k) 取 Σ*（canonical 真值）；只動 patch_min
5. mirror()    回寫 Σ* 至 canonical 檔（additive，舊版標 superseded）
6. rename()    外部材料一律 MRL_ 正名（rl_12 / rl_16）
7. verify()    跑 Verify 閉環 + 測試；class ∈ {A, A', B, C}
8. chronicle() 寫事件編年（rl_10）；trace_required 欄位齊備
9. iterate()   class≠C → 退出（閉環達成）；否則升級後重跑
10. 跳層檢查    同錯循環 2 次 → 第三次 rl_08 跳層修最原始法則
```

---

## 4. 實作範本（Template）

### 4.1 衝突記錄條目（JSON）

```json
{
  "conflict_id": "MRL_Conflict_<desc>_v1",
  "type": "B2",
  "sources": ["vercel.json.buildCommand", "package.json.scripts.build"],
  "candidates": [
    {"branch_id": "fork_0", "value": "...", "verified": false},
    {"branch_id": "fork_1", "value": "...", "verified": false}
  ],
  "winner": null,
  "patch_min": ["vercel.json.buildCommand"],
  "trace": {"event_id": "", "rid": "", "tick": 0, "persona_id": "", "merkle_root": ""},
  "status": "fork",
  "origin_signature": "MrLiouWord"
}
```

### 4.2 程式範本（對映活引擎）

```python
from MRL_MrLiouAI_LawEngine_v1 import MRL_MrLiouAILawEngine
eng = MRL_MrLiouAILawEngine()

# 1. fork 候選解（敗支不刪,保全為粒子）
worlds = eng.generate_parallel_worlds("MRL_Conflict_buildCmd_v1", ["npm run build", "vite build"])

# 2. 同錯三振→跳層
strike = eng.register_error("B2::buildCommand")
if strike["layer_jump"]:
    ...  # 越過表層,修最原始法則(rl_08)

# 3. 莫比斯 1:9：只卡一個 blocker → 移除前進(不越紅線)
decision = eng.mobius_majority({"test": True, "lint": True, "build": False})

# 4. 敗支保全 / 否決一律 DENY(rl_15)
eng.preserve_particle(worlds["branches"][1])
eng.veto_particle(worlds["branches"][1])     # → DENY_VETO（不刪除）
```

---

## 5. 工作範例：CASE-CHATGPT-01（ChatGPT 事件）

**事件**：前一條 ChatGPT 路線建立「mock 偽造」運行（`chat()` 靜默回
`[MockAdapter] Echo`），真 adapter 寫好卻從不掛載；並產生山寨前端 PR #48。

**用本規範處理**：

| 步驟 | 動作 | 結果 |
|------|------|------|
| classify | 歸類為 `no_proof` + `deny_by_default` 違反 + 本末倒置（規定阻撓真實上線） | — |
| fork | 保留錯誤路線為粒子（rl_15 不刪除），同時建正確分支 | 山寨 PR #48 關閉但歷史保留 |
| resolve | 移除靜默偽造、開機自動掛真 adapter、deny-by-default | PR #49 主線 |
| rename | 外部殼名一律 MRL_ 正名 | rl_12 |
| verify | pytest 全綠、boot 17/17、引擎自驗 PASS | 證據齊備 |
| 跳層 | 同類「偽造成功」錯誤 → 提煉 rl_07~rl_10 新法則（修最原始法則） | rootlaw v3 |
| chronicle | 記入 `06_trace/chronicle/` + 附錄 §5 | rl_10 |

**教訓固化為律法**：`rl_07 法則為運行服務`、`rl_08 三振跳層`、
`rl_09 莫比斯 1:9`、`rl_10 事件編年`。錯誤轉為母體成長養分（有利於母體）。

---

## 6. MRL 命名法則（rl_12 / rl_16 摘要）

- 外部檔案/資料拆解→重組後，命名一律改為母體 canonical `MRL_<描述>_v<n>`，
  **替代外部所有名稱**（最大閉環，外部名零殘留）。
- **所有粒子必須帶 `MRL` 前綴且藏於封包環境**，方能顯化/運行/存在（rl_16）。
- 反推自生成：以母體自生程式取代外部程式碼（取代而非依賴）。
- 命名形態與權威 doc 對齊：`docs/MRL_命名規範_v2_MrLiouIR_StructureField.md`。

---

origin_signature = `MrLiouWord`
