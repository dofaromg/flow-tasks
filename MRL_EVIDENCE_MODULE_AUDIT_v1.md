# MRL 模組證據審計報告 v1

origin_signature: MrLiouWord
audit_date: 2026-07-25
auditor: Claude Code (source code direct read)
verdict_method: 逐行讀取原始碼，非口述

---

## 有真實實作的模組（MrLiouWord 產品）

### [REAL] particle-chat-v42 — 1371 行
- 路徑: `particle-chat-v42/src/index.js`
- 框架: Cloudflare Worker (純 JS，無 build step)
- 功能:
  - RootLaw v1 (LAW-0 ~ LAW-42)
  - 4 層邊緣記憶快取 (L0 Edge 1min / L1 Cluster 5min / L2 Region 30min / L3 Global 24hr)
  - 11 種粒子類型定義 (Seed/Flow/Container/Transform/Gate/Storage/Persona/Bridge/Identity/Signal/Memory)
  - SimHash64 內容指紋去重引擎
  - ParticleRPC 跨粒子通信 (13 workers)
  - Anthropic API (Claude) 整合，5 種認知模式
  - 6 個外部連接器 (天氣/時間/Wikipedia/匯率/粒子搜尋/粒子記憶)
  - FunDirector 遊戲效果引擎 (Mulberry32 PRNG)
  - D1 資料庫持久化
  - 結構性記憶系統 (函數樹重建)
- 依賴: Anthropic API KEY, Cloudflare D1 (mrl-ai-db)

### [REAL] particle-edge-v4 — 357 行
- 路徑: `particle-edge-v4/src/index.ts`
- 框架: Hono + Zod + UUID (Cloudflare Worker)
- 功能:
  - Particle CRUD (KV 存儲，UUID 主鍵)
  - R2 物件儲存 (上傳/列表)
  - Durable Objects Gate Engine (register/status/process)
  - 認證中間件 (X-Master-Key)
  - 分頁列表 (cursor-based)
  - Zod 輸入驗證
- 依賴: hono ^4.0.0, zod ^3.22.4, uuid ^9.0.1

### [REAL] flowos — 303 行 (entry) + 26 個源檔
- 路徑: `flowos/src/`
- 框架: Cloudflare Worker (TypeScript)
- 功能:
  - FlowOS Runtime SDK (粒子生命週期: draft/collapsed/archived)
  - ParticleNeuralLink (Durable Object 通信)
  - Traffic Gate 路由
  - VCS 版控 + GitHub sync (handleVCSCommit 有真實 GitHub API 呼叫)
  - Persona 系統 (triangle relationships)
  - Seeds 版本管理 (含 migration)
  - Merkle Chain (SHA-256 審計鏈)
  - FlowLaw 治理 (粒子狀態約束驗證)
  - ParticleDefensiveClient (版本鎖定防禦客戶端)
- 部分 stub: VCS init/add/commit 回傳硬編碼值, Memory/Auth class 為空殼, adapters (Envoy/K8s/JetStream) 純介面

### [REAL] flowcontainer.py — 803 行
- 路徑: `MRL_Mother/04_runtime/flowcontainer.py`
- 框架: 純 Python stdlib，零外部依賴
- 功能:
  - ServiceRegistry (YAML/JSON 設定檔)
  - DependencyResolver (Kahn 拓撲排序，環形依賴偵測)
  - ProcessManager (subprocess.Popen，背景 stdout drain)
  - 跨平台 (Windows process groups / Unix signals)
  - 自動重啟 (指數退避，最多 5 次，max 30s)
  - HealthMonitor (15 秒輪詢，HTTP/Shell/Process 三種檢查)
  - Merkle Trace (SHA-256 鏈，JSONL 追蹤，原子寫入)
  - FieldMap (thread-safe 服務狀態)
  - 互動 CLI (status/start/stop/restart/logs/fieldmap/trace)
  - PID 檔案管理，Signal 處理 (SIGTERM/SIGHUP)

