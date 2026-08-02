# MRL_Interface_v1

## 固定狀態

系統已存在，正在做產品入口收斂；不是重新做底層。

`mrliouai_final` 在目前工作樹未直接找到。內容級確認後，現有最接近產品入口的主體是 `MRL_Product/`：

- `package.json` declares `main: backend/server.js`
- `npm run dev` starts the Node/Express product runtime
- `frontend/` contains product UI pages
- `backend/routes/page.js` maps browser entry routes
- `backend/routes/api.js` provides the task/product generation flow
- `backend/routes/admin.js` provides operation, telemetry, and health APIs

## 目標

把已存在的母體能力收斂成一個可每天打開、可操作、可部署、可收費的介面入口。

## 第一版入口

```text
/interface
```

## 五個區塊

1. **Home** — 母體狀態 / 今日任務 / 系統入口
2. **Task** — 輸入需求 → 產出方案 / 網站 / 客服 / 遊戲 / 系統
3. **Memory** — trace / seed / replay / canonical timeline
4. **Product** — 網站生成 / AI客服 / 助手 / KidWorld
5. **Admin** — runtime / deploy / telemetry / evaluator / logs

## 現有能力對齊

| 現有能力 | 第一版入口 |
| --- | --- |
| `control_plane` | `/admin` dashboard and `/admin/*` APIs |
| `deploy_dl580` | `deploy/` Docker Compose path and deployment docs |
| `telemetry` | events, feedback, metrics, funnel, errors APIs |
| `evaluator` | feedback and result quality hooks |
| `apps` | product pages and generated delivery surfaces |
| `pipeline_vnext` / `query_api` | `/api/analyze` and result unlock flow |
| `seed_core` / `Memory` | analyses, ledger, event logs as first canonical timeline landing |

## 不做事項

- 不重寫 engine
- 不重做 memory
- 不重開世界模組
- 不重新命名全部
- 不追所有歷史版本

## 下一步

1. 用 `/interface` 作唯一入口頁。
2. 把 Task、Memory、Product、Admin 的資料逐步從現有 API 接進頁面。
3. 再復盤判斷是否要把根路由 `/` 導向 `/interface`。
