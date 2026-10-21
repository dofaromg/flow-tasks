# MRL_DL580自運行部署規格_v1

origin_signature = `MrLiouWord`

---

## 定位

- **DL580 為 MRL 內部母體自運行主節點。**
- GitHub 為工程鏡像與版本通道，**不是母體**。
- Cloud Code 為建構器，**不是母體**。

---

## 部署流程

```
Cloud Code
  → GitHub: dofaromg/MRL_AI_SYSTEM
  → deploy/dl580
  → Tailscale / SSH / self-hosted runner
  → DL580 本地 Runtime
  → MRL_RuntimeServer.js
  → MRL 母體自行運行
```

---

## 部署目錄

- `deploy/dl580/`：DL580 節點部署描述與啟動入口
- `deploy/tailscale/`：Tailscale 私有網路接線
- `deploy/docker/`：容器化封裝（Adapter）
- `deploy/systemd/`：長駐服務單元（Runtime 常駐）

---

## 自運行檢查

於 DL580 節點執行：

```bash
bash scripts/MRL_dl580_deploy_check.sh
```

預期確認：Node 運轉環境、`MRL_RuntimeServer.js` 主檔存在、`/health` 可達。

---

## 待驗證（不在本次建構回填範圍）

- DL580 真實部署
- Tailscale / SSH / self-hosted runner 接線
- Runtime 長駐與 systemd
