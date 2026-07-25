# mrliouai_core — C++ 實作

origin_signature: MrLiouWord
version: 1.0.0
runtime: C++17 / POSIX，**零外部依賴**（不用 OpenSSL、不用 npm、不用 Cloudflare）

---

## 這是什麼

用 C++ 重寫 FireCore stub 模組與 Flask 空殼的**真實實作**。
架構邏輯沿用母體規格，程式碼不用他們的框架。

## 取代對象（逐一對照）

| 原檔案位置 | 原行數 | 原實際行為 | 本專案取代 |
|-----------|-------|-----------|-----------|
| `MRL_Mother/MRL_FireCore_v1_0/modules/mrl-firecore-auth/src/index.ts` | 91 | `authContract()` 回 202 `{accepted:false}`，零密碼哈希、零 JWT | `include/mrl/auth.hpp` — PBKDF2 600k 迭代 + HS256 JWT + refresh 輪替 |
| `MRL_Mother/MRL_FireCore_v1_0/modules/mrl-firecore-store/src/index.ts` | 91 | `storeContract()` 回 202 `{accepted:false}`，零 CRUD | `include/mrl/store.hpp` — 文件 CRUD + 樂觀鎖 + 版本歷史 + 查詢分頁 |
| `apps/module-a/app.py` | 28 | Flask 空殼，只有 health check | `src/main.cpp` — 完整路由服務 |
| `apps/orchestrator/app.py` | 61 | 只會 GET module-a/info 轉手，pymongo 宣告未用 | `src/main.cpp` — 真實編排 |
| `MRL_Mother/04_runtime/flowcontainer.py` Tracer | (規格來源) | Python 版 Merkle 鏈 | `include/mrl/merkle.hpp` — C++ 同規格 + 驗證 |
| `MRL_Mother/04_runtime/flowcore_loop.py` Vault | (規格來源) | Python 版沙箱 FS | `include/mrl/vault.hpp` — C++ 同規格 |

**原 stub 的關鍵字**：`"local contract response only; JWT private signing remains on DL580"`
**本實作**：JWT 真的在本地簽發，DL580 仍是資料權威來源（`dl580_sync_state` 欄位追蹤）。

---

## 檔案清單

```
mrliouai_core/
├── include/mrl/
│   ├── sha256.hpp     SHA-256 + HMAC-SHA256 + PBKDF2-HMAC-SHA256 + 常數時間比較
│   ├── base64.hpp     Base64 / Base64URL（JWT 用）
│   ├── json.hpp       JSON 解析 + 序列化（17 位精度，PHI 無損）
│   ├── merkle.hpp     Merkle 追蹤鏈 + 完整性驗證 + 原子狀態寫入
│   ├── auth.hpp       FireCore Auth 真實實作
│   ├── store.hpp      FireCore Store 真實實作
│   └── vault.hpp      沙箱檔案系統 + traversal 防護
├── src/main.cpp       HTTP 伺服器 + 全部路由接線
├── include/mrl/http.hpp   POSIX socket HTTP/1.1 + 路由 + 中間件
├── tests/selftest.cpp 106 項測試（含 NIST/RFC 官方測試向量）
└── Makefile
```

---

## 建構與測試

```bash
cd mrliouai_core
make test     # 跑 106 項自我測試
make          # 建構 ./mrliouai_core
make run      # 啟動於 :8800
```

實測結果：**PASS: 106  FAIL: 0**

測試涵蓋：
- SHA-256 — NIST FIPS 180-4 官方測試向量（含 1,000,000 x 'a' 多 block）
- HMAC-SHA256 — RFC 4231 Case 1 & 2
- PBKDF2-HMAC-SHA256 — 官方測試向量
- Base64 — RFC 4648 + UTF-8 來回
- JSON — 跳脫字元、`\uXXXX`、巢狀、缺欄位
- Merkle 鏈 — 鏈式相連 + **篡改偵測**
- 密碼 — 隨機 salt、錯密碼拒絕、畸形哈希拒絕、常數時間比較
- JWT — 簽發/驗證、錯 secret 拒絕、**偽造 payload 拒絕**、過期拒絕、**alg=none 降級攻擊拒絕**
- AuthService — 註冊/登入/refresh 輪替/**重放攻擊拒絕**/撤銷/持久化
- StoreService — CRUD、**樂觀鎖 409**、查詢過濾、cursor 分頁、軟刪除保留歷史
- Vault — 原子寫入、SHA-256、**5 種 traversal 攻擊全擋**

---

## 啟動

```bash
export MRL_JWT_SECRET=$(openssl rand -hex 32)   # 或任何 32 byte 隨機值
export MRL_HUMAN_TOKEN=<你的寫入權杖>

./mrliouai_core --port 8800 --data ./data --vault ./vault
```

| 參數 | 環境變數 | 預設 |
|------|---------|------|
| `--port` | `MRL_PORT` | 8800 |
| `--host` | — | 0.0.0.0 |
| `--data` | `MRL_DATA_DIR` | ./data |
| `--vault` | `MRL_VAULT_ROOT` | ./vault |
| `--secret` | `MRL_JWT_SECRET` | (未設則產生臨時值並警告) |
| `--token` | `MRL_HUMAN_TOKEN` | (未設則不強制寫入權杖) |

