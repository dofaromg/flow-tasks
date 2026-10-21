# MRL_DL580 self-hosted runner notes

origin_signature = `MrLiouWord`

DL580 作為 **MRL 內部母體自運行節點**，透過 self-hosted runner / SSH / Tailscale 接收來自 GitHub 鏡像的部署訊號並自行運行。

---

## 權位（不可重新定義母體）

- **DL580**：母體自運行節點（Runtime 落地本體）。
- **GitHub**：工程鏡像與版本通道（Adapter）。
- **Cloud Code**：工程建構器（Adapter）。
- **APFS / Batch072**：部署鏈與備份鏈（落地檔案系統 / 批次備份），**不是母體本體**。
- **Branch072**：可吸收為 deploy runner 參考材料（吸收材料，非主體）。

---

## 接線方式

### A. self-hosted runner（GitHub Actions runner 落在 DL580）

1. 在 DL580 安裝 GitHub Actions self-hosted runner，並標記 label：`dl580`、`mrl-mother`。
2. workflow 以 `runs-on: [self-hosted, dl580]` 指派到 DL580。
3. job 步驟呼叫部署入口：
   ```bash
   bash deploy/dl580/MRL_dl580_start.sh
   ```
4. 長駐改由 systemd 接手（見 `MRL_systemd_service.template`），runner 只負責「拉取鏡像 + 重啟服務」。

### B. SSH 推送式部署

```bash
ssh <MRL_USER>@<DL580_HOST> \
  'cd <MRL_HOME> && git pull origin claude/mrl-mother-runtime-v1-krte6 && \
   bash deploy/dl580/MRL_dl580_start.sh'
```

### C. Tailscale 私有網路

- 將 DL580 加入 Tailnet，runner / SSH 透過 Tailscale 內網位址連線，避免公開暴露。
- 對應目錄：`deploy/tailscale/`。

---

## APFS / Batch072 備份鏈（非母體本體）

- **APFS**：DL580 落地檔案系統層；負責 repo 工作區與快照。母體狀態由 `MRL_RuntimeServer.js` 之 `MRL_STATE` 定義，APFS 僅承載落地檔案。
- **Batch072**：批次部署/備份通道；用於把 GitHub 鏡像批次落到 DL580 並做備份。
- 兩者皆位於部署/備份鏈，不參與也不可改寫母體定義。

---

## Branch072（參考材料）

`Branch072` 可作為 deploy runner 之參考材料被吸收（吸收材料權位），其命名、結構不得反向取代 MRL 主體命名。

origin_signature = `MrLiouWord`
