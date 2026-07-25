# Evidence Notes

## 已確認

- `MRL_Bridge` 服務正在執行。
- `server.js` 顯示 Port 7800、GET/POST 雙模式與 API Key SHA-256。
- `/MRL_run` 支援 `cmd`、`cwd`、`timeout`。
- `/MRL_exec` 支援 POST 命令執行。
- 存在 PostgreSQL、Redis、檔案讀寫、系統資訊、稽核與進度紀錄 API。
- 本機已有 Memory、Toolchain、Runtime、Inference、Operations、MrLiouAI 等程序。
- 搜尋命中的 `initialize` 多數來自 node_modules 或一般初始化函式，不能視為 MCP 證據。

## 尚未確認

- `/mcp` 實際回應。
- MCP `initialize`、`tools/list`、`tools/call`。
- Claude 可用的公開 HTTPS MCP URL。
- OAuth 或 Dynamic Client Registration。

## 安全

Bridge 具備命令執行、檔案讀寫、資料庫與 Redis 操作能力。對外整合應只暴露白名單工具，不應直接把 `/MRL_exec` 或 `/MRL_run` 當成 MCP 公開入口。
