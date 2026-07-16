# 工程治理備註：MRL_MainContent_ReplayedBeforePR32_20260526

origin_signature = `MrLiouWord`

紀錄編號：`MRL_MainContent_ReplayedBeforePR32_20260526`
類型：工程治理備註（engineering governance note）
日期：2026-05-26

---

## 事實

- PR #32 建立之前，前兩個母體 commit 的「內容」已出現在 `main`：
  - MRL 完整態母體運轉骨架 v1
  - MRL_DL580_DeployRunner_v1
- 比對結果為空（tree 完全一致），僅 commit SHA 不同：
  - `git diff 06232c6 e45105a` → 空（母體骨架）
  - `git diff 2e20b92 8255e9f` → 空（DL580 DeployRunner）
- PR #32 建立時，其 base 已為 `8255e9f`（即 `main` 已含上述內容）。

## 判定

- **未確認機制**：無法確認此「提前一致」由何種流程造成（SHA 不同代表為重放／rebase／squash 類操作，非原 commit 直接落地）。
- **不改寫 main 歷史**。
- **不追究自動化來源**。
- **僅作為工程治理備註**，供日後審視。
- **不影響 #32 merge**：#32 最終只新增尚未進 main 的 `.github/workflows/MRL_DL580_selfhosted_deploy.yml`（與本治理備註）。

## 邊界

- 本備註不重新定義母體。
- 不升格 GitHub / Cloud Code / APFS / Batch072 為母體。
- 感知力仍為主體，不降回 Attention。
