# Backfill Runbook (過往回顧補齊作業)
Last updated: 2025-09-12 03:44:48Z UTC

## 0. 準備（一次性）
- [ ] 建立 repo/folder：`ParticleArchive/`
- [ ] 放入 `PROVENANCE.md`（外部連結與雜湊）
- [ ] 建立 `SEED_CATALOG.jsonl`、`EVIDENCE_LOG.csv`、`TIMELINE.md`

## 1. 蒐集（Collect）
- [ ] 連結/截圖/檔案 → 記錄到 `EVIDENCE_LOG.csv`
- [ ] 重要對話 → `TIMELINE.md` 建節點（日期/主題/連結）
- [ ] 上傳檔（若適用）計算 SHA-256 → 填入 `EVIDENCE_LOG.csv`

## 2. 建索引（Index）
- [ ] 依你的 schema 寫入 `SEED_CATALOG.jsonl`（每行一個 seed object）
- [ ] 加上 `tags:`（domain/role/phase/layer/sign）

## 3. 快照（Snapshot）
- [ ] 對每個重要節點產生 `SNAPSHOT-<id>.json`（PU header/body/proof 模板）
- [ ] 把雜湊寫入 `PROVENANCE.md` 與 git tag（若用 git）

## 4. 還原測試（Restore Test）
- [ ] 檔案比對：`hash(in) == hash(out)`
- [ ] 結構同構：Graph 映射（parents/layer/sign）一致

## 5. 發佈（Publish）
- [ ] 打包：`Backfill_Archive_YYYYMMDD.zip`
- [ ] 在首頁/Notion/部落格貼上索引與雜湊
