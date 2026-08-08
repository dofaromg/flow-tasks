# Mrldl580 Evidence Package

本封包整理本次 DL580 本地伺服器檢查畫面與已確認結果。

## 核心結論

1. `MRL_Bridge` Windows 服務正在運行，啟動類型為 Automatic。
2. Bridge 主程式為 `D:\mrl\bridge\server.js`，Node 位於 `D:\MrlToolchain\node\node.exe`。
3. Bridge 使用 Port 7800。
4. 已存在 REST API：健康檢查、版本、檔案讀寫、命令執行、PostgreSQL、Redis、系統資訊、稽核及進度記錄。
5. 本次搜尋未確認正式 MCP Server 或 `/mcp` 路由。
6. Claude Remote Connector 應在既有 Bridge 上增加受控 MCP 轉譯層，不需重建後端。
