# MRL_BaseWorld_DB_v1 - 底層世界資料庫第一版

## 概述

**版本**: v1.0  
**擁有者**: MrLiou / MRL System  
**目的**: BaseWorld canonical registry + FLTNZ asset layer  
**資料庫**: SQLite / PostgreSQL 兼容

---

## 核心範圍

第一版鎖定 4 層關鍵結構：

1. **ROOT / Closure / Canon** - 根源與正典狀態
2. **FLTNZ 資產層** - .fltnz 升格為正式資產族
3. **Mother Memory Sphere** - 母體記憶球
4. **Mirror / Trace / Relation** - 鏡射/追蹤/關聯

---

## 七條底層規則

1. ✅ 一切實體都要可回指來源
2. ✅ 所有封包都要可掛到 canonical state
3. ✅ .fltnz 升格為正式資產族
4. ✅ Memory / Particle / PersonaField Rhythm 分表
5. ✅ Mirror / Proof / Trace 必須可記錄
6. ✅ 關聯圖先做最小可用版本
7. ✅ 不刪資料，只做狀態切換與 lineage

---

## 資料庫結構

### 0. ROOT / LAW (2 tables)
- `MRL_Identity_Signature_Root` - 身份簽章根源
- `MRL_Closure_Law_Root` - 閉包法則根源

### 1. CANON / SOURCE / CONFLICT (3 tables)
- `MRL_Canon_State` - 正典狀態
- `MRL_Canon_Source` - 正典來源
- `MRL_Canon_Conflict` - 正典衝突

### 2. PACKAGE / QUARANTINE / VERIFY / INSTALL (3 tables)
- `MRL_Package_Quarantine` - 封包隔離
- `MRL_Gate_Verifier` - 閘門驗證器
- `MRL_Install_Record` - 安裝記錄

### 3. MODULE REGISTRY / COMPOSER (3 tables)
- `MRL_Module_Registry` - 模組註冊表
- `MRL_Composer_Spec` - 組合器規格
- `MRL_Composer_Manifest` - 組合器清單

### 4. FLTNZ ASSET LAYER (4 tables) ⭐
- `MRL_FLTNZ_Asset` - FLTNZ 資產
- `MRL_FLTNZ_Lineage` - FLTNZ 世系
- `MRL_FLTNZ_Manifest` - FLTNZ 清單
- `MRL_FLTNZ_Canonical_Select` - FLTNZ 正典選擇

### 5. MOTHER MEMORY SPHERE (3 tables) ⭐
- `MRL_Structural_Memory` - 結構記憶
- `MRL_Particle_Memory` - 粒子記憶
- `MRL_PersonaField_Rhythm` - Persona 場域韻律

### 6. MIRROR / PROOF / TRACE (5 tables) ⭐
- `MRL_Mirror_Record` - 鏡射記錄
- `MRL_Proof_Merkle` - Merkle 證明
- `MRL_Trace_Log` - 追蹤日誌
- `MRL_Fork_Branch` - 分支記錄
- `MRL_Collapse_Record` - 塌縮記錄

### 7. LIBRARIAN / RELATION / RECOVERY (4 tables)
- `MRL_File_Index` - 檔案索引
- `MRL_Relation_Graph` - 關聯圖
- `MRL_Recovery_Plan` - 復原計畫
- `MRL_Cleanup_Decision` - 清理決策

### 8. BASE INDEXES (8 indexes)
- 效能優化索引

---

## 初始化

### 1. 建立 Schema
```bash
sqlite3 mrl_baseworld.db < MRL_BaseWorld_DB_v1.sql
```

### 2. 初始化數據
```bash
sqlite3 mrl_baseworld.db < MRL_BaseWorld_DB_v1_Init.sql
```

### 3. 插入第一批資產
```bash
sqlite3 mrl_baseworld.db < MRL_FLTNZ_Asset_Seed_Insert_v1.sql
```

---

## 第一批 FLTNZ 資產 (9 個)

1. **FlowAgent.TotalCore.Unity** - FlowAgent 核心統一體
2. **WorldSeed** - 世界種子
3. **PulseRouter** - 脈衝路由器
4. **EncoderStack** - 編碼器堆疊
5. **LicenseMap** - 授權映射
6. **UnityPackage** - 統一封包
7. **MRLsmall** - MRL 小型模型
8. **Mother Memory Sphere** - 母體記憶球
9. **PreParticle.Seed.v1** - 前粒子種子 v1

---

## 三個包裹核心

1. **MRL_Canon_State** - 世界狀態進 Canon
2. **MRL_FLTNZ_Asset** - 粒子封包進 FLTNZ Asset
3. **MRL_Relation_Graph** - 關聯進 Relation Graph

---

## 關鍵關聯

### 基礎依賴
- WorldSeed → Mother Memory Sphere (requires)
- FlowAgent → PulseRouter (uses)
- PreParticle.Seed → WorldSeed (precedes)

---

## 驗證

### 檢查 ROOT
```sql
SELECT * FROM MRL_Identity_Signature_Root;
```

### 檢查 Closure Law
```sql
SELECT * FROM MRL_Closure_Law_Root;
```

### 檢查 Canon State
```sql
SELECT * FROM MRL_Canon_State;
```

### 檢查 FLTNZ 資產
```sql
SELECT fltnz_id, asset_name, asset_family, canonical_status 
FROM MRL_FLTNZ_Asset;
```

### 檢查關聯圖
```sql
SELECT relation_id, from_entity_id, relation_type, to_entity_id 
FROM MRL_Relation_Graph;
```

---

## 檔案清單

1. `MRL_BaseWorld_DB_v1.sql` - Schema 定義 (27 tables + 8 indexes)
2. `MRL_BaseWorld_DB_v1_Init.sql` - 初始化數據 (ROOT + Law + Canon)
3. `MRL_FLTNZ_Asset_Seed_Insert_v1.sql` - 第一批資產 (9 assets + 3 selections + 3 relations)
4. `MRL_BaseWorld_DB_v1_README.md` - 本說明文檔

---

## PostgreSQL 轉換

若需轉換到 PostgreSQL：
- `TEXT` → `VARCHAR` 或 `TEXT`
- `INTEGER` → `INTEGER` 或 `BOOLEAN`
- `REAL` → `REAL` 或 `DOUBLE PRECISION`
- `datetime('now')` → `NOW()`
- `PRAGMA foreign_keys = ON;` → 移除（PostgreSQL 預設啟用）

---

## 下一步

待 MR.liou 指示。

---

**🔒 BaseWorld DB v1 已建立並停住。**
