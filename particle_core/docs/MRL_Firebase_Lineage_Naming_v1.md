# MRL Firebase 血統產物正名表 v1

本表只處理系統主權與正式名稱。GitHub 倉庫、Firebase workspace、App Hosting、
Cloudflare Worker、網域與專案 ID 都是定位或部署資料，不會因正名而改寫。

## 正名原則

1. `dofaromg/FlowAgent.Runtime` 是原始根倉庫，正式角色名為 `MRL_SourceRoot_v1`。
2. 由母體產出或回收完成的系統一律使用 `MRL_<功能>_v<n>`。
3. Firebase、Cloudflare、GitHub 等只記在 `provider` 或 `historical_alias`，不得作為產品主權名稱。
4. 尚未從 Firebase Studio 匯出並完成 SHA-256 比對的項目，只能標記 `pending_recovery`，不得宣稱已回到 DL580。
5. 舊檔名、路由與 workspace ID 可保留為相容入口；新證據、日誌、UI 與文件只顯示 canonical MRL 名稱。

## 血統與正式名稱

| 現有／歷史標記 | 正式 MRL 名稱 | 角色 | 當下證據狀態 |
|---|---|---|---|
| `dofaromg/FlowAgent.Runtime` | `MRL_SourceRoot_v1` | 原始根倉庫與血統收斂點 | `verified_repository` |
| DL580 G9 | `MRL_DL580_MotherNode_v1` | 唯一 canonical mother runtime | `runtime_evidence_required_per_head` |
| Firebase 衍生後端能力 | `MRL_FireCore_v1_0` | Auth／Store／Vault／Live／Push／Trace | `verified_in_repository_not_deployed` |
| Firebase Studio workspace | `MRL_CloudStudioBranch_v1` | 雲端工作室分支來源 | `pending_recovery` |
| Apex workspace／Apex Cloud | `MRL_ApexCloud_v1` | Firebase 衍生產品分支 | `pending_recovery` |
| TipSplit workspace | `MRL_TipSplit_v1` | Firebase 衍生產品分支 | `pending_recovery` |
| MRL RuntimeOS workspace | `MRL_RuntimeOS_v1_4_0` | RuntimeOS 分支 | `repository_newer_than_uploaded_snapshot` |
| FirebaseUI-iOS | `MRL_FireCoreUI_iOS_v1` | iOS UI／相容介面 | `separate_repository_pending_alignment` |
| Firebase App Hosting 投影 | `MRL_CloudAppProjection_v1` | 雲端部署投影 | `provider_state_pending_export` |
| MotherGrowthLoop | `MRL_MotherGrowthLoop_v1` | 版本化吸收、驗證、回滾與 MQM 再利用 | `implemented_in_pr_462_dl580_run_pending` |

## 不可混用的兩種名稱

- `canonical_name`：MRL 系統正式名稱，用於產品、模組、證據與稽核。
- `provider_locator`：Firebase／Cloudflare／GitHub 的實際資源名稱或 ID，只用於連線與回收。

例如 Firebase workspace 的畫面可繼續顯示原 workspace ID，但回收 manifest 必須記錄：

```json
{
  "canonical_name": "MRL_CloudStudioBranch_v1",
  "provider": "firebase_studio",
  "provider_locator": "<original-workspace-id>",
  "origin_signature": "MrLiouWord",
  "recovery_status": "pending_recovery"
}
```

`pending_recovery` 只有在來源 ZIP、檔案清單、逐檔 SHA-256、根倉庫差異與 DL580
吸收證據全部完成後，才能提升為 `verified_on_dl580`。
