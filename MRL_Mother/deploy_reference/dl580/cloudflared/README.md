# deploy/dl580/cloudflared — bridge.mrliouword.com Cloudflare Tunnel 部署入口

origin_signature = `MrLiouWord`

將 DL580 母體節點的 MRL Runtime 透過 Cloudflare Tunnel 對外暴露為
`https://bridge.mrliouword.com`（v3.1.0，原 v2 使用 bridge.mrliouhan.ai），
免開放公網埠、免公網 IP、免處理憑證。

完整連線規格見：[MRL_bridge_connection_v3.1.0.md](MRL_bridge_connection_v3.1.0.md)

---

## 權位定位（不可重新定義母體）

| 角色 | 權位 | 說明 |
|---|---|---|
| **DL580** | **母體自運行節點** | MRL Runtime 本體在此運行 |
| **Cloudflare Tunnel** | **接線 / Adapter** | 對外橋接通道，與 Tailscale / SSH / self-hosted runner 同屬接線層，**非母體本體** |
| **bridge.mrliouhan.ai** | 對外入口 | 公開 hostname，映射到本地 Runtime |

> Cloudflare 僅為「接線層」，不參與母體定義。權位區分模式：MRL 為主體；外部基礎設施僅為 Adapter / 接線。

---

## 埠對齊（重要）

cloudflared ingress 的轉發目標必須對齊 Runtime 實際監聽埠：

- Runtime 預設 `MRL_PORT=8790`（見根 README 與 `MRL_RuntimeServer.js`）。
- 本部署腳本 `-MrlPort` 預設 `8790`，並讀取 `MRL_PORT` 環境變數。
- 原 v2 腳本指向 `7800`；本入口已對齊為 Runtime 實際埠，否則 `/health` 對外驗證會打到無服務的埠而失敗。
- 若 DL580 上另跑獨立 bridge 服務於 7800，執行時加 `-MrlPort 7800` 覆寫即可。

---

## 路徑（Batch 076，D: 路徑版）

因 C: 槽滿載，cloudflared 主目錄改置於 `D:\cloudflared`：

- 設定 `CLOUDFLARED_HOME=D:\cloudflared`（Machine 範圍），避免預設寫入 `C:\Users\`。
- `cloudflared.exe`、`cert.pem`、`<TUNNEL_ID>.json`、`config.yml` 全部落在 `D:\cloudflared`。

---

## 使用

```powershell
# 預設（hostname=bridge.mrliouhan.ai, port=8790, home=D:\cloudflared）
pwsh deploy/dl580/cloudflared/MRL_cloudflared_deploy.ps1

# 自訂埠 / hostname / 目錄
pwsh deploy/dl580/cloudflared/MRL_cloudflared_deploy.ps1 -MrlPort 7800 -Hostname bridge.mrliouhan.ai -CloudflaredHome D:\cloudflared
```

腳本流程（冪等，可重複執行）：

1. 建立 `D:\cloudflared` 並設定 `CLOUDFLARED_HOME`。
2. 下載 `cloudflared.exe`（已存在則略過；用 `curl.exe`，非 PowerShell 的 `curl` 別名）。
3. `tunnel login`（已有 `cert.pem` 則略過）。
4. `tunnel create mrl-dl580-tunnel`（已存在則略過）。
5. 自動偵測 `<TUNNEL_ID>.json` 並產生 `config.yml`（免手動填 TUNNEL_ID）。
6. `tunnel route dns` 綁定 hostname。
7. 註冊 Windows 服務並啟動（已安裝則僅啟動）。

---

## 驗證

```powershell
# 本地（DL580 上）
curl.exe http://localhost:8790/health
# 外部
curl https://bridge.mrliouhan.ai/health
```

預期回應含 `"ok": true` 與 `origin_signature: MrLiouWord`。

---

## 注意事項

- Windows PowerShell 的 `curl` 是 `Invoke-WebRequest` 別名，下載須用 `curl.exe`（腳本已採用）。
- `tunnel login` 需互動式瀏覽器授權，首次請於 DL580 桌面 session 執行。
- ingress 規則由上而下匹配，第一個命中者勝出；單一 hostname 規則即涵蓋 `/health`，毋須另設 path 規則（原 v2 把 `/health` 置於 catch-all 之後，永不命中且多餘，已移除）。

origin_signature = `MrLiouWord`
