# MRL Scaffold Generation 流程
> origin_signature: MrLiouWord  
> phase: 第十六包

---

## 完整路徑

```
ProductPack JSON（storage/packs/{pack_id}.json）
  ↓
POST /api/scaffold/generate { pack_id }
  → routes/scaffold.js
  → Scaffolds.generateFromPackId(packId)
     → PackExporter.loadPack(packId)   ← 讀取 pack
     → buildScaffoldPlan(pack)         ← 建計畫
        → _buildContext(pack)          ← pack → template 變數
        → templates.*                  ← 各檔案 stub 內容
        → manifest                     ← scaffold metadata
        → files: [{ path, content }]  ← 26+ 個檔案
     → writeScaffold(packId, plan)     ← 寫入 disk
        → storage/scaffolds/{pack_id}/
           ├── manifest.json
           ├── README.md
           ├── frontend/*.html + assets/
           ├── backend/server.js + routes/ + modules/
           ├── deploy/Dockerfile + docker-compose.yml + nginx.conf
           ├── .env.example
           └── docs/scaffold-notes.md
  ← response: { scaffold_id, pack_id, scaffold_dir, file_count, file_list, manifest }
```

---

## 哪些檔案從 Pack 取資料

| 檔案 | 使用的 pack 欄位 |
|------|----------------|
| `manifest.json` | 全部 |
| `README.md` | title / summary / core_judgment / scope / steps / doVsNot / deployment |
| `docs/scaffold-notes.md` | pages / flows / pricing_model / deployment |
| `frontend/*.html` | title / page.name / page.purpose / coreJudgment |
| `deploy/docker-compose.yml` | slug（from title）|
| `deploy/nginx.conf` | slug |
| `.env.example` | scaffold_id（metadata）|

---

## 哪些是固定 Stub（不從 pack 取資料）

- `backend/server.js` — express 基礎骨架
- `backend/routes/*.js` — TODO stub
- `backend/modules/*.js` — TODO stub
- `storage/schema.sql` — 最小 schema
- `frontend/assets/style.css` — 基礎樣式
- `frontend/assets/app.js` — 基礎互動 stub

這些檔案需要人工補完或參考 MRL_Product_v1 填充。

---

*origin_signature: MrLiouWord*
