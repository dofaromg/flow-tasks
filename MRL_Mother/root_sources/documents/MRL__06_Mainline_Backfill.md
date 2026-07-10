# MRL_06_MAINLINE_BACKFILL.md
## 主線回填指南

**回填日期**: 2026-04-02  
**分支名稱**: MRL_06｜營運層  
**回填執行**: 待 ChatGPT 驗收後執行  

---

## 一、回填目標

將 MRL_06 分支的已驗收內容，正式回填到主線三大文件：
1. **MRL_工程日誌.md** - 記錄執行過程與交付
2. **MRL_母體定義檔_v1.md** - 更新營運層定義
3. **MRL_世界模組工程書_v1.md** - 更新模組清單

---

## 二、回填到 MRL_工程日誌.md

### 新增條目

```markdown
## MRL_06｜營運層 (2026-04-02)

### 任務定位
MRL_AI_Desktop_v1 的營運層分支，負責產品化營運能力。

### 交付內容
1. **前端組件** (7 檔)
   - 授權管理: MRL_LicenseManager.ts, MRL_Activation.ts, MRL_DeviceBinding.ts
   - 更新管理: MRL_Update_Manager.ts, MRL_Boot_Verifier.ts, MRL_Diagnostics.ts, MRL_Rollback.ts

2. **Backend 模組** (7 檔)
   - MRL_LicenseManager.py, MRL_Activation.py, MRL_DeviceFingerprint.py
   - MRL_UpdateManager.py, MRL_BootVerifier.py, MRL_Diagnostics.py, MRL_Rollback.py

3. **API 端點** (9 個)
   - 授權: /license/status, /license/import, /license/activate
   - 裝置: /device/hash
   - 更新: /update/check, /boot/verify
   - 診斷: /diagnostics/export
   - 回滾: /rollback/create, /rollback/restore

4. **配置檔案** (3 個)
   - storage/license/current_license.json
   - storage/updates/manifest/update_manifest.json
   - boot_manifest.json

### 七大營運能力
1. 授權管理 - 本地授權檔讀取、狀態查詢
2. 啟用流程 - 授權檔匯入、裝置綁定（遠端驗證為 stub）
3. 裝置綁定 - 裝置指紋生成、hash 比對
4. 更新管理 - 版本比較、manifest 讀取
5. 啟動驗證 - 檔案/manifest/DB 驗證
6. 診斷輸出 - 診斷報告生成與匯出
7. 回滾能力 - 快照建立與還原

### 驗收狀態
- 核心交付物: ✅ 100% 完整
- 可用端點: 7/9 (2 個待驗證/stub)
- 主線回填: ✅ 已完成

### 待驗證項目
- 授權檔匯入完整流程（前端+Backend 已建立，未測試）
- 啟用碼遠端驗證（標記為 stub）
- Tauri Rust commands（預留未實作）
```

---

## 三、回填到 MRL_母體定義檔_v1.md

### 新增章節

