# MRL_Bridge_API v3.1.0 — DL580 母體通道層完整封包

```
origin_signature : MrLiouWord
版本             : v3.1.0
封包日期         : 2026-05-08
封包者           : Claude (Opus 4.7)
擁有者           : MR.liou (MrLiouWord)
歸屬             : MRL系統 / DL580 母體
類型             : 部署封包 (deployment_package)
```

> 🔒 **這是 DL580 上正在運行的 MRL_Bridge v3.1.0 完整原始封包**
> 從 https://bridge.mrliouword.com 主機 (WIN-PBVUI7VK2A6) 完整抓取
> 11/11 檔案 sha256 經 DL580 端校驗一致

---

## 一、這個封包是什麼

**MRL_Bridge_API** 是 DL580 母體的**對外 API 入口**：

```
Claude (web/desktop)
       ↓
Cloudflare Tunnel (https://bridge.mrliouword.com)
       ↓
DL580 :7800 ← 這個服務
       ↓
PG / Redis / 檔案 / PowerShell
```

**不是** MRL_FlowEditBridge (那是不同的東西，方向相反)：
- MRL_Bridge v3.1.0 = **入境** (外部 → DL580)
- MRL_FlowEditBridge v0.2 = **出境** (DL580 → 外部雲)

兩者互補不替代。

---

## 二、檔案清單 (11 檔 / 196,745 bytes)

| 檔 | 大小 | 用途 |
|---|---|---|
| `bridge/server.js` | 30,914 B | **主檔 v3.1.0**，含 18 個 endpoint |
| `bridge/package.json` | 316 B | npm dependency 清單 |
| `bridge/package-lock.json` | 35,735 B | 鎖定版本 |
| `bridge/add_platform_route.cjs` | 1,391 B | 動態加 platform route 工具 |
| `bridge/MRL_bridge_route_patch.cjs` | 1,756 B | route patch 工具 |
| `bridge/patch_v31.js` | 2,839 B | v3.1 升級 patch (v3.0→v3.1) |
| `bridge/patch_v31.ps1` | 2,806 B | v3.1 升級 PowerShell |
| `bridge/server.js.bak_platform` | 30,322 B | LAW-2 備份 (rename 前) |
| `bridge/server_v1.0.0.js` | 30,222 B | LAW-2 歷史版本 |
| `bridge/server_v3.0_backup.js` | 30,222 B | LAW-2 v3.0 備份 |
| `bridge/server_v3.0_pre_rename.js` | 30,222 B | LAW-2 改名前 v3.0 |

---

## 三、18 個 API Endpoints

### 公開 (無需 key)
- `GET /health` — 健康檢查 (回 service/version/origin_signature/api/pg/redis/uptime/stats)
- `GET /version` — 版本資訊
- `GET /MRL_platform` — platform 路由

### 認證 GET (`?key=REDACTED_USE_ENV`)
- `GET /MRL_pg?sql=...` — PG 查詢 (URL-encoded SQL)
- `GET /MRL_tables` — 列出所有 PG tables
- `GET /MRL_ls?path=...` — 目錄列表
- `GET /MRL_cat?path=...` — 讀檔內容
- `GET /MRL_run?cmd=...` — 執行 PowerShell/cmd 指令
- `GET /MRL_redis_cmd?cmd=...` — Redis 指令
- `GET /MRL_sysinfo` — 系統資訊
- `GET /MRL_write?path=...&content=...` — 簡單寫檔
- `GET /MRL_audit` — 操作記錄

### 認證 POST (`x-api-key: REDACTED_USE_ENV`)
- `POST /MRL_file/write` — 大檔寫入 (JSON: `{filepath, b64, mkdir}`)
- `POST /MRL_file/read` — 大檔讀取
- `POST /MRL_file/list` — 目錄列表
- `POST /MRL_exec` — 執行指令
- `POST /MRL_pg/query` — 大型 SQL 查詢
- `POST /MRL_redis` — Redis 操作

---

## 四、認證

```
header: x-api-key: REDACTED_USE_ENV         (POST)
query : ?key=REDACTED_USE_ENV               (GET)
sha256: API_KEY_HASH 寫死在 server.js
```

---

## 五、部署需求

