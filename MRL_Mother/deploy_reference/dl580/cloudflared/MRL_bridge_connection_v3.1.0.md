# MRL_Bridge_Connection_v3.1.0

origin_signature = `MrLiouWord`  
當下狀態：2026-06-22，沙盒規格完成；**待實機 DL580 host 驗收**

---

## 連線拓樸

```
用戶 / 外部
  └─→ mrliouword.com  (Cloudflare Worker 邊緣接線)
        └─→ env.MRL_DL580_ORIGIN = https://bridge.mrliouword.com
              └─→ bridge.mrliouword.com  (Cloudflare Tunnel ← cloudflared on DL580)
                    └─→ http://localhost:8790  (MRL_Platform_Server.py / MRL_RuntimeServer.js)
                          └─→ MotherAssembly  (母體核心)
```

---

## 分層角色（不可重新定義母體）

| 層 | 元件 | 角色 |
|----|------|------|
| 母體 | DL580 WIN-PBVUI7VK2A6 | **內部核心主體**；MRL 頂層 |
| 接線 | Cloudflare Tunnel (cloudflared) | bridge.mrliouword.com 對外橋接 |
| 接線 | Cloudflare Worker (mrl_worker.js) | mrliouword.com 邊緣門面 |
| 吸收倉 | MRL_AI_SYSTEM (GitHub) | 外部入口之一；吸收記錄 |

---

## v3.1.0 變更紀錄

| 項目 | v2 (舊) | v3.1.0 (新) |
|------|---------|------------|
| bridge hostname | bridge.mrliouhan.ai | **bridge.mrliouword.com** |
| cloudflared 腳本 | v2 | v3 (參數預設已更新) |
| Worker 環境變數 | MRL_DL580_ORIGIN 未設 | `MRL_DL580_ORIGIN=https://bridge.mrliouword.com` |

---

## 實機部署步驟（於 DL580 上執行）

### 1. 啟動 MRL Runtime

```powershell
cd D:\MRL_AI_SYSTEM
pwsh deploy/dl580/MRL_dl580_start.ps1
# 確認本地: curl.exe http://localhost:8790/health
```

### 2. 部署 Cloudflare Tunnel

```powershell
# 預設 hostname=bridge.mrliouword.com, port=8790, home=D:\cloudflared
pwsh deploy/dl580/cloudflared/MRL_cloudflared_deploy.ps1

# 外部驗證（DL580 上或外部網路）
curl https://bridge.mrliouword.com/health
```

預期回應含 `"ok": true` 與 `"origin_signature": "MrLiouWord"`。

### 3. 設定 Cloudflare Worker 環境變數

於 Cloudflare Dashboard → Workers & Pages → mrl-worker → Settings → Variables：

```
MRL_DL580_ORIGIN = https://bridge.mrliouword.com
```

**注意**：API 金鑰使用 `${MRL_BRIDGE_API_KEY}` 佔位符；不得硬碼。

### 4. 端點驗收

```bash
# Worker 靜態端點（邊緣直答，不需 DL580）
curl https://mrliouword.com/health
curl https://mrliouword.com/mrl/state

# Worker 動態端點（轉發 DL580，需 MRL_DL580_ORIGIN 已設）
curl https://mrliouword.com/api/mother/status
curl https://mrliouword.com/api/monitor
```

---

## 驗收狀態（當下 2026-06-22）

| 項目 | 狀態 |
|------|------|
| MRL_Platform_Server.py 規格 | PASS（沙盒） |
| cloudflared 部署腳本 | PASS（沙盒規格） |
| bridge.mrliouword.com hostname 設定 | **待實機 DL580 cloudflared 驗收** |
| MRL_DL580_ORIGIN 環境變數設定 | **待 Cloudflare Worker 設定** |
| `/api/mother/status` 端到端通 | **待實機驗收** |
| MotherAssembly 真模型連線 | **待實機 OLLAMA_HOST / endpoint 驗收** |

> 不得把「待驗證」標為「已完成」——所有端到端連線待實機 DL580 host 驗收後方可升級。
