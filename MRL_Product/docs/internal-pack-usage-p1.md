# MRL ProductPack 內部使用指南
> origin_signature: MrLiouWord  
> phase: 第十五包  
> 目前 Pack 是內部使用工具，不對外高調曝光

---

## 一、怎麼生成

### 方法 A：透過前端（推薦）

1. 進 `/app.html?cat=product`
2. 輸入問題，開始分析
3. 付款解鎖完整方案
4. 在結果頁底部找到 **「⬡ ProductPack Generator」** 區塊
5. 選擇 mode（做第一版網站 / 做第一版產品 / 做收費入口 / 產品收斂）
6. 點「生成 ProductPack」
7. 看到 Pack summary + 下載 JSON 按鈕

### 方法 B：直接呼叫 API

```bash
# 生成 pack
curl -X POST http://localhost:3000/api/pack/generate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {your_token}" \
  -d '{"analysis_id": "{analysis_id}", "mode": "website"}'
```

---

## 二、怎麼下載

```bash
# 下載 pack JSON
curl -O http://localhost:3000/api/pack/{pack_id}/download \
  -H "Authorization: Bearer {your_token}"
```

或在前端直接點「下載 Pack JSON」按鈕。

---

## 三、Pack JSON 包含什麼

```json
{
  "pack_id":      "mrl_pack_abc123def456",
  "title":        "先做付款入口",
  "mode":         "website",
  "mode_label":   "做第一版網站",
  "summary":      "核心摘要...",
  "core_judgment": "第一版真正該做的事",
  "first_version_scope": ["..."],
  "execution_steps": ["先做首頁", "再接付款", "..."],
  "do_vs_not_do": ["最優先：XXX", "暫緩：XXX"],
  "pages": [
    {"name": "index",   "purpose": "首頁",    "priority": "high"},
    {"name": "app",     "purpose": "分析入口", "priority": "high"},
    {"name": "pricing", "purpose": "定價",    "priority": "high"},
    ...
  ],
  "flows": [
    {"step": 1, "name": "landing",    "description": "進入首頁"},
    {"step": 2, "name": "input",      "description": "輸入問題"},
    ...
  ],
  "pricing_model": {
    "currency": "TWD",
    "once_amount": 299,
    "sub_amount": 499,
    "primary": "both"
  },
  "deployment": {
    "target": "DL580",
    "stack": ["Node.js 20", "SQLite", "Docker", "Nginx"],
    "command": "docker compose up -d --build",
    "env": ["ANTHROPIC_API_KEY", "STRIPE_SECRET_KEY", ...],
    "volumes": ["/opt/mrl_product_v1/storage:/app/storage", ...]
  }
}
```

---

## 四、Pack 拿去能做什麼

### 立即可做
- 把 `execution_steps` 貼進你的 TODO 工具，直接開始
- 把 `pages` 當作前端開發的功能清單
- 把 `flows` 當作 UX 設計的 user journey
- 把 `deployment` 的 `env` 清單當作 .env.example 參考
- 把 `do_vs_not_do` 的「暫緩」清單當作 scope 控制邊界

### 配合 deploy.md
```bash
# Pack 的 deployment.command 就是
docker compose up -d --build
```

### 第十六包後：Pack Scaffold
- Pack JSON → 前後端骨架代碼
- Pack JSON → docker-compose.yml
- Pack JSON → .env.example

---

## 五、Pack 存在哪

```
storage/packs/
└── mrl_pack_abc123def456.json
    mrl_pack_xyz789uvw012.json
    ...
```

也可用 admin API 列出所有 pack：
```bash
curl http://localhost:3000/api/pack \
  -H "X-Admin-Key: {admin_key}"
```

---

*origin_signature: MrLiouWord*
