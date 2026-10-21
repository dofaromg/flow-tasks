# MRL_Formula_Parameter_Registry_v1｜牽一髮動全身參數保存層

- 母體簽名：MrLiouWord
- Schema：`schemas/MRL_Formula_Parameter_Record.schema.json`
- Registry 資料：`data/MRL_formula_parameter_registry.json`
- 驗收腳本：`scripts/MRL_formula_parameter_registry_check.js`（`npm run MRL_parameter_registry`）

## 目標

作為所有公式參數、觀測權重、環境折損、反推穩定項、放大縮小係數的**唯一登錄層**。

## 核心原因

參數是一切變動的重要數據。任何參數改動都可能影響：

- 創世公式
- 反推公式
- 放大縮小公式
- 源代碼壓縮
- 環境變化
- APFS-style customs gate
- 莫比斯反轉鏡像轉正
- Canon Packet 判定

## 記錄格式（必須保存欄位）

每筆 registry record 必須符合 `schemas/MRL_Formula_Parameter_Record.schema.json`：

| 欄位 | 說明 |
| --- | --- |
| `formula_name` | 參數所屬公式名稱 |
| `parameter_name` | 參數名稱 |
| `parameter_value` | 參數當前值 |
| `parameter_version` | 參數版本號 |
| `source_ref` | 參數來源引用 |
| `changed_by` | 變更者身分 |
| `changed_at` | UTC 變更時間 |
| `change_reason` | 變更原因（不得為空） |
| `impact_scope` | 影響範圍：`low` / `medium` / `high` |
| `before_value` | 變更前的值（首次登錄為 `null`） |
| `after_value` | 變更後的值（必須等於 `parameter_value`） |
| `rollback_ref` | 回滾參考點（checkpoint） |
| `replay_required` | 是否需要回放驗證 |
| `verification_status` | `pending` / `verified` / `parameter_review` / `rejected` |
| `origin_signature` | 必須為 `MrLiouWord` |

## 必須管控的參數類型

| 公式 | 參數 |
| --- | --- |
| MRL_創世公式 | `P_k` / `N_k` / `eta_k` |
| MRL_放大縮小公式 | `alpha` / `beta` / `scale_mode` |
| MRL_反推公式 | `inverse_epsilon` / `stability_clip` / `loss_bound` |
| MRL_源代碼壓縮公式 | `compression_ratio` / `hash` / `simhash` / `roundtrip_score` |
| MRL_環境變化公式 | `context_weight` / `runtime_weight` / `dependency_weight` / `external_noise` / `trust_score` |
| MRL_莫比斯反轉鏡像轉正公式 | `inversion_axis` / `mirror_axis` / `correction_axis` / `orientation_hash` / `mismatch_score` |

## 強制規則

1. **未登錄參數不得進入母體運算。**
2. 所有參數變更必須**可回放**（`replay_required`）、**可反推**（`before_value` / `after_value`）、**可比較**（`after_value` 必須等於 `parameter_value`）、**可回滾**（`rollback_ref` 不得為空）。
3. 參數不得只存在 README 或對話中，必須落入 `data/MRL_formula_parameter_registry.json`。
4. 每次調整都必須產生 checkpoint（記錄於 `rollback_ref`）。
5. 高影響參數（`impact_scope: high`）需進 `parameter_review`，不可自動放行：`verification_status` 只允許 `parameter_review` 或 `verified`，且 `replay_required` 必須為 `true`。

## 變更流程

1. 修改 `data/MRL_formula_parameter_registry.json`：更新 `parameter_value`、遞增 `parameter_version`，將舊值填入 `before_value`、新值填入 `after_value`，填寫 `change_reason` 與 `rollback_ref` checkpoint。
2. 高影響參數將 `verification_status` 設為 `parameter_review`，經審核後改為 `verified`。
3. 執行 `npm run MRL_parameter_registry` 驗收。

## 驗收

```bash
npm run MRL_parameter_registry
```

驗收腳本會：

1. 依 schema 驗證每筆 record（欄位、型別、enum、簽名、date-time）。
2. 確認 6 大類共 23 個核心公式參數均有 registry record。
3. 檢查治理規則（可回放、可反推、可比較、可回滾、高影響審核）。
4. 輸出 impact report（`MRL_Formula_Parameter_Impact_Report_v1`）。
5. 全部通過輸出 `MRL_FORMULA_PARAMETER_REGISTRY_PASS`；任一違規輸出 `MRL_FORMULA_PARAMETER_REGISTRY_FAIL` 並以非零碼結束。
