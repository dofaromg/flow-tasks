#!/bin/bash
# ============================================================================
#  MRL_BaseWorld_DB_v1_Backup.sh
#  origin_signature: MrLiouWord
#  歸屬: MRL母體工程架構中心
#  分支: MRL_Branch_06_BaseWorld_DB_Deploy_DL580
#  用途: PostgreSQL timestamped backup to /opt/mrl/baseworld/backups
#
#  使用方式:
#    手動: docker exec mrl-baseworld-canonical-db /usr/local/bin/backup.sh
#    排程: crontab -e → 0 3 * * * docker exec mrl-baseworld-canonical-db /usr/local/bin/backup.sh
# ============================================================================

set -e

DB_NAME="${POSTGRES_DB:-mrl_baseworld}"
DB_USER="${POSTGRES_USER:-mrl_admin}"
BACKUP_DIR="${MRL_BACKUP_DIR:-/backups}"
RETAIN_DAYS="${MRL_BACKUP_RETAIN_DAYS:-30}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/mrl_baseworld_${TIMESTAMP}.sql"

echo "============================================"
echo "  MRL BaseWorld DB Backup"
echo "  origin_signature: MrLiouWord"
echo "  Time: $(date -Iseconds)"
echo "============================================"

# 確保備份目錄存在
mkdir -p "${BACKUP_DIR}"

# 執行 pg_dump
echo "[1/4] Dumping database: ${DB_NAME} ..."
pg_dump -U "${DB_USER}" -d "${DB_NAME}" --format=plain --no-owner --no-privileges > "${BACKUP_FILE}"

# 壓縮
echo "[2/4] Compressing ..."
gzip "${BACKUP_FILE}"
BACKUP_FILE="${BACKUP_FILE}.gz"

# 驗證備份檔案
FILESIZE=$(stat -c%s "${BACKUP_FILE}" 2>/dev/null || stat -f%z "${BACKUP_FILE}" 2>/dev/null)
echo "[3/4] Backup created: ${BACKUP_FILE} (${FILESIZE} bytes)"

if [ "${FILESIZE}" -lt 100 ]; then
    echo "ERROR: Backup file too small, possible failure"
    exit 1
fi

# 清理舊備份
echo "[4/4] Cleaning backups older than ${RETAIN_DAYS} days ..."
find "${BACKUP_DIR}" -name "mrl_baseworld_*.sql.gz" -mtime "+${RETAIN_DAYS}" -delete 2>/dev/null || true

TOTAL=$(ls -1 "${BACKUP_DIR}"/mrl_baseworld_*.sql.gz 2>/dev/null | wc -l)
echo "============================================"
echo "  Backup complete"
echo "  File: ${BACKUP_FILE}"
echo "  Size: ${FILESIZE} bytes"
echo "  Total backups: ${TOTAL}"
echo "============================================"
