# MRL_Network_Whitelist_Recovery_v1 — 雲端 session 網路放行與 bridge 復原

origin_signature = `MrLiouWord`
當下狀態：2026-07-06（沙盒 / Claude Code 雲端環境實測），**待放行後重驗**

---

## 現況（當下 2026-07-06，雲端 session 實測）

| 項目 | 狀態 |
|------|------|
| DL580 bridge 本體（`bridge.mrliouword.com`） | **活著**（使用者瀏覽器實測 `{"ok":true,"output":"PING"}`，實機） |
| 雲端 session → `bridge.mrliouword.com` | **封鎖**（agent proxy CONNECT tunnel 回 403，沙盒） |
| 雲端 session → `*.mrliouword.com` 全網域 | **封鎖**（bridge / dl580 / chat / 根網域皆 403，沙盒） |
| 7700 ASI Engine（`app\server.js`） | **紅**（面板顯示 DOWN，待診斷 — 見復原腳本 Phase 1） |
| bridge key | **舊 key 已在對話中曝光，待輪替作廢**（Phase 3） |
| 官網 OAuth / session | **待驗證**（Phase 4） |

> 結論：不是 DL580、不是 tunnel、不是 7700 的網路問題——是雲端環境的
> egress 網路政策把整個 `*.mrliouword.com` 擋在外面。依規不得繞過，只能放行。

---

## 放行步驟（使用者於環境設定操作，不在對話裡改）

1. 到啟動 session 的介面：claude.ai/code（網頁版）或 Claude Code 的
   **Environment settings / 環境設定**。
2. 找 **Network access（egress policy）** 設定。
3. 目前為受限政策 → 改為允許自訂網域，加入 **`mrliouword.com`（含子網域）**，
   或改用較寬鬆的網路政策。
4. 官方說明：<https://code.claude.com/docs/en/claude-code-on-the-web>
5. 放行後開新一輪對話（或重跑本 session），執行下方復原腳本。

---

## 放行後一次打完：復原腳本

腳本位置：`scripts/MRL_bridge_recovery_run.sh`

```bash
export MRL_BRIDGE_KEY=<目前有效的 bridge key>   # key 一律走環境變數，不得硬碼
bash scripts/MRL_bridge_recovery_run.sh all
```

| Phase | 內容 | 對應待辦 |
|-------|------|---------|
| 0 | bridge `/health` + `MRL_run` echo PING 連通性 | 前置 |
| 1 | 7700 診斷：netstat / node 命令列 / schtasks / 本機 health / log | ① 7700 為什麼紅 |
| 2 | 重啟 7700（schtasks 或 node 直啟），驗 `127.0.0.1:7700/health` | ① 復活 7700 |
| 3 | 產新 key、DL580 上換掉舊 key、驗「舊拒新通」 | ② key 輪替 |
| 4 | `mrliouword.com` 邊緣/轉發端點 + 登入端點狀態碼 | ③ 官網 OAuth |

Phase 1 的輸出會告訴你 Phase 2/3 需要的環境變數
（`MRL_7700_TASK` / `MRL_7700_HOME` / `MRL_BRIDGE_CONFIG` / `MRL_BRIDGE_TASK`），
可分段跑：`bash scripts/MRL_bridge_recovery_run.sh 1` → 設變數 → `... 2`。

---

## 驗收約定（沿用 CLAUDE.md / RuntimeOS 報告約束）

- 本文件所有「封鎖」結論為 **沙盒（雲端 session）當下狀態 2026-07-06**，
  放行後需重測，不是永久結論。
- 腳本每一 phase 以實際回應為準；沒實跑的項目一律維持「待驗證」。
- key 輪替完成的判準：**舊 key 被拒 + 新 key 回 NEWKEY（實機）**，缺一不可。

---

## Session re-test log（additive；只追加不覆蓋）

| 日期（環境） | 檢查 | 實測結果 | 判讀 |
|-------------|------|---------|------|
| 2026-07-06（雲端 session） | `MRL_BRIDGE_KEY` | 未設（`<unset>`） | key 走環境變數，尚未提供 → 無法過 Phase 0 `need_key` |
| 2026-07-06（雲端 session） | `curl https://bridge.mrliouword.com/health` | `CONNECT tunnel failed, response 403` | egress 政策擋 |
| 2026-07-06（雲端 session） | `curl https://mrliouword.com/health` | `CONNECT tunnel failed, response 403` | egress 政策擋（根網域也擋）|
| 2026-07-06（雲端 session） | agent proxy `/__agentproxy/status` | `recentRelayFailures`：`connect_rejected`「gateway answered 403 to CONNECT (policy denial or upstream failure)」，host `bridge.mrliouword.com:443` 與 `mrliouword.com:443` | **403 來自 gateway 的 CONNECT 拒絕，是本地 egress 政策，不是 DL580 / tunnel / 7700 的問題** |

> 判讀強化：403 出現在 **CONNECT tunnel 建立階段**（proxy relay `connect_rejected`），
> 代表封包還沒離開雲端環境就被本地政策擋下——與 DL580 本體、cloudflared tunnel、
> 7700 服務狀態無關。修法唯一路徑仍是上方「放行步驟」把 `mrliouword.com`
> （含子網域）加進 egress 白名單，放行後重跑 `scripts/MRL_bridge_recovery_run.sh all`。
