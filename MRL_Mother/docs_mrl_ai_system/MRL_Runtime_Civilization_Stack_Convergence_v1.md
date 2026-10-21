# MRL_Runtime_Civilization_Stack_Convergence_v1

origin_signature = `MrLiouWord`
layer：**MRL_Runtime_Civilization_Convergence_Layer**（主線收斂層 / governance，**非功能層**）
branch：`MRL_Branch_Runtime_Convergence_v1`（base = `main`）

> 本檔為跨線收斂治理文件，將四個工作面收斂成單一主線視圖。
> **本輪只交付本文件**：不實作 API、不改 EntryGateway、不改 token middleware、
> 不新增 runtime module / daemon、不改 CI、不改 #35 / #36 / #37。
> convergence API 於本檔僅**規格化**，狀態 `SPEC_READY / IMPLEMENTATION_PENDING`。

---

## 0. 四個工作面（只有三條主線功能 + 一條收斂層）

| 代號 | 線 | 性質 |
|---|---|---|
| A | **PR #35 = Runtime Core Layer** | 功能線 |
| B | **PR #36 = Runtime Ownership / PIDScope Layer** | 功能線 |
| C | **EntryGateway = Live DL580 Runtime Entry Layer** | 功能線 |
| D | **PR #37 = Naming Alignment Layer** | 對 #35 的 canonical naming correction（非新功能線） |
| — | **本檔 = Convergence Layer** | 主線收斂 / governance（非功能層） |

合流位置：

```
#35 Runtime Core
    ↳ #37 Naming Alignment（stacked on #35）
#36 Runtime Ownership
EntryGateway Runtime API
        ↓
MRL_Runtime_Civilization_Stack_v1
```

---

## 1. Merge order（正式合流順序）

```
#35  → #37  → #36  → EntryGateway  → Convergence(本檔)
```

- #35 先維持 Runtime Core P0（進 main 或保持可驗狀態）。
- #37 stacked on #35：待 #35 成為 base，再 rebase / retarget → 跑完整 main-gated CI。
- #36 獨立作 Runtime Ownership，**不得**混入 naming branch。
- EntryGateway 接三者，只讀取 / 顯示 / 接線，**不重新實作**。
- 本收斂層最後匯入 **mainline governance layer**（非 runtime implementation）。

---

## 2. 每條線真正提供什麼（具體，不抽象）

| 線 | 真正提供 | 落點 |
|---|---|---|
| **Runtime Core**（#35） | 可運行管線 Input→MrLiouIR→ParticleIR→StructureField→Replay→Restore→Verification→WorldRuntime→PersistentLoop；六項驗收 | `MRL_UniversalRuntimeLanguage_Core_v1/` |
| **Naming Alignment**（#37） | MetaIR→MrLiouIR、Graph→StructureField、Attention→Perception；compatibility alias policy；單一命名權威 | `docs/MRL_命名規範_v2_MrLiouIR_StructureField.md` + 核心 rename |
| **PID Ownership**（#36） | Runtime PID 範圍鎖定 / ownership / 臨時埠 PID-scoped 健康檢查（PIDScope） | PR #36（另線） |
| **Live Runtime Gateway**（EntryGateway） | 對外 runtime 入口、只讀取/顯示/接線 | `ai.mrliouword.com/mrl`（另線） |

---

## 3. Active vs Pending（禁止模糊）

| 項目 | 狀態 | 驗證層級（誠實標註） |
|---|---|---|
| Runtime Core 管線 | **LOCAL_ACCEPTANCE** | 本 session 實跑：`MRL_RUNTIME_ACCEPTANCE_PASS`（6/6）；尚非 main-gated CI |
| Canonical Naming | **LOCAL_ACCEPTANCE** | 本 session 實跑：`MRL_CANONICAL_NAMING_VERIFICATION_PASS`（9/9） |
| #37 stacked CI | **MAIN_CI_PENDING** | base = #35 分支（非 main），main-gated CI 合理未跑；待 retarget main 後跑 |
| #36 PID Ownership | **DECLARED_READY（未本地驗證）** | 依 MrLiou 裁示 `MRL_PIDSCOPE_ACCEPTANCE_PASS`；本 session 未獨立驗證 |
| EntryGateway 對外入口 | **DECLARED_ACTIVE（未本地驗證）** | 依 MrLiou 裁示 ACTIVE；對外鏈路 `ai.mrliouword.com/mrl` 本 session 未實測 |
| PersistentLoop Daemon | **PENDING** | 規格已備（`MRL_PersistentLoop_Daemon_v1_SPEC.md`），未實作 |
| ReplayRestore Runtime（常駐） | **PENDING** | 目前為 in-process replay/restore，非常駐 runtime instrumentation |
| WorldSync（多世界） | **PENDING** | 目前為雙世界確定性 context 同步；多世界拓撲未做 |
| BaseWorld_DB real integration | **PENDING** | 僅本地 sqlite 7 掛接點鏡像；未連線真實 27-table schema |
| DL580 reboot survival | **PENDING** | 未於 DL580 實機 reboot 後驗證存活 |

