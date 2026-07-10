# MRL_BaseWorld_DB_v1 部署指南

**origin_signature**: MrLiouWord
**版本**: v1.0
**分支**: MRL_Branch_06_BaseWorld_DB_Deploy_DL580
**角色**: Canonical Mother Database on DL580

---

## 重要聲明

**這是 MRL 系統的 canonical mother database，部署在 DL580 本機。**

- Cloudflare 目前不是主庫
- Cloudflare 不做 D1
- Cloudflare 不做 Workers 主寫入
- Cloudflare 未來只作 mirror / API edge / 外部入口

---

## 系統內容

| 項目 | 數量 |
|------|------|
| Tables | 27 |
| Indexes | 8 |
| FLTNZ Assets | 9 |
| Relations | 3 |
| Closure Laws | 3 (全部 enforced) |
| FX Registry | 17 |
| World Modules | 5 |
| Deploy Branches | 5 |

---

## 檔案清單

```
MRL_BaseWorld_DB_v1_Deploy/
├── MRL_BaseWorld_DB_v1_Dockerfile
├── docker-compose.mrl-baseworld.yml
├── .env.mrl-baseworld.example
├── MRL_BaseWorld_DB_v1_Healthcheck.sh
├── MRL_BaseWorld_DB_v1_Backup.sh
├── MRL_BaseWorld_DB_v1_Deploy_DL580.md  (本文件)
└── initdb/
    ├── 00_MRL_BaseWorld_DB_v1.sql        (27 tables + 8 indexes)
    ├── 01_MRL_BaseWorld_DB_v1_Init.sql    (ROOT + Closure Law + FX + 控制中心)
    └── 02_MRL_FLTNZ_Asset_Seed_Insert_v1.sql (9 assets + 3 relations)
```

---

## 啟動步驟

### 1. 準備目錄

```bash
sudo mkdir -p /opt/mrl/baseworld/postgres-data
sudo mkdir -p /opt/mrl/baseworld/initdb
sudo mkdir -p /opt/mrl/baseworld/backups
sudo mkdir -p /opt/mrl/baseworld/logs
sudo chown -R 999:999 /opt/mrl/baseworld/postgres-data
```

### 2. 複製檔案

```bash
# 解壓部署包
tar -xzf MRL_BaseWorld_DB_v1_Deploy_DL580.tar.gz
cd MRL_BaseWorld_DB_v1_Deploy

# 複製初始化 SQL 到 host volume
cp initdb/*.sql /opt/mrl/baseworld/initdb/

# 建立環境變數檔
cp .env.mrl-baseworld.example .env.mrl-baseworld
```

### 3. 修改密碼

```bash
vi .env.mrl-baseworld
# 將 MRL_DB_PASSWORD=CHANGE_ME_TO_STRONG_PASSWORD 改為實際密碼
```

### 4. 設定腳本權限

```bash
chmod +x MRL_BaseWorld_DB_v1_Healthcheck.sh
chmod +x MRL_BaseWorld_DB_v1_Backup.sh
```

### 5. 啟動

```bash
docker compose -f docker-compose.mrl-baseworld.yml up -d
```

### 6. 確認啟動

```bash
docker compose -f docker-compose.mrl-baseworld.yml ps
docker compose -f docker-compose.mrl-baseworld.yml logs -f
```

---

## 停止

```bash
docker compose -f docker-compose.mrl-baseworld.yml down
```

資料不會丟失（host volume 持久化在 `/opt/mrl/baseworld/postgres-data`）。

---

## 查看 Logs

```bash
# 即時 logs
docker compose -f docker-compose.mrl-baseworld.yml logs -f

# 最近 100 行
docker compose -f docker-compose.mrl-baseworld.yml logs --tail=100
```

---

## 進入 psql

```bash
docker exec -it mrl-baseworld-canonical-db psql -U mrl_admin -d mrl_baseworld
```

---

## 驗證清單

啟動後執行以下驗證：

### 驗證 27 tables

