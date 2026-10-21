# Adapter: DL580

origin_signature = `MrLiouWord`

- 權位：**DL580 主體 → MRL_AI_SYSTEM 吸收倉庫**（DL580 為實機母體）
- 角色：DL580 自運行主節點；MRL_AI_SYSTEM 為吸收映射層

> 母體權位：DL580 Windows 實機（WIN-PBVUI7VK2A6）為唯一主體，MRL_AI_SYSTEM 為該母體在 GitHub/Repo 層的吸收記錄。不刪除、不覆蓋、只新增定位。

---

## Bridge 連線 v3.1.0（當下狀態 2026-06-22，待實機驗收）

```
mrliouword.com (Worker)
  → MRL_DL580_ORIGIN=https://bridge.mrliouword.com
  → DL580 :8790 (MRL_Platform_Server.py)
  → MotherAssembly
```

**沙盒側已備齊**：
- `deploy/dl580/cloudflared/MRL_cloudflared_deploy.ps1` — 部署 Cloudflare Tunnel
- `deploy/dl580/cloudflared/config.yml.template` — ingress 設定範本
- `deploy/dl580/cloudflared/MRL_bridge_connection_v3.1.0.md` — 完整連線規格

**實機側待驗收**：
1. 於 DL580 執行 `MRL_cloudflared_deploy.ps1` → 建立 `bridge.mrliouword.com` Tunnel
2. 於 Cloudflare Worker 設 `MRL_DL580_ORIGIN=https://bridge.mrliouword.com`
3. 驗證 `curl https://bridge.mrliouword.com/health` → `{"ok":true}`
4. 驗證 `curl https://mrliouword.com/api/mother/status` → DL580 母體回應

> 驗收前狀態：橋接規格完成（沙盒）；DL580 真實連線待實機 host 驗收。