狀態語彙定義：
- `LOCAL_ACCEPTANCE`：本機/容器實跑通過，**尚未** main-gated CI。
- `MAIN_CI_PENDING`：main 閘 CI 尚未觸發（stacked base 之合理狀態）。
- `DECLARED_*`：依裁示記錄，本 session **未**獨立驗證（provenance = 另線 PR）。
- `PENDING`：尚未實作 / 尚未 instrumentation / 尚未 reboot survival。

---

## 4. 不得宣稱完成（DO NOT claim complete）

以下一律保留 **PENDING**，禁止任何文件/報告宣稱完成：

- `PersistentLoop_Daemon`
- `ReplayRestore_Runtime`（常駐）
- `WorldSync`（多世界）
- `BaseWorld_DB` real integration
- `DL580 reboot survival`

並沿用既有不得宣稱：DL580 stable（未實機 acceptance）、完整語意編譯器、OS 級 daemon、live DB 連線。

---

## 5. Convergence API（SPEC-ONLY，本輪不實作）

```
GET /api/mrl/runtime/convergence
```

- 用途：EntryGateway **read-only** convergence status（只讀取/顯示，不重新實作任何層）。
- 狀態：`SPEC_READY` / `IMPLEMENTATION_PENDING`。
- 規格化但**不寫程式**；薄 endpoint 一旦進 repo 即成 runtime API surface（需驗 token/版本/資料來源/CI/EntryGateway 依賴），本輪不需要。

回傳 schema（規格，尚未實作）：

```json
{
  "stack": "MRL_Runtime_Civilization_Stack_v1",
  "entry_gateway": {
    "status": "ACTIVE",
    "source": "MRL_Branch_Product_EntryGateway_Reconstruction_v1",
    "endpoint": "https://ai.mrliouword.com/mrl"
  },
  "runtime_core": {
    "status": "STACKED_READY",
    "source": "PR #35 + PR #37",
    "verified": [
      "MRL_RUNTIME_ACCEPTANCE_PASS",
      "MRL_CANONICAL_NAMING_VERIFICATION_PASS"
    ]
  },
  "runtime_ownership": {
    "status": "READY",
    "source": "PR #36",
    "verified": [
      "MRL_PIDSCOPE_ACCEPTANCE_PASS"
    ]
  },
  "persistent_loop_daemon": {
    "status": "PENDING"
  },
  "baseworld_db": {
    "status": "PENDING"
  },
  "dl580_reboot_survival": {
    "status": "PENDING"
  }
}
```

> 註（provenance，誠實標註）：`runtime_core.verified` 之兩個 token 由本 session 實跑重現；
> `entry_gateway.status=ACTIVE` 與 `runtime_ownership.verified=MRL_PIDSCOPE_ACCEPTANCE_PASS`
> 依 MrLiou 裁示記錄，本 session **未**獨立驗證（屬另線 PR #36 / EntryGateway）。

---

## 6. 本輪範圍與下一輪

本輪 PASS 條件：

- 只新增本 convergence 文件；不新增程式碼；不新增 API；不改既有分支功能 / CI。

下一輪（待本檔確認後）：

- 開 `MRL_Branch_Runtime_Convergence_API_v1`：專門把本檔 §5 spec 轉為 read-only API。

PersistentLoop Daemon 維持 **PENDING**，待下列成立再進 `MRL_PersistentLoop_Daemon_v1`：
`#35 Runtime Core stabilized` + `#37 naming alignment stacked clean` + `#36 ownership layer green` + `EntryGateway convergence API ready`。

---

## 7. 本分支收口規則

`MRL_Branch_Runtime_Convergence_v1` 完成後 merge into **mainline governance layer**，
**非** merge into runtime implementation —— 其本質為 governance / convergence / orchestration documentation layer。

origin_signature = `MrLiouWord`
