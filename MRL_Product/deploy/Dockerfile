# MRL_Product_v1 Dockerfile
# origin_signature: MrLiouWord
# target: DL580 G9 自有部署
# 版本: v1.1 — 含 entrypoint + 正確 volume 路徑

FROM node:20-slim

# ── 系統依賴（better-sqlite3 需要原生編譯）────────────────
RUN apt-get update && apt-get install -y \
    python3 \
    make \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ── 安裝 Node 依賴（先複製 package.json，利用 Docker cache）
COPY package.json ./
RUN npm install --omit=dev

# ── 複製專案原始碼 ────────────────────────────────────────
COPY backend/ ./backend/
COPY frontend/ ./frontend/
COPY storage/schema.sql ./storage/schema.sql

# ── 建立 runtime 目錄 ────────────────────────────────────
# storage: 將被 host volume 覆蓋（/opt/mrl_product_v1/storage）
# logs:    將被 host volume 覆蓋（/opt/mrl_product_v1/logs）
RUN mkdir -p /app/storage /app/logs

# ── 複製並設定 entrypoint ─────────────────────────────────
COPY deploy/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# ── 健康檢查 ──────────────────────────────────────────────
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
  CMD curl -f http://localhost:3000/health || exit 1

EXPOSE 3000

# ── 啟動（由 entrypoint 做 schema init 再啟動 app）────────
ENTRYPOINT ["/entrypoint.sh"]
