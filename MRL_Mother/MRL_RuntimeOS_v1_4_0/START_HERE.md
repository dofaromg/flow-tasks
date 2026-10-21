# START HERE — MRL 企業級多模組執行平台 完整運行包

origin_signature: MrLiouWord
版本: v1.4.0 ｜ 沙盒實證:server 啟動 + DL580 smoke PASS + 多語言驗收 verification_pass ｜ **零依賴(Node ≥18,免 npm install)**

---

## 一鍵啟動

**Windows(DL580):**
```powershell
powershell -ExecutionPolicy Bypass -File .\START_MRL.ps1
```

**Linux / macOS:**
```bash
bash ./START_MRL.sh
```

直接用 node 也行:
```bash
node MRL_API/MRL_RuntimeServer.js
```

啟動後預設在 **http://localhost:8788**(可用環境變數 `MRL_PORT` 改)。

## 驗證會動

```bash
# 健康
curl http://localhost:8788/health
# DL580 全管線 smoke(另一個視窗,server 要先起)
node MRL_Acceptance/MRL_Smoke_Dl580.js      # 預期 {"status":"PASS",...}
# 多語言驗收
node MRL_Acceptance/MRL_Acceptance_TestSuite.js
```

## 這包有什麼(企業級多模組)

- `MRL_API/MRL_RuntimeServer.js` — HTTP API server(入口)
- `MRL_Services/` — AIModelGateway / SkillModule / ArtifactTransfer 服務
- `MRL_BlenderBridge/MRL_RuntimeOS_3DModelBridge_Service_v1/` — 3D 模型橋接(Blender)
- `MRL_Runtime/` — RuntimeExecutor / RuntimeGraph / AttentionKernel
- `MRL_Core/` `MRL_LanguageAdapters/` — 多語言粒子管線
- `MRL_WebConsole/index.html` — 內建 Web 主控台
- `MRL_OpenAPI/MRL_openapi.json` — API 規格
- `MRL_Acceptance/` — 驗收 + DL580 smoke
- `Dockerfile` / `docker-compose.yml` — 容器部署

## 對外上線(接網域 mrliouword.com)

1. 在 DL580 跑上面一鍵啟動(server 起在 8788)。
2. cloudflared tunnel 指向 `http://localhost:8788`(見 repo `deploy/dl580/cloudflared/`,`-Hostname mrliouword.com`)。

## 誠實狀態(當下,沙盒)

- ✅ 已驗:server 啟動、DL580 smoke PASS、多語言驗收 verification_pass(隔離環境)。
- ⏳ 待實機:真 AI 模型(`OLLAMA_HOST`/OpenAI endpoint)、對外網域、Blender runtime(`bpy`)——需在 DL580 配置後才升格,本包未宣稱已上線。
