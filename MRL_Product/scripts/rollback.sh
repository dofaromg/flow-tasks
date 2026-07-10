#!/usr/bin/env bash
# scripts/rollback.sh
# MRL_Product_v1 — 回滾腳本
# origin_signature: MrLiouWord
# 用途：快速回滾到上一個 image tag

set -euo pipefail

echo "======================================================="
echo " MRL_Product_v1 — Rollback"
echo " origin_signature: MrLiouWord"
echo "======================================================="
echo ""

APP_NAME="mrl-app"
IMAGE_NAME="mrl-product-v1"
BACKUP_DIR="/opt/mrl_product_v1/backups"

# ── 備份現有 DB ──────────────────────────────────────────────────
echo "[ 1/4 ] 備份目前 DB..."
DB_SRC="/opt/mrl_product_v1/storage/db.sqlite"
if [ -f "$DB_SRC" ]; then
  TS=$(date +%Y%m%d_%H%M%S)
  mkdir -p "$BACKUP_DIR"
  cp "$DB_SRC" "$BACKUP_DIR/db_before_rollback_$TS.sqlite"
  echo "       備份至: $BACKUP_DIR/db_before_rollback_$TS.sqlite"
else
  echo "       DB 不存在，略過備份"
fi

# ── 列出可用 image tags ─────────────────────────────────────────
echo ""
echo "[ 2/4 ] 可用 image tags："
docker images "$IMAGE_NAME" --format "{{.Tag}}\t{{.CreatedAt}}\t{{.ID}}" | head -10 || {
  echo "       無 $IMAGE_NAME image"
  exit 1
}

# ── 指定回滾目標 ────────────────────────────────────────────────
echo ""
TARGET_TAG="${1:-previous}"
echo "[ 3/4 ] 回滾目標 tag: $TARGET_TAG"
echo "       （若要指定 tag，執行: bash rollback.sh <tag>）"

# ── 停止 + 重起 ─────────────────────────────────────────────────
echo ""
echo "[ 4/4 ] 停止目前服務..."
cd /opt/mrl_product_v1/app/deploy 2>/dev/null || cd "$(dirname "$0")/../deploy" 2>/dev/null || {
  echo "       [WARN] 找不到 deploy 目錄，請手動 cd 到 deploy/ 執行"
  echo "              docker compose down && docker compose up -d"
  exit 1
}

docker compose down
docker compose up -d

echo ""
echo "[ OK ] 回滾完成，等待健康狀態..."
sleep 10
bash health-check.sh 2>/dev/null || bash ../scripts/health-check.sh || {
  echo "[FAIL] 回滾後 health-check 失敗，請查 docker compose logs -f app"
  exit 1
}

echo ""
echo "======================================================="
echo " 回滾完成 ✓"
echo "======================================================="