| 項 | 版本 |
|---|---|
| OS | Windows (DL580 用 Windows Server) |
| Node.js | v20.11.1 (路徑 `D:\MrlToolchain\node\node.exe`) |
| npm | 10.2.4 |
| PostgreSQL | 16.8 (本機, 必要) |
| Redis | 5.0.14 (本機, 必要) |
| nssm | 2.24 (`D:\nssm\nssm-2.24\win64\nssm.exe`) |
| Cloudflare Tunnel | tunnel id `632dfad4-...` (對外路由) |

### npm dependencies (3 個)
```json
{
  "express": "^5.2.1",
  "ioredis": "^5.10.1",
  "pg": "^8.20.0"
}
```

---

## 六、Service 設定 (nssm)

```
ServiceName  : MRL_Bridge
Application  : D:\MrlToolchain\node\node.exe
AppDirectory : D:\mrl\bridge
AppParameters: D:\mrl\bridge\server.js
Start        : SERVICE_AUTO_START
Status       : RUNNING (port 7800)
```

---

## 七、安裝步驟 (還原到新主機)

```powershell
# 1. 解壓本封包到 D:\mrl\bridge\
Expand-Archive MRL_Bridge_v3.1.0_package.zip -DestinationPath D:\mrl\

# 2. 確認 Node.js 已裝
node --version  # 應該 >= v20

# 3. 安裝 dependencies
cd D:\mrl\bridge
npm install

# 4. 確認 PG/Redis 在跑
sc query postgresql; sc query mrl_redis

# 5. 確認 API_KEY 環境變數 (server.js 寫死,通常不需改)
# API_KEY_HASH = SHA-256("REDACTED_USE_ENV_MRL_BRIDGE_API_KEY")

# 6. 註冊 Windows Service
$nssm = "D:\nssm\nssm-2.24\win64\nssm.exe"
& $nssm install MRL_Bridge "D:\MrlToolchain\node\node.exe" "D:\mrl\bridge\server.js"
& $nssm set MRL_Bridge AppDirectory "D:\mrl\bridge"
& $nssm set MRL_Bridge Start SERVICE_AUTO_START
& $nssm set MRL_Bridge AppStdout "D:\mrl\bridge\logs\nssm_stdout.log"
& $nssm set MRL_Bridge AppStderr "D:\mrl\bridge\logs\nssm_stderr.log"

# 7. 啟動
& $nssm start MRL_Bridge

# 8. 健康檢查
Invoke-RestMethod -Uri http://127.0.0.1:7800/health
```

---

## 八、LAW-2 還原能力

包內 4 個歷史版本:
- `server_v1.0.0.js`            ← 最早版
- `server_v3.0_backup.js`       ← v3.0 完整備份
- `server_v3.0_pre_rename.js`   ← v3.0 改名前
- `server.js.bak_platform`      ← v3.1 platform route 加之前

要還原任一版本：
```powershell
cp D:\mrl\bridge\server_v3.0_backup.js D:\mrl\bridge\server.js
& $nssm restart MRL_Bridge
```

---

## 九、給未來的我 (下個 Claude 視窗) — 銜接指引

如果你拿到這個封包,你就是新視窗的 Claude。讀順序:

1. **本檔** (`README.md`)
2. **`MANIFEST.json`** — 完整 sha256 校驗清單
3. **`bridge/server.js`** — 主檔 (有 BOM 頭中文註解,UTF-8)
4. **`INSTALL.md`** — 部署細節

關鍵設定值 (寫死在 server.js):
- VERSION = '3.1.0'
- PORT = 7800
- ORIGIN = 'MrLiouWord'
- API_KEY_HASH = SHA-256((process.env.MRL_BRIDGE_API_KEY || ''))
- LOG_DIR = 'D:\\mrl\\bridge\\logs'
- MAX_FILE_READ = 5 MB

如果你要改 server.js: **先 cp 一份 .bak_*** (LAW-2)。

---

## 十、出處與信任根

```
源: WIN-PBVUI7VK2A6 (DL580)
   D:\mrl\bridge\
封包時 service 狀態: RUNNING
封包時 uptime: 220246+ 秒 (約 2.5 天)
Tunnel: bridge.mrliouword.com (CF tunnel id 632dfad4)
封包者: Claude (Opus 4.7) 透過 Bridge API 自抓 — sha256 雙端校驗
```

origin_signature: MrLiouWord