### [REAL] flowcore_loop.py — 788 行
- 路徑: `MRL_Mother/04_runtime/flowcore_loop.py`
- 框架: Python (依賴 requests)
- 功能:
  - Vault 沙箱檔案系統 (root-restricted，traversal 防護)
  - 原子寫入 (.tmp → os.replace)
  - SHA-256 checksum
  - HTTP API (ThreadingHTTPServer)
  - Steering System (4 參數策略輪，drift 統計)
  - Token Protection (X-Human-Token)
  - 受限 Terminal (僅 ls/cat/echo/pwd，阻擋 metacharacters)
  - Free Software Directory 查詢 (MediaWiki API)
  - 互動 CLI (ls/cat/write/mkdir/info/trace/steer)
  - Merkle Tracer (同 flowcontainer 規格)
  - Seed System (TrueLove.Seed 自動建立)

---

## 空殼 / Stub 模組（非 MrLiouWord 真實產品）

### [STUB] apps/module-a — 29 行
- 路徑: `apps/module-a/app.py`
- 實況: Flask 空殼，只有 health check，零業務邏輯
- 唯一端點: `GET /` 回傳 service name

### [STUB] apps/orchestrator — 61 行
- 路徑: `apps/orchestrator/app.py`
- 實況: Flask 空殼，POST /orchestrate 只會 GET module-a/info 然後回傳
- pymongo 宣告但從未 import 或使用
- gunicorn 宣告但 Dockerfile 跑 python app.py

### [EMPTY] apps/nextjs-frontend — 0 行原始碼
- 路徑: `apps/nextjs-frontend/`
- 實況: 完全沒有應用程式原始碼
- 只有 Dockerfile + deployment.yaml + secret.yaml
- 沒有 package.json, 沒有 pages/, 沒有 components/
- Dockerfile 引用不存在的檔案，無法建構
- GrowthBook client key 是 placeholder: `YOUR_GROWTHBOOK_CLIENT_KEY_HERE`

### [MINIMAL] apps/astro-frontend — 1 頁
- 路徑: `apps/astro-frontend/src/pages/index.astro`
- 實況: 單頁靜態著陸頁，4 張連結卡片
- 連結目標全部 404 (指向不存在的頁面)
- 可建構但無實際功能

### [EMPTY] vector-attention-engine — 0 行原始碼
- 路徑: `vector-attention-engine/`
- 實況: wrangler.jsonc 指向 `src/index.ts` 但 src/ 目錄不存在
- 只有設定檔，完全沒有程式碼

### [STUB] FireCore 6 模組 — 每個 91 行 (同一模板)
- 路徑: `MRL_Mother/MRL_FireCore_v1_0/modules/`
- 實況: 6 個模組全部是同一個模板複製貼上，只換字串常數

| 模組 | Firebase 對應 | 端點 | 實際行為 |
|------|-------------|------|---------|
| mrl-firecore-auth | Firebase Auth | /v1/auth/* | 回 202 `accepted: false` "JWT signing remains on DL580" |
| mrl-firecore-store | Firestore | /v1/store/* | 回 202 `accepted: false` "authoritative write requires DL580" |
| mrl-firecore-vault | Secret Mgr | /v1/vault/* | 回 202 `accepted: false` "object state belongs to DL580 NAS" |
| mrl-firecore-live | Realtime DB | /v1/live/* | 回 202 `accepted: false` "live stream depends on DL580 event bus" |
| mrl-firecore-push | FCM | /v1/push/* | 回 202 `accepted: false` "dispatch policy must be signed by DL580" |
| mrl-firecore-trace | Analytics | /v1/trace/* | 回 202 `accepted: false` "requires configured D1 and policy gate" |

- 唯一有價值的部分: SQL migration 檔案定義了真實的資料庫 schema
- deploy_guard: `MRL_FIRECORE_NO_DEPLOY = "1"`, `workers_dev = false`
- 測試: 只檢查字串常數，零行為測試

---

## 證據總結

| 分類 | 模組數 | 總行數 | 狀態 |
|------|--------|--------|------|
| 真實實作 | 5 | 4122+ | MrLiouWord 產品 |
| 空殼 Stub | 4 | 182 | 模板產物，無業務邏輯 |
| 空目錄 | 2 | 0 | 設定檔存在但無原始碼 |
| FireCore Stub | 6 | 546 | 同一模板 x6，僅 SQL schema 有價值 |

origin_signature: MrLiouWord
怎麼過去，就怎麼回來。