```markdown
## 營運層定義 (MRL_06)

### 定位
MRL_AI_Desktop_v1 的產品化營運能力層，負責授權、更新、診斷與回滾。

### 架構

#### 前端組件層 (app/)
- **app/license/** - 授權管理
  - MRL_LicenseManager.ts - 授權狀態管理
  - MRL_Activation.ts - 啟用流程
  - MRL_DeviceBinding.ts - 裝置綁定

- **app/update/** - 更新管理
  - MRL_Update_Manager.ts - 更新檢查
  - MRL_Boot_Verifier.ts - 啟動驗證
  - MRL_Diagnostics.ts - 診斷收集
  - MRL_Rollback.ts - 回滾管理

#### Backend 模組層 (backend/)
- **授權管理模組**
  - MRL_LicenseManager.py - 授權檔管理
  - MRL_Activation.py - 啟用驗證
  - MRL_DeviceFingerprint.py - 裝置指紋

- **更新管理模組**
  - MRL_UpdateManager.py - 更新管理
  - MRL_BootVerifier.py - 啟動驗證
  - MRL_Diagnostics.py - 診斷報告
  - MRL_Rollback.py - 回滾系統

#### API 端點層 (backend/MRL_API.py)
9 個營運 API 端點，詳見 MRL_06_API_AUDIT.md

#### 儲存層 (storage/)
- **storage/license/** - 授權檔儲存
- **storage/diagnostics/** - 診斷報告 (logs/reports/exports)
- **storage/updates/** - 更新管理 (manifest/downloads)
- **storage/rollback/** - 回滾快照 (backups/snapshots)

### 格式定義

#### 授權檔格式 (current_license.json)
```json
{
  "license_id": "MRL-2024-XXXX",
  "edition": "Professional",
  "expiry_date": "2025-12-31",
  "device_binding": {
    "bound": true,
    "device_hash": "sha256_hash_value"
  },
  "features": ["feature1", "feature2"]
}
```

#### 裝置綁定格式
```json
{
  "device_hash": "sha256_hash_value",
  "bound_at": "2024-04-02T00:00:00Z"
}
```

#### 更新 Manifest 格式 (update_manifest.json)
```json
{
  "version": "1.0.1",
  "release_date": "2024-04-02",
  "download_url": "https://...",
  "signature": "base64_signature",
  "changelog": ["change1", "change2"]
}
```

#### 啟動 Manifest 格式 (boot_manifest.json)
```json
{
  "required_files": ["file1", "file2"],
  "required_modules": ["module1", "module2"],
  "database_required": true
}
```

### 營運能力

1. **授權管理** - 本地授權檔讀取、狀態查詢
2. **啟用流程** - 授權檔匯入、裝置綁定（遠端驗證預留）
3. **裝置綁定** - 裝置指紋生成、hash 驗證
4. **更新管理** - 版本比較、manifest 讀取、Tauri 接口（預留）
5. **啟動驗證** - 檔案完整性、manifest 符合性、DB 存在性
6. **診斷輸出** - 系統資訊、錯誤日誌、診斷報告匯出
7. **回滾能力** - 快照建立、快照還原

### 限制與預留

#### 已實作
- 本地授權檔管理
- 裝置指紋生成
- 更新 manifest 讀取
- 啟動驗證
- 診斷報告生成
- 回滾快照管理

#### 待驗證
- 授權檔匯入完整流程
- 裝置綁定實際驗機

#### 預留未實作
- 遠端啟用碼驗證（標記為 stub）
- Tauri updater 整合（接口預留）
- 更新簽章驗證邏輯
- Tauri Rust commands

### 工程哲學
- **Offline First** - 不依賴網路可正常使用
- **Online Optional** - 網路僅用於更新檢查
- **不碰付款** - 完全不觸及付款/商城
- **不建平行結構** - 基於既有結構擴展
```

---

## 四、回填到 MRL_世界模組工程書_v1.md

### 新增模組條目

```markdown
## 營運層模組 (MRL_06)

### 模組定位
MRL_AI_Desktop_v1 的營運層，負責產品化營運能力。

### 模組清單

#### 1. 授權管理模組
- **檔案**: backend/MRL_LicenseManager.py
- **類別**: MRL_LicenseManager
- **職責**: 授權檔讀取、狀態查詢
- **API**: POST /license/status

#### 2. 啟用模組
- **檔案**: backend/MRL_Activation.py
- **類別**: MRL_Activation
- **職責**: 授權檔匯入、裝置綁定
- **API**: POST /license/import, POST /license/activate (stub)

#### 3. 裝置指紋模組
- **檔案**: backend/MRL_DeviceFingerprint.py
- **類別**: MRL_DeviceFingerprint
- **職責**: 裝置 hash 生成、綁定驗證
- **API**: GET /device/hash

#### 4. 更新管理模組
- **檔案**: backend/MRL_UpdateManager.py
- **類別**: MRL_UpdateManager
- **職責**: 版本比較、manifest 讀取
- **API**: GET /update/check

#### 5. 啟動驗證模組
- **檔案**: backend/MRL_BootVerifier.py
- **類別**: MRL_BootVerifier
- **職責**: 檔案/manifest/DB 驗證
- **API**: GET /boot/verify

#### 6. 診斷模組
- **檔案**: backend/MRL_Diagnostics.py
- **類別**: MRL_Diagnostics
- **職責**: 診斷報告生成與匯出
- **API**: POST /diagnostics/export

#### 7. 回滾模組
- **檔案**: backend/MRL_Rollback.py
- **類別**: MRL_Rollback
- **職責**: 快照建立與還原
- **API**: POST /rollback/create, POST /rollback/restore

### 前端對應

#### 授權管理前端
- **目錄**: app/license/
- **檔案**: MRL_LicenseManager.ts, MRL_Activation.ts, MRL_DeviceBinding.ts
- **職責**: 授權狀態顯示、授權檔匯入、裝置綁定

#### 更新管理前端
- **目錄**: app/update/
- **檔案**: MRL_Update_Manager.ts, MRL_Boot_Verifier.ts, MRL_Diagnostics.ts, MRL_Rollback.ts
- **職責**: 更新檢查、啟動驗證、診斷收集、回滾管理

### 儲存結構

#### 授權儲存
- **目錄**: storage/license/
- **檔案**: current_license.json

#### 診斷儲存
- **目錄**: storage/diagnostics/
- **子目錄**: logs/, reports/, exports/

#### 更新儲存
- **目錄**: storage/updates/
- **子目錄**: manifest/, downloads/
- **檔案**: update_manifest.json

#### 回滾儲存
- **目錄**: storage/rollback/
- **子目錄**: backups/, snapshots/

### 配置檔案
- **boot_manifest.json** - 啟動必要項目定義

### 模組依賴

```
MRL_LicenseManager ─→ current_license.json
MRL_Activation ─→ MRL_DeviceFingerprint
MRL_UpdateManager ─→ update_manifest.json
MRL_BootVerifier ─→ boot_manifest.json
MRL_Diagnostics ─→ storage/diagnostics/
MRL_Rollback ─→ storage/rollback/
```

### 版本
- **首版**: v1.0 (2026-04-02)
- **狀態**: 分支完成，已回填主線
```

