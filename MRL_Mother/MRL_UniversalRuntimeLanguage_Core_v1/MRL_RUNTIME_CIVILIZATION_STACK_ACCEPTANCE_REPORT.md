# MRL_RUNTIME_CIVILIZATION_STACK_ACCEPTANCE_REPORT

origin_signature: `MrLiouWord`
範圍：`MRL_UniversalRuntimeLanguage_Core_v1`（PR #35 — Runtime Civilization Stack **P0 可驗證核心**）
狀態定位：**P0 可驗證核心**。本報告嚴格區分「已實跑驗證」與「未驗證 / 不得宣稱完成」。

---

## 1. 已實跑 PASS（actually executed, not asserted）

於本機（Python 3.11.15）實際執行並通過：

| 項目 | 指令 | 結果 |
|---|---|---|
| Runtime 驗收套件（stdlib） | `python3 MRL_UniversalRuntimeLanguage_Core_v1/acceptance/MRL_Runtime_Acceptance_TestSuite.py` | **6/6 PASS** → `MRL_RUNTIME_ACCEPTANCE_PASS` + **9/9** → `MRL_CANONICAL_NAMING_VERIFICATION_PASS` |
| 核心 pytest | `python3 -m pytest tests/test_MRL_universal_runtime_core.py -q` | **14 passed** |
| 端到端執行 + 報告產出 | `python3 MRL_UniversalRuntimeLanguage_Core_v1/scripts/MRL_runtime_civilization_run.py` | `MRL_RUNTIME_ACCEPTANCE_PASS`，產出 `docs/` 報告與 MRL_StructureField_Visualization |

六項驗收（§10）逐項實跑通過：

| Check | 內容 | 結果 |
|---|---|---|
| A | RuntimeStructureField build success | PASS |
| B | ReplayStructureField exactness（state hash 相等） | PASS |
| C | RestoreStructureField exactness（由 checkpoint 續播至尾，hash 相等） | PASS |
| D | PersistentLoop survives restart（新實例自磁碟 checkpoint 接續） | PASS |
| E | WorldRuntime synchronization active（雙世界 context 一致） | PASS |
| F | Verification roundtrip exact（fltnz 可逆鏈 txt↔trace 還原一致） | PASS |

Canonical Naming Verification（v2，新增第七類驗收）逐項實跑通過（9/9）：
無 canonical `MetaIR` / `Graph` / `Attention`（pipeline + name map）；canonical 主體
`MrLiouIR`/`StructureField`/`Perception` 存在；`MetaIR`/`RuntimeGraph` 僅以 alias 指向單一 canonical 實作。
→ `MRL_CANONICAL_NAMING_VERIFICATION_PASS`（`MRL_Verification.verify_canonical_naming()`）。

> 唯一命名權威來源：`docs/MRL_命名規範_v2_MrLiouIR_StructureField.md`。

---

## 2. 本地驗收範圍（local acceptance scope）

- **語言輸入**：實測 `python / typescript / cpp / json / markdown / fltnz / text` 之解析；
  py/ts/cpp 為**結構層級**解析（縮排/大括號 + 語句種類辨識）。
- **確定性**：MrLiouIR 對相同輸入產生相同 `mrliouir_hash`（replay/verify 之根據），已測。
- **可逆性**：ParticleIR `collapse/expand`、`jump/unjump`、全鏈 `to_particles/from_particles` 還原一致，已測。
- **重啟存活**：以磁碟 checkpoint 模擬 process 重啟（新實例自磁碟接續），已測。
- **資料層**：`MRL_BaseWorld_DB_Adapter` 以本地 sqlite 鏡像建立 §5 的 7 個邏輯掛接點，已測；
  **未連線**任何 live DB。
- **全測試套件**：`pytest tests/` = **289 passed, 1 skipped, 1 failed**。
  唯一 failed = `tests/test_MRL_host_guard.py::...::test_cidr_check_fails_when_no_ip_matches`，
  經實證：**移除本 PR 變更後仍以相同方式失敗** → 為容器網路/IP 環境依賴之既有測試，
  與本 PR 無關，預期於 GitHub `ubuntu-latest` runner 通過。

---

## 3. GitHub CI 結果（CI results）

CI 閘（PR #35）：

| Workflow / Job | 觸發 | 最近一次已完成結果（branch commit `27025d2`） |
|---|---|---|
| `deploy.yml` → `Run test suite` | 每個 PR / push main | ✅ success |
| GitGuardian Security Checks | 每個 PR | ✅ success |
| `deploy.yml` → `Build & publish release` | 僅 tag | ⏭ skipped（非 tag） |
| `.github/workflows/MRL_GitHub_Mirror.yml` → `Runtime Civilization Acceptance` | 路徑含核心檔變動 | 由本核心 commit 起首次觸發 |

> 撰寫當下：核心 commit（`cc41364`）與本報告 commit 之 CI 仍在佇列/執行中，結果以 PR #35 的 checks 為準。
> 本 session 已訂閱 PR #35 活動：CI 完成事件會回拋，屆時依「CI 失敗先修 CI、不新增功能」原則處理，並回填本節。

---

## 4. 未驗證邊界（unverified boundaries）

以下**尚未驗證**，不得當作已完成：

1. **DL580 上實機 acceptance**：本核心僅於 CI 容器 / 本機驗跑，**未在 DL580 母體節點上跑過**。
2. **live `MRL_BaseWorld_DB_v1`**：未連線真實 27-table / 8-index schema；僅本地 sqlite 7 掛接點鏡像。
3. **多語言語意深度**：py/ts/cpp 僅結構層級，未做完整語意/型別/控制流分析。
4. **OS 級常駐**：PersistentLoop 為磁碟 checkpoint 重啟存活，**非** OS daemon / 背景排程器。
5. **多世界拓撲**：僅雙世界確定性 context 同步；N 世界拓撲、衝突解析策略未驗。
6. **cloudflared 對外鏈路**：`bridge.mrliouhan.ai` 對外 `/health` 未實測（需 DL580 + Cloudflare 帳號）。

---

## 5. 不得宣稱完成的項目（DO NOT claim complete）

- ❌ 不得宣稱「DL580 stable / 母體已上線」——未於 DL580 跑過 acceptance。
- ❌ 不得宣稱「Universal 完整語意編譯器」——目前為結構層級解析。
- ❌ 不得宣稱「OS 級永續 daemon 完成」——目前為 checkpoint 重啟存活。
- ❌ 不得宣稱「已接 BaseWorld DB / 27-table」——僅本地鏡像，未連線。
- ❌ 不得宣稱「bridge.mrliouhan.ai 已對外驗證」——對外鏈路未實測。
- ❌ 不得宣稱「Runtime Civilization Stack 全量完成」——本版為 **P0 可驗證核心**。

---

## 6. 下一增量（next increment，單一焦點）

`MRL_PersistentLoop_Daemon_v1`（規格見 `MRL_PersistentLoop_Daemon_v1_SPEC.md`，**僅規格/準備，尚未實作**）：

```
disk checkpoint → restart → replay → restore → verification → runtime structurefield reload
```

暫不接 live BaseWorld DB、不改遠端 schema、不宣稱 DL580 stable。

> 註：本分支 `MRL_Branch_StructureField_Rename_Alignment_v1` 已套用 v2 canonical 命名
> （`MetaIR→MrLiouIR`、`Graph→StructureField`，舊名保留為 compatibility alias）；
> 上述驗收於改名後重跑仍 6/6 PASS。

origin_signature: `MrLiouWord`