---

## API

### Auth（真實 JWT）

```bash
# 註冊
curl -X POST localhost:8800/v1/auth/signup \
  -H 'content-type: application/json' \
  -d '{"email":"mr@liou.tw","password":"my_real_password"}'
# → 201 {"ok":true,"user_id":"usr_...","password_algo":"pbkdf2_sha256","iterations":600000}

# 登入 → 拿真 JWT
curl -X POST localhost:8800/v1/auth/signin \
  -H 'content-type: application/json' \
  -d '{"email":"mr@liou.tw","password":"my_real_password"}'
# → {"access_token":"eyJhbGci...","refresh_token":"rt_...","expires_in":3600,"alg":"HS256"}

# 驗證
curl -H "authorization: Bearer $ACCESS" localhost:8800/v1/auth/verify
# → {"valid":true,"claims":{"sub":"usr_...","iss":"mrliouai","origin_signature":"MrLiouWord",...}}

# Refresh（自動輪替舊 token，防重放）
curl -X POST localhost:8800/v1/auth/refresh -d '{"refresh_token":"rt_..."}'

# 撤銷
curl -X POST localhost:8800/v1/auth/revoke -d '{"refresh_token":"rt_..."}'
```

### Store（真實 CRUD + 樂觀鎖）

```bash
# 建立
curl -X POST localhost:8800/v1/store/documents \
  -d '{"collection":"particles","doc_id":"p1","payload":{"type":"SEED","PHI":1.618033988749895}}'
# → 201 {"doc_id":"p1","version":1}

# 讀取（PHI 精度無損保存）
curl localhost:8800/v1/store/documents/particles/p1

# 更新（樂觀鎖：版本不符回 409 + current_version）
curl -X PUT localhost:8800/v1/store/documents/particles/p1 \
  -d '{"payload":{...},"expected_version":1}'

# 軟刪除（法則：不刪檔，資料與版本歷史全保留）
curl -X DELETE localhost:8800/v1/store/documents/particles/p1

# 查詢（collection + 欄位等值 + cursor 分頁）
curl -X POST localhost:8800/v1/store/query \
  -d '{"collection":"particles","field":"type","value":"SEED","limit":50}'

# 版本歷史
curl "localhost:8800/v1/store/history?collection=particles&doc_id=p1"

# 待同步 DL580 的文件
curl localhost:8800/v1/store/pending_sync
```

### Vault（沙箱檔案系統）

```bash
curl "localhost:8800/vault/list?path=."
curl "localhost:8800/vault/read_text?path=MrLiouWord.seed"
curl "localhost:8800/vault/info?path=MrLiouWord.seed"

# 寫入需 X-Human-Token
curl -X POST localhost:8800/vault/write_text \
  -H 'x-human-token: <你的權杖>' \
  -d '{"path":"MrLiouWord.seed","content":"怎麼過去，就怎麼回來"}'

curl -X POST localhost:8800/vault/mkdir -H 'x-human-token: ...' -d '{"path":"sub/deep"}'
```

Traversal 攻擊（`../../../etc/passwd`、`/etc/passwd`、`sub/../../..`）全部拒絕。

### Merkle 追蹤

```bash
curl localhost:8800/trace/root      # 當前 merkle_root 與 tick
curl localhost:8800/trace/verify    # 重算整條鏈，篡改則回 409
```

篡改任一位元組 → `{"chain_intact":false,"error":"event_hash tampered at tick N"}`

---

## 法則

**不刪檔。** 本 runtime 沒有任何破壞性刪除介面：

- Vault 不提供 `delete` / `unlink`
- Store 的 DELETE 是軟刪除，`deleted:true` 標記，payload 與版本歷史完整保留
- Merkle trace 是 append-only
- 所有寫入走 `.tmp` → `rename` 原子替換，不會半寫壞檔

## 安全設計

| 項目 | 做法 |
|------|------|
| 密碼儲存 | PBKDF2-HMAC-SHA256，600,000 迭代（OWASP 2023），32 byte 隨機 salt（`/dev/urandom`） |
| 密碼比較 | 常數時間，防 timing attack |
| 帳號枚舉 | 帳號不存在時仍跑一次哈希，回相同錯誤訊息 |
| JWT 演算法 | 只接受 HS256，明確拒絕 `alg=none` 降級 |
| JWT 簽章比較 | 常數時間 |
| Refresh token | 只存 SHA-256 哈希，不存明文；使用即輪替，舊 token 撤銷（防重放） |
| Vault 路徑 | canonical 解析 + root 包含檢查，符號連結解開後再驗 |
| 寫入權限 | `X-Human-Token` 常數時間比對 |
| 請求上限 | body 8 MB，header 64 KB |
| 稽核 | `auth_audit.jsonl` + Merkle 鏈雙寫 |

---

怎麼過去，就怎麼回來。
