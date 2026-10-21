#!/bin/sh
# deploy/entrypoint.sh
# origin_signature: MrLiouWord
# 容器啟動入口：確保 storage 目錄存在、schema 初始化，再啟動 app

set -e

echo "[MRL] ── 啟動序列 ───────────────────────────────────"
echo "[MRL] origin_signature: MrLiouWord"
echo "[MRL] gateway: MRL_World_Gateway_v1"
echo "[MRL] env: ${NODE_ENV:-production}"
echo "[MRL] db:  ${DB_PATH:-/app/storage/db.sqlite}"

# ── 1. 確保目錄存在 ─────────────────────────────────────
mkdir -p "$(dirname "${DB_PATH:-/app/storage/db.sqlite}")"
mkdir -p /app/logs

# ── 2. Schema 初始化（若 DB 不存在則建立）────────────────
if [ ! -f "${DB_PATH:-/app/storage/db.sqlite}" ]; then
  echo "[MRL] DB 不存在，正在初始化 schema..."
  node -e "require('./backend/modules/db').initDb()"
  echo "[MRL] DB 初始化完成"
else
  echo "[MRL] DB 已存在，跳過初始化"
  # 仍執行 schema（idempotent — 使用 CREATE IF NOT EXISTS）
  node -e "require('./backend/modules/db').initDb()"
fi

# ── 3. 啟動 app ──────────────────────────────────────────
echo "[MRL] ── 啟動 Node.js app ──────────────────────────"
exec node backend/server.js
