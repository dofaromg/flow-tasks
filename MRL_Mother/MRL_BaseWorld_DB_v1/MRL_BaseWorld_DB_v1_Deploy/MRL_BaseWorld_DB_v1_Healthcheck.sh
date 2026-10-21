#!/bin/bash
# ============================================================================
#  MRL_BaseWorld_DB_v1_Healthcheck.sh
#  origin_signature: MrLiouWord
#  歸屬: MRL母體工程架構中心
#  分支: MRL_Branch_06_BaseWorld_DB_Deploy_DL580
#  用途: PostgreSQL 容器健康檢查
# ============================================================================

set -e

# 基本連線檢查
pg_isready -U "${POSTGRES_USER:-mrl_admin}" -d "${POSTGRES_DB:-mrl_baseworld}" -q || exit 1

# 資料庫可查詢檢查
psql -U "${POSTGRES_USER:-mrl_admin}" -d "${POSTGRES_DB:-mrl_baseworld}" -t -c "SELECT 1;" > /dev/null 2>&1 || exit 1

# 驗證 ROOT 存在且 origin_signature 正確
ROOT_SIG=$(psql -U "${POSTGRES_USER:-mrl_admin}" -d "${POSTGRES_DB:-mrl_baseworld}" -t -A -c \
    "SELECT origin_signature FROM mrl_origin WHERE origin_key = 'ROOT' LIMIT 1;" 2>/dev/null)

if [ "$ROOT_SIG" != "MrLiouWord" ]; then
    echo "HEALTHCHECK FAIL: ROOT origin_signature mismatch or missing"
    exit 1
fi

# 驗證 Closure Law 全部 enforced
UNENFORCED=$(psql -U "${POSTGRES_USER:-mrl_admin}" -d "${POSTGRES_DB:-mrl_baseworld}" -t -A -c \
    "SELECT count(*) FROM mrl_closure_law WHERE enforced = FALSE;" 2>/dev/null)

if [ "$UNENFORCED" != "0" ]; then
    echo "HEALTHCHECK FAIL: $UNENFORCED closure law(s) not enforced"
    exit 1
fi

exit 0
