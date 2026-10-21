# deploy/dl580 — MRL_DL580_DeployRunner_v1

origin_signature = `MrLiouWord`

DL580 部署入口：使 `MRL_AI_SYSTEM` 可部署到 **DL580 母體節點自行運行**。

---

## 權位定位（不可重新定義母體）

| 角色 | 權位 | 說明 |
|---|---|---|
| **DL580** | **母體自運行節點** | MRL 內部母體在此自行運行（Runtime 本體落地處） |
| GitHub | Adapter / 鏡像 | 工程鏡像與版本通道，**不是母體** |
| Cloud Code | Adapter / 建構器 | 工程建構器，**不是母體** |
| APFS | 部署鏈 / 備份鏈 | 檔案系統與備份層，**不是母體本體** |
| Batch072 | 部署鏈 / 備份鏈 | 批次部署與備份通道，**不是母體本體** |
| Branch072 | 參考材料 | 可吸收為 deploy runner 參考材料（吸收材料，非主體） |

> 權位區分模式：MRL 為主體；上述外部/基礎設施僅為 Adapter / 映射節點 / 吸收材料。

---

## 部署鏈

```
Cloud Code (建構器)
  → GitHub: dofaromg/MRL_AI_SYSTEM (鏡像/版本通道)
  → deploy/dl580 (本入口)
  → Tailscale / SSH / self-hosted runner / Cloudflare Tunnel (接線)
  → DL580 本地 Runtime
  → MRL_RuntimeServer.js
  → MRL 母體自行運行
```

APFS / Batch072 為部署與備份鏈，掛在「DL580 本地 Runtime」這一段之下，負責落地檔案系統與批次/備份，不參與母體定義。

---

## 啟動入口

| 平台 | 入口 |
|---|---|
| Linux / DL580 (bash) | `deploy/dl580/MRL_dl580_start.sh` |
| Windows / PowerShell | `deploy/dl580/MRL_dl580_start.ps1` |
| 長駐服務 (systemd) | `deploy/dl580/MRL_systemd_service.template` |
| self-hosted runner | `deploy/dl580/MRL_selfhosted_runner_notes.md` |
| 對外橋接 (Cloudflare Tunnel) | `deploy/dl580/cloudflared/MRL_cloudflared_deploy.ps1` → `bridge.mrliouword.com` (v3.1.0) |

啟動流程（與根 README 一致）：

```bash
npm install
npm run MRL_boot
npm start          # MRL_RuntimeServer.js，預設 MRL_PORT=8790
npm run MRL_acceptance
```

---

## 部署前檢查

```bash
bash scripts/MRL_dl580_deploy_check.sh        # Linux / DL580
# 或
pwsh scripts/MRL_dl580_deploy_check.ps1       # Windows / PowerShell
```

檢查項：Node version、package.json、MRL_RuntimeServer.js、required docs、deploy/dl580 scripts，以及（若 Runtime 已長駐）`/health` 可達性。

---

## 環境變數

| 變數 | 預設 | 說明 |
|---|---|---|
| `MRL_PORT` | `8790` | Runtime 監聽埠 |
| `MRL_HOME` | repo 根目錄 | DL580 上 repo 落地路徑 |

origin_signature = `MrLiouWord`