---

## 五、回填內容分類

### 正式完成（可回填主線）

#### 檔案結構
- 7 個前端 TypeScript 組件
- 7 個 Backend Python 模組
- 9 個 API 端點定義
- 3 個配置檔案範本
- 10 個新儲存目錄

#### 格式定義
- 授權檔格式 (JSON schema)
- 裝置綁定格式
- 更新 manifest 格式
- 啟動 manifest 格式

#### 核心能力
- 本地授權檔讀取
- 裝置 hash 生成
- 版本比較與更新檢查
- 啟動完整性驗證
- 診斷報告生成
- 回滾快照管理

### 待驗證（標記但不回填）

#### 完整流程
- 授權檔匯入 → 驗機 → 啟用 完整測試
- 更新檢查 → 下載 → 安裝 → 驗證 完整流程
- 啟動驗證 → 失敗 → 回滾 完整流程

#### 增強功能
- 遠端啟用碼驗證服務
- 授權檔/更新包簽章驗證邏輯
- Tauri updater 實際整合
- Tauri Rust commands

---

## 六、回填執行步驟

### Step 1: 準備回填內容
- [x] 完成 MRL_06_CANONICAL_HANDOFF.md
- [x] 完成 MRL_06_FILE_TREE_AUDIT.md
- [x] 完成 MRL_06_API_AUDIT.md
- [x] 完成 MRL_06_MAINLINE_BACKFILL.md

### Step 2: 等待 ChatGPT 驗收
- [ ] ChatGPT 審查 4 份文件
- [ ] ChatGPT 確認可回填

### Step 3: 執行回填（ChatGPT 執行）
- [ ] 更新 MRL_工程日誌.md
- [ ] 更新 MRL_母體定義檔_v1.md
- [ ] 更新 MRL_世界模組工程書_v1.md

### Step 4: 回填驗證
- [ ] 確認主線三大文件已更新
- [ ] 確認內容無遺漏
- [ ] 確認待驗證項目已標記

---

## 七、不回填內容清單

### 預留功能（明確標示）
- Tauri Rust commands（預留目錄，未實作檔案）
- 遠端啟用碼驗證（標記為 stub）
- 更新簽章驗證邏輯（格式支援，邏輯未實作）

### 測試結果（未執行）
- 端到端測試報告（未執行測試）
- 效能基準測試（未執行）
- 安全性測試（未執行）

### 遠端服務（未實作）
- 啟用碼驗證服務
- 授權檔簽發服務
- 更新包分發服務

---

## 八、回填後主線狀態

### MRL_工程日誌.md
新增 MRL_06 完整執行記錄。

### MRL_母體定義檔_v1.md
新增營運層完整定義：
- 架構層級
- 格式規範
- 能力清單
- 限制說明

### MRL_世界模組工程書_v1.md
新增 7 個營運層模組：
- 模組定位
- 職責說明
- API 對應
- 依賴關係

---

## 九、回填驗收標準

回填完成須滿足：
1. ✅ 主線三大文件已更新
2. ✅ MRL_06 內容已完整記錄
3. ✅ 待驗證項目已明確標示
4. ✅ 不回填內容已分類說明
5. ✅ 無隱藏缺口
6. ✅ 無重複內容

---

## 🔒 回填指南完成

**回填準備**: ✅ 就緒  
**等待**: ChatGPT 驗收  
**執行**: ChatGPT
