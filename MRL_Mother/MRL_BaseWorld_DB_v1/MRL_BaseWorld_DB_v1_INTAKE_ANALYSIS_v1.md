# MRL_BaseWorld_DB_v1 — 吸收分析與沙盒驗證（當下狀態 2026-05-29，沙盒；非永久結論）

origin_signature: MrLiouWord
law: Additive-Only（不刪除、不覆蓋、給位置、待起動）

本檔記錄使用者上傳之 5 個 BaseWorld 檔的吸收、沙盒實跑驗證，以及一個**必須裁決的 schema 分歧**。

## 1. 吸收清單（additive，root 新目錄，零覆蓋）

| 上傳檔 | 吸收位置 |
|---|---|
| `MRL__Mrl_Baseworld_Db_V1.tar.gz` | `MRL_BaseWorld_DB_v1_Schema/`（4 檔：SQL×3 + README） |
| `MRL__Mrl_Baseworld_Db_V1_Deploy_Dl580.tar.gz` | `MRL_BaseWorld_DB_v1_Deploy/`（Dockerfile/compose/initdb×3/backup/healthcheck/.env.example/部署md） |
| `MRL_BaseWorld_DB_v1_Dockerfile` | `MRL_BaseWorld_DB_v1_Dockerfile`（standalone） |
| `MRL__Mrl_Baseworld_Db_V1_Consistency_Check.pdf` | `consistency_check/` |
| `MRL_Mainline_Batch015_*.docx` | `mainline_batch/` |

## 2. 已釐清事實（解掉先前的後端矛盾）

- **正式後端 = DL580 上的本地 PostgreSQL 16**（`Dockerfile: FROM postgres:16-bookworm`）。
- `.env.mrl-baseworld.example`：`MRL_DEPLOY_TARGET=DL580`、`MRL_ROLE=canonical_mother_db`、`MRL_CANONICAL_LOCATION=local`。
- **「Cloudflare 僅作未來鏡像，不作主庫」**（`MRL_CLOUDFLARE_ROLE=mirror_only`）。
- → 先前文件中 Cloudflare D1 / Supabase 的說法皆非主庫；**主庫是 DL580 本地 Postgres**。

## 3. 沙盒實跑驗證（真實，PostgreSQL 16.13）

以沙盒臨時 postgres cluster 套用 **deploy 包 initdb（00/01/02）**：

- initdb / createdb / 三支 SQL 套用：**全部成功，無錯誤**。
- 實際建表數：**27 BASE TABLE**（與 `PROD_SCHEMA.tables=27` 數量吻合）。
- → deploy 包 schema 在真 Postgres 上**可成功初始化（沙盒）**。

> 注意：這是沙盒對 deploy SQL 的可套用性驗證，**非 DL580 實機**、**非 live 連線**。實機驗收待 DL580 部署。

## 4. ⚠ 必須裁決的分歧：兩套都叫 MRL_BaseWorld_DB_v1 的 27 表 schema

沙盒套用後發現，**Schema 包(tar1) 與 Deploy 包(tar2) 是兩套不相交的 27 表**：

| | Schema 包（tar1）`MRL_BaseWorld_DB_v1.sql` | Deploy 包（tar2）`initdb/00_*.sql`（Dockerfile 實際部署） |
|---|---|---|
| 表數 | 27（+ 8 indexes） | 27（沙盒實建 27 表） |
| 命名 | PascalCase | 小寫 |
| 代表表 | `MRL_Canon_State` / `MRL_FLTNZ_Asset` / `MRL_Proof_Merkle` / `MRL_Trace_Log` / `MRL_Mirror_Record` / `MRL_Module_Registry` / `MRL_Identity_Signature_Root` … | `mrl_origin` / `mrl_state` / `mrl_world_module` / `mrl_passport_system` / `mrl_jump_point` / `mrl_dimension_sync` / `mrl_signature` … |

**證據指向（彼此衝突）：**

- 指向 **Schema 包(tar1)** 為 canonical：
  - `MRL_BaseWorld_DB_v1_README.md`（分層 ROOT/Canon/FLTNZ/Memory/Mirror）
  - `Consistency_Check.pdf`（Branch B Auditor，2026-04-02）全程引用 PascalCase 表名
  - 本 repo adapter `MRL_BaseWorld_DB_Adapter.py` 的 7 掛接點（Canon/Registry/FLTNZ_Asset/Memory_Sphere/Proof/Trace/Mirror）
- 指向 **Deploy 包(tar2)** 為 canonical：
  - `MRL_Mainline_Batch015` docx 第 24 章「FlowPassport 七大不變量」明確映射到 `mrl_signature/mrl_persona/mrl_memory/mrl_particle/mrl_jump_point/mrl_world_module/mrl_passport_*`，並稱「完整映射到 MRL_BaseWorld_DB_v1 核心表」
  - `Dockerfile` 實際 COPY 的 initdb 就是這套

**影響**：若以 Dockerfile 現狀部署到 DL580，建出的是小寫 schema；而 repo adapter 的掛接點（Canon/Proof/Trace/Mirror/Registry）在該庫中**無對應表** → adapter 接線會缺表。

## 5. 不可誤標（當下狀態）

- ✅ 後端＝DL580 本地 Postgres（已釐清）
- ✅ deploy 包 schema 沙盒可初始化、實建 27 表（沙盒）
- ⏳ 真實 DL580 實機部署 / live 連線：**待實機**
- ⛔ **schema canonical 歸屬未定**：兩套 27 表分歧，需擁有者裁決；在裁決前**不得宣稱 BaseWorld 已對齊／已上線**，亦不擅自改寫任一方。
