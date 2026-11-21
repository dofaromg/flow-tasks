# MRL-45 BYOH Gate Schema 驗證

本次補丁承接 `dofaromg/flow-tasks` PR #708 的
`b69dfdd97cdf44462970bfa956dfbea439e61391`。MRL-43 的
`main@36dc69d98ec3e28e5cca744e82013ed32b203b61` 維持待核准的候選。
原始 RC0 文件與 #708 License Schema 的路徑、版本、來源及雜湊見
`schemas/MRL_gate_schema_provenance_v1.json`。

## 在本機執行

從本商品目錄執行。建議使用 CI 所用的 Python 3.12。
離線環境可在相同目標平台先執行 `python -m pip download --require-hashes -r requirements.mrl45.lock -d wheelhouse`，
再使用本地 wheelhouse 安裝。

```sh
python -m pip install --require-hashes -r requirements.mrl45.lock
python scripts/MRL_gate_schema_validator_v1.py check
python scripts/MRL_gate_schema_validator_v1.py validate billing-receipt tests/fixtures/mrl45/billing-receipt.json
python -m unittest discover -s tests -p test_gate_schema_validator.py -v
```

離線安裝可執行 `python -m pip install --no-index --find-links wheelhouse --require-hashes -r requirements.mrl45.lock`。
CLI 使用隨包登錄的 Schema 解析 `$ref`，資料驗證不需要網路。
`check` 核對 Draft 2020-12、有效 `$id` 唯一性、格式檢查器及參照。
輸入通過時回傳 0，驗證拒絕時回傳 2，並提供 JSON 錯誤與可用的 JSON Pointer。
現有 Artifact Trust workflow 的 Linux 與 Windows job 會執行同一個 CLI 和 fixtures。

## 現有 Gate 與候選

- License Gate 使用同一個驗證器載入 #708 原始 Schema 與現有欄位限制。Owner rights、檔案重雜湊、NOTICE 與 Registry 判定仍由原 License Gate 執行。
- Artifact Trust Schema 取自現有 #708／#706 manifest 結構。原信任 Gate 負責實際驗簽、上游政策及實際 bytes 驗證。
- 原始 Deployment Passport、Decision Request、Decision Response 與 Route Receipt 逐位元組保留。Deployment Passport 沿用 RC0 原本允許延伸的部分巢狀物件。
- RC0 Compatibility Manifest 與 Security／Privacy Baseline 的新增 Schema 用於原始快照結構。Bundle Manifest Schema 核對現有 builder 輸出契約。
- Billing Receipt `0.1-RC1-DRAFT` 依 MRL-39 及 RC0 Route Receipt 提出。它直接引用 Route Receipt 的 `pricing` 子 Schema，未知價格保留 `null`。正式計量、供應商計費規則及對帳仍由 MRL-39 承接。
- 版本比對使用各文件既有版本欄位或 Schema discriminator。RC0 → RC1 的轉換與保留規則需要正式核准的目標契約。

結構驗證結果只描述 Schema 符合度。正式商品採認、部署、DL580 實機驗證及授權由各既有流程保存獨立證據。