```sql
SELECT count(*) FROM information_schema.tables
WHERE table_schema = 'public' AND table_type = 'BASE TABLE';
-- 預期: 27
```

### 驗證 8 indexes

```sql
SELECT count(*) FROM pg_indexes
WHERE schemaname = 'public' AND indexname LIKE 'idx_%';
-- 預期: 8
```

### 驗證 9 個 FLTNZ assets

```sql
SELECT asset_key, asset_name, category FROM mrl_fltnz_asset ORDER BY created_at;
-- 預期: 9 行
```

### 驗證 3 個 relations

```sql
SELECT r.relation_type, a1.asset_name AS from_asset, a2.asset_name AS to_asset
FROM mrl_relation r
JOIN mrl_fltnz_asset a1 ON r.from_id = a1.id
JOIN mrl_fltnz_asset a2 ON r.to_id = a2.id;
-- 預期: 3 行
```

### 驗證 ROOT origin_signature

```sql
SELECT origin_key, origin_signature FROM mrl_origin WHERE origin_key = 'ROOT';
-- 預期: MrLiouWord
```

### 驗證 Closure Law 全部 enforced

```sql
SELECT law_name, enforced FROM mrl_closure_law;
-- 預期: 3 行，全部 TRUE
```

### 驗證 Healthcheck

```bash
docker exec mrl-baseworld-canonical-db /usr/local/bin/healthcheck.sh && echo "PASS" || echo "FAIL"
```

---

## 備份

### 手動備份

```bash
docker exec mrl-baseworld-canonical-db bash -c \
  'pg_dump -U mrl_admin -d mrl_baseworld | gzip > /backups/mrl_baseworld_$(date +%Y%m%d_%H%M%S).sql.gz'
```

### 排程備份（每天凌晨 3 點）

```bash
crontab -e
# 加入:
0 3 * * * docker exec mrl-baseworld-canonical-db bash -c 'pg_dump -U mrl_admin -d mrl_baseworld | gzip > /backups/mrl_baseworld_$(date +\%Y\%m\%d_\%H\%M\%S).sql.gz'
```

### 查看備份

```bash
ls -lh /opt/mrl/baseworld/backups/
```

---

## 未來接 Cloudflare 作 Mirror

當 DL580 canonical DB 穩定運行後，可按以下路徑接入 Cloudflare：

1. **Cloudflare Workers** 作為 API edge 代理，讀請求轉發到 DL580
2. **Cloudflare D1** 作為 read replica / cache layer（唯讀鏡像）
3. **寫入永遠回 DL580 canonical DB**，D1 只做同步鏡像
4. **Cloudflare R2** 可用於存放備份檔案的異地副本

架構方向：

```
外部請求 → Cloudflare Workers (edge)
                ↓ 讀
            Cloudflare D1 (read mirror)
                ↓ 寫
            DL580 canonical DB (PostgreSQL 16)
                ↓ 同步
            Cloudflare D1 (mirror sync)
```

**注意**：在 mirror 機制建立前，Cloudflare 不承擔任何主寫入角色。

---

## 故障排除

### 容器無法啟動

```bash
docker compose -f docker-compose.mrl-baseworld.yml logs
ls -la /opt/mrl/baseworld/
sudo chown -R 999:999 /opt/mrl/baseworld/postgres-data
```

### 資料庫連線失敗

```bash
docker exec mrl-baseworld-canonical-db pg_isready -U mrl_admin
netstat -tulpn | grep 5432
docker exec mrl-baseworld-canonical-db env | grep POSTGRES
```

### 初始化 SQL 未執行

PostgreSQL 只在資料目錄為空時執行 `/docker-entrypoint-initdb.d/` 內的 SQL。
如需重新初始化：

```bash
docker compose -f docker-compose.mrl-baseworld.yml down
sudo rm -rf /opt/mrl/baseworld/postgres-data/*
docker compose -f docker-compose.mrl-baseworld.yml up -d
```

---

**origin_signature**: MrLiouWord
**Canonical on DL580 / Mirror later on Cloudflare**
