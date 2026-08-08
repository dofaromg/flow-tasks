#!/bin/bash
# scripts/backup.sh
# origin_signature: MrLiouWord
# 備份 MRL_Product_v1 核心資料
# 使用方式：bash /opt/mrl_product_v1/app/scripts/backup.sh

set -e

BASE="/opt/mrl_product_v1"
BACKUP_DIR="$BASE/backups"
TIMESTAMP=$(date +%F-%H%M%S)

echo "[MRL Backup] ── 開始備份 $TIMESTAMP ──────────────"

# ── 1. 建立備份目錄 ────────────────────────────────────────
mkdir -p "$BACKUP_DIR"

# ── 2. SQLite 備份 ────────────────────────────────────────
DB_SRC="$BASE/storage/db.sqlite"
DB_DST="$BACKUP_DIR/db-$TIMESTAMP.sqlite"

if [ -f "$DB_SRC" ]; then
  cp "$DB_SRC" "$DB_DST"
  echo "[MRL Backup] SQLite: $DB_DST ($(du -sh "$DB_DST" | cut -f1))"
else
  echo "[MRL Backup] WARNING: SQLite 不存在 $DB_SRC"
fi

# ── 3. .env 備份（加密，避免明文存在 backups）──────────────
ENV_SRC="$BASE/app/.env"
ENV_DST="$BACKUP_DIR/env-$TIMESTAMP.bak"

if [ -f "$ENV_SRC" ]; then
  # 簡單複製（注意：請確保 backups 目錄本身有適當的存取控制）
  cp "$ENV_SRC" "$ENV_DST"
  chmod 600 "$ENV_DST"
  echo "[MRL Backup] .env: $ENV_DST"
fi

# ── 4. nginx.conf 備份 ────────────────────────────────────
NGINX_SRC="$BASE/app/deploy/nginx.conf"
NGINX_DST="$BACKUP_DIR/nginx-$TIMESTAMP.conf"

if [ -f "$NGINX_SRC" ]; then
  cp "$NGINX_SRC" "$NGINX_DST"
  echo "[MRL Backup] nginx.conf: $NGINX_DST"
fi

# ── 5. 清理舊備份（保留最近 30 份 SQLite）────────────────
KEEP=30
OLD_COUNT=$(ls "$BACKUP_DIR"/db-*.sqlite 2>/dev/null | wc -l)
if [ "$OLD_COUNT" -gt "$KEEP" ]; then
  ls -t "$BACKUP_DIR"/db-*.sqlite | tail -n +$((KEEP+1)) | xargs rm -f
  echo "[MRL Backup] 清理舊 SQLite 備份，保留最新 $KEEP 份"
fi

# ── 6. 顯示目前備份清單 ────────────────────────────────────
echo ""
echo "[MRL Backup] 目前備份："
ls -lh "$BACKUP_DIR"/db-*.sqlite 2>/dev/null | tail -5
echo "[MRL Backup] ── 備份完成 ──────────────────────────────"
