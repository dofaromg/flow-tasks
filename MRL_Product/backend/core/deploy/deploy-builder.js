'use strict';
// backend/core/deploy/deploy-builder.js
// MRL Deploy Pack Builder
// origin_signature: MrLiouWord
//
// 讀取 scaffold manifest → 決定哪些 stub 要升級為 runnable → 生成 deploy plan
// 輸入：scaffold manifest + pack context
// 輸出：{ manifest, files: [{ path, content, source }] }
//   source = 'scaffold'（直接複製）| 'runnable'（升級版）| 'new'（新增）

const { uuid } = require('../../utils/ids');
const { now }  = require('../../utils/time');
const fs       = require('fs');
const path     = require('path');
const { readManifest, listScaffoldFiles } = require('../scaffolds/scaffold-writer');

const SCAFFOLDS_DIR  = path.join(__dirname, '../../../storage/scaffolds');

/**
 * 從 scaffold 生成 deploy plan
 */
function buildDeployPlan(scaffoldManifest) {
  const packId     = scaffoldManifest.pack_id;
  const scaffoldId = scaffoldManifest.scaffold_id;
  const title      = scaffoldManifest.title || 'MRL Product';
  const _rawSlug   = title.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '').slice(0, 30);
  // fallback：若 title 全是 CJK，用 packId 最後一段英文
  const _packSlug  = packId.replace(/^mrl[_-]pack[_-]?/, '').replace(/[^a-z0-9]/g, '-').replace(/^-+|-+$/g, '').slice(0, 20);
  const slug       = _rawSlug.length >= 2 ? _rawSlug : (_packSlug.length >= 2 ? _packSlug : 'mrl-product');
  const scaffoldDir = path.join(SCAFFOLDS_DIR, packId);

  const deployId = 'mrl_deploy_' + uuid().replace(/-/g, '').slice(0, 12);

  const ctx = {
    packId, scaffoldId, deployId, title, slug,
    mode:     scaffoldManifest.mode || 'website',
    pages:    scaffoldManifest.pages || [],
    generatedAt: now(),
    templateId:  scaffoldManifest.template_id,
    targetStack: scaffoldManifest.target_stack || 'node_sqlite_docker_nginx',
  };

  // ── Deploy Manifest ────────────────────────────────────────────
  const manifest = {
    deploy_pack_id:      deployId,
    scaffold_id:         scaffoldId,
    pack_id:             packId,
    category:            scaffoldManifest.category,
    template_id:         scaffoldManifest.template_id,
    mode:                scaffoldManifest.mode,
    title,
    pages:               scaffoldManifest.pages || [],
    target_stack:        ctx.targetStack,
    source_pack_path:    scaffoldManifest.source_pack_path,
    source_scaffold_path: `storage/scaffolds/${packId}`,
    generated_at:        ctx.generatedAt,
    origin:              'MrLiouWord',
  };

  // ── 從 scaffold 複製的檔案（直接讀 scaffold 目錄）──────────────
  const scaffoldFiles = listScaffoldFiles(packId) || [];
  const copyFiles = scaffoldFiles
    .filter(f => !_isUpgradeable(f))
    .map(f => ({
      path:    f,
      content: _readScaffoldFile(scaffoldDir, f),
      source:  'scaffold',
    }))
    .filter(f => f.content !== null);

  // ── 升級為 runnable 的檔案 ─────────────────────────────────────
  const runnableFiles = _buildRunnableFiles(ctx, scaffoldManifest);

  // ── 新增的檔案（scaffold 沒有的）─────────────────────────────
  const newFiles = _buildNewFiles(ctx);

  const files = [...copyFiles, ...runnableFiles, ...newFiles];

  return { manifest, files };
}

// ── 判斷是否需要升級（而非直接複製）─────────────────────────────
function _isUpgradeable(relPath) {
  const upgradeable = [
    'backend/server.js',
    'backend/config.js',
    'backend/routes/api.js',
    'backend/routes/payment.js',
    'backend/routes/webhook.js',
    'deploy/Dockerfile',
    'deploy/docker-compose.yml',
    'deploy/nginx.conf',
    '.env.example',
    'package.json',
    'storage/schema.sql',
    'README.md',
  ];
  return upgradeable.includes(relPath);
}

// ── 讀取 scaffold 檔案內容 ─────────────────────────────────────
function _readScaffoldFile(scaffoldDir, relPath) {
  const abs = path.join(scaffoldDir, relPath);
  if (!fs.existsSync(abs)) return null;
  try { return fs.readFileSync(abs, 'utf8'); } catch { return null; }
}

// ── 升級為 runnable 版本 ───────────────────────────────────────
function _buildRunnableFiles(ctx, manifest) {
  const { slug, deployId, title, pages } = ctx;
  return [
    { path: 'package.json',           content: _runnablePackageJson(ctx),   source: 'runnable' },
    { path: 'backend/config.js',      content: _runnableConfig(ctx),        source: 'runnable' },
    { path: 'backend/server.js',      content: _runnableServer(ctx),        source: 'runnable' },
    { path: 'backend/routes/api.js',  content: _runnableRouteApi(ctx),      source: 'runnable' },
    { path: 'backend/routes/payment.js', content: _runnablePayment(ctx),    source: 'runnable' },
    { path: 'backend/routes/webhook.js', content: _runnableWebhook(ctx),    source: 'runnable' },
    { path: 'deploy/Dockerfile',      content: _runnableDockerfile(ctx),    source: 'runnable' },
    { path: 'deploy/docker-compose.yml', content: _runnableCompose(ctx),    source: 'runnable' },
    { path: 'deploy/nginx.conf',      content: _runnableNginx(ctx),         source: 'runnable' },
    { path: '.env.example',           content: _runnableEnv(ctx),           source: 'runnable' },
    { path: 'storage/schema.sql',     content: _runnableSchema(ctx),        source: 'runnable' },
    { path: 'README.md',              content: _runnableReadme(ctx, manifest), source: 'runnable' },
  ];
}

// ── 新增的檔案（scaffold 沒有）────────────────────────────────
function _buildNewFiles(ctx) {
  return [
    { path: 'deploy/health-check.sh',        content: _healthCheckSh(ctx),   source: 'new' },
    { path: 'deploy/entrypoint.sh',          content: _entrypointSh(ctx),    source: 'new' },
    { path: 'deploy/setup.sh',               content: _setupSh(ctx),         source: 'new' },
    { path: 'deploy/pre-deploy-check.sh',    content: _preDeployCheck(ctx),  source: 'new' },
    { path: 'backend/routes/health.js',      content: _healthRoute(ctx),      source: 'new' },
    { path: 'backend/modules/db-init.js',    content: _dbInitModule(ctx),     source: 'new' },
    { path: 'docs/deploy-pack-notes.md',     content: _deployNotes(ctx),      source: 'new' },
  ];
}

// ═══════════════════════════════════════════════════════════════
// Runnable File Templates
// ═══════════════════════════════════════════════════════════════

function _runnablePackageJson({ slug, title, deployId }) {
  return JSON.stringify({
    name:        slug || 'mrl-product',
    version:     '1.0.0',
    description: `${title} — MRL Deploy Pack`,
    main:        'backend/server.js',
    scripts: {
      start:   'NODE_ENV=production node backend/server.js',
      dev:     'NODE_ENV=development node backend/server.js',
    },
    dependencies: {
      '@anthropic-ai/sdk': '^0.39.0',
      'better-sqlite3':    '^9.4.0',
      dotenv:              '^16.4.0',
      express:             '^4.18.3',
      jsonwebtoken:        '^9.0.2',
      stripe:              '^14.20.0',
      uuid:                '^9.0.0',
    },
    engines: { node: '>=20.0.0' },
    _deploy_pack_id: deployId,
    _origin:         'MrLiouWord',
  }, null, 2);
}

function _runnableConfig({ deployId }) {
  return `'use strict';
// config.js — MRL Deploy Pack
// deploy_pack_id: ${deployId}
// origin_signature: MrLiouWord
require('dotenv').config();

module.exports = {
  port:                parseInt(process.env.PORT || '3000', 10),
  nodeEnv:             process.env.NODE_ENV || 'development',
  baseUrl:             process.env.BASE_URL || 'http://localhost:3000',
  dbPath:              process.env.SQLITE_PATH || './storage/db.sqlite',
  jwtSecret:           process.env.JWT_SECRET || 'dev-secret-change-me',
  anthropicApiKey:     process.env.ANTHROPIC_API_KEY || '',
  anthropicModel:      process.env.ANTHROPIC_MODEL || 'claude-haiku-4-5-20251001',
  stripeSecretKey:     process.env.STRIPE_SECRET_KEY || '',
  stripeWebhookSecret: process.env.STRIPE_WEBHOOK_SECRET || '',
  stripePriceOnce:     process.env.STRIPE_PRICE_ONCE || '',
  stripePriceSub:      process.env.STRIPE_PRICE_SUB || '',
  adminKey:            process.env.ADMIN_KEY || 'dev-admin',
  logLevel:            process.env.LOG_LEVEL || 'info',
  originSignature:     'MrLiouWord',
};
`;
}

function _runnableServer({ slug, title, deployId }) {
  return `'use strict';
// backend/server.js — MRL Deploy Pack (Runnable)
// deploy_pack_id: ${deployId}
// origin_signature: MrLiouWord

require('dotenv').config();
const express = require('express');
const path    = require('path');
const config  = require('./config');
const { initDb } = require('./modules/db-init');
const app     = express();
const PORT    = config.port;

// ── Middleware ─────────────────────────────────────────────────
app.use(express.json({ limit: '512kb' }));
app.use(express.urlencoded({ extended: false }));

// ── Static assets ──────────────────────────────────────────────
app.use('/assets', express.static(path.join(__dirname, '../frontend/assets')));

// ── Routes ─────────────────────────────────────────────────────
app.use('/',        require('./routes/health'));   // /health
app.use('/api',     require('./routes/api'));
app.use('/payment', require('./routes/payment'));
app.use('/webhook', require('./routes/webhook'));

// ── Frontend pages ─────────────────────────────────────────────
const frontendDir = path.join(__dirname, '../frontend');
['/', '/index', '/app', '/pricing', '/product', '/success', '/cancel'].forEach(p => {
  const file = p === '/' ? 'index.html' : p.slice(1) + '.html';
  app.get(p, (_req, res) => res.sendFile(file, { root: frontendDir }));
});

// ── 404 fallback ────────────────────────────────────────────────
app.use((req, res) => res.status(404).json({ error: 'Not found', path: req.path }));

// ── Error handler ───────────────────────────────────────────────
app.use((err, _req, res, _next) => {
  console.error('[ERROR]', err.message);
  res.status(500).json({ error: 'Internal server error' });
});

// ── Init DB & Start ─────────────────────────────────────────────
initDb()
  .then(() => {
    app.listen(PORT, () => {
      console.log(\`[${slug}] running on :\${PORT} (env=\${config.nodeEnv})\`);
      console.log(\`[${slug}] origin_signature: MrLiouWord\`);
    });
  })
  .catch(err => {
    console.error('[FATAL] DB init failed:', err.message);
    process.exit(1);
  });

module.exports = app; // for testing
`;
}

function _runnableRouteApi({ deployId }) {
  return `'use strict';
// routes/api.js — MRL Deploy Pack (Runnable stub)
// deploy_pack_id: ${deployId}
// origin_signature: MrLiouWord
// TODO: 接上真正的 Core_Generator

const express = require('express');
const router  = express.Router();

router.post('/session', (_req, res) => {
  const { v4: uuidv4 } = require('uuid');
  const jwt = require('jsonwebtoken');
  const config = require('../config');
  const sessionId = uuidv4();
  const token = jwt.sign({ sessionId }, config.jwtSecret, { expiresIn: '7d' });
  res.json({ token, sessionId });
});

router.post('/analyze', async (req, res) => {
  // TODO: 接上 Core_Generator.analyze()
  res.json({
    analysis_id: 'deploy-stub-' + Date.now(),
    is_partial: true,
    requires_payment: true,
    result: {
      summary: '(Deploy Pack stub — 請接上 Core_Generator)',
      breakdown: ['TODO: 補充真正的分析邏輯'],
      directions: ['TODO: 接上 ai.js'],
    },
    template_id: null,
  });
});

router.get('/result/:id', (_req, res) => {
  res.status(501).json({ error: 'Not implemented yet — see docs/deploy-pack-notes.md' });
});

module.exports = router;
`;
}

function _runnablePayment({ deployId }) {
  return `'use strict';
// routes/payment.js — MRL Deploy Pack (Runnable stub)
// deploy_pack_id: ${deployId}
// origin_signature: MrLiouWord
// TODO: 填入真實 Stripe 邏輯

const express = require('express');
const router  = express.Router();

router.post('/once',         (_req, res) => res.status(501).json({ error: 'Stripe not configured yet' }));
router.post('/subscription', (_req, res) => res.status(501).json({ error: 'Stripe not configured yet' }));

module.exports = router;
`;
}

function _runnableWebhook({ deployId }) {
  return `'use strict';
// routes/webhook.js — MRL Deploy Pack (Runnable stub)
// deploy_pack_id: ${deployId}
// origin_signature: MrLiouWord
// TODO: 填入 Stripe webhook 驗證 + confirmation 觸發

const express = require('express');
const router  = express.Router();

router.post('/stripe', express.raw({ type: 'application/json' }), (req, res) => {
  console.log('[webhook] stripe received (stub)');
  res.json({ received: true });
});

module.exports = router;
`;
}

function _runnableDockerfile({ slug, deployId }) {
  return `# Dockerfile — MRL Deploy Pack (Runnable)
# deploy_pack_id: ${deployId}
# origin_signature: MrLiouWord
# target: DL580 G9

FROM node:20-slim

RUN apt-get update && \\
    apt-get install -y python3 make g++ curl && \\
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY package.json ./
RUN npm install --omit=dev

COPY backend/ ./backend/
COPY frontend/ ./frontend/
COPY storage/schema.sql ./storage/schema.sql
COPY deploy/entrypoint.sh ./entrypoint.sh
RUN chmod +x ./entrypoint.sh

RUN mkdir -p /app/storage /app/logs

HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \\
  CMD curl -f http://localhost:3000/health || exit 1

EXPOSE 3000
ENTRYPOINT ["/app/entrypoint.sh"]
`;
}

function _runnableCompose({ slug, deployId }) {
  const svcName = slug.replace(/-/g, '_');
  return `# docker-compose.yml — MRL Deploy Pack (Runnable)
# deploy_pack_id: ${deployId}
# origin_signature: MrLiouWord

services:
  app:
    build:
      context: ..
      dockerfile: deploy/Dockerfile
    container_name: ${slug}-app
    restart: unless-stopped
    env_file: ../.env
    environment:
      - SQLITE_PATH=/app/storage/db.sqlite
    volumes:
      - /opt/${slug}/storage:/app/storage
      - /opt/${slug}/logs:/app/logs
    networks: [app-net]
    expose: ["3000"]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 20s

  nginx:
    image: nginx:1.25-alpine
    container_name: ${slug}-nginx
    restart: unless-stopped
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro
      - /opt/${slug}/logs/nginx:/var/log/nginx
    depends_on:
      app:
        condition: service_healthy
    networks: [app-net]

networks:
  app-net:
    driver: bridge
`;
}

function _runnableNginx({ slug, deployId }) {
  const upstream = slug.replace(/-/g, '_') + '_backend';
  return `# nginx.conf — MRL Deploy Pack (Runnable)
# deploy_pack_id: ${deployId}
# origin_signature: MrLiouWord

upstream ${upstream} {
  server app:3000;
  keepalive 32;
}

server {
  listen 80;
  server_name _;

  proxy_http_version 1.1;
  proxy_set_header   Host              $host;
  proxy_set_header   X-Real-IP         $remote_addr;
  proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
  proxy_set_header   X-Forwarded-Proto $scheme;
  proxy_set_header   Connection        "";

  location /webhook/ {
    proxy_pass http://${upstream};
    proxy_read_timeout 30s;
  }
  location /api/ {
    proxy_pass http://${upstream};
    proxy_read_timeout 60s;
  }
  location /payment/ {
    proxy_pass http://${upstream};
  }
  location /assets/ {
    proxy_pass  http://${upstream};
    expires     1h;
    add_header  Cache-Control "public";
  }
  location /health {
    proxy_pass  http://${upstream};
    access_log  off;
  }
  location / {
    proxy_pass         http://${upstream};
    proxy_read_timeout 120s;
  }

  client_max_body_size 1m;
  gzip on;
  gzip_types text/plain text/css application/json application/javascript;
}
`;
}

function _runnableEnv({ deployId, slug }) {
  return `# .env — MRL Deploy Pack
# deploy_pack_id: ${deployId}
# 複製本檔為 .env 並填入真實值
# origin_signature: MrLiouWord

PORT=3000
NODE_ENV=production
BASE_URL=https://your-domain.com

JWT_SECRET=REPLACE_WITH_STRONG_RANDOM_SECRET

SQLITE_PATH=/app/storage/db.sqlite

ANTHROPIC_API_KEY=sk-ant-REPLACE
ANTHROPIC_MODEL=claude-haiku-4-5-20251001

STRIPE_SECRET_KEY=sk_live_REPLACE
STRIPE_WEBHOOK_SECRET=whsec_REPLACE
STRIPE_PRICE_ONCE=price_REPLACE
STRIPE_PRICE_SUB=price_REPLACE

ADMIN_KEY=REPLACE_WITH_ADMIN_KEY
LOG_LEVEL=info
`;
}

function _runnableSchema({ deployId }) {
  return `-- schema.sql — MRL Deploy Pack (Runnable)
-- deploy_pack_id: ${deployId}
-- origin_signature: MrLiouWord

PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS sessions (
  id         TEXT PRIMARY KEY,
  token_hash TEXT,
  user_id    TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS analyses (
  id              TEXT PRIMARY KEY,
  session_id      TEXT NOT NULL,
  problem_text    TEXT NOT NULL,
  category        TEXT,
  partial_result  TEXT,
  full_result     TEXT,
  status          TEXT NOT NULL DEFAULT 'pending',
  created_at      TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS orders (
  id               TEXT PRIMARY KEY,
  analysis_id      TEXT,
  session_id       TEXT,
  stripe_session_id TEXT,
  amount_cents     INTEGER,
  currency         TEXT DEFAULT 'TWD',
  plan_type        TEXT,
  status           TEXT NOT NULL DEFAULT 'pending',
  created_at       TEXT NOT NULL DEFAULT (datetime('now')),
  FOREIGN KEY (analysis_id) REFERENCES analyses(id)
);

CREATE TABLE IF NOT EXISTS ledger (
  id            TEXT PRIMARY KEY,
  event_type    TEXT NOT NULL,
  order_id      TEXT,
  analysis_id   TEXT,
  amount_cents  INTEGER,
  meta_json     TEXT,
  origin_sig    TEXT NOT NULL DEFAULT 'MrLiouWord',
  created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_analyses_session ON analyses(session_id);
CREATE INDEX IF NOT EXISTS idx_orders_analysis  ON orders(analysis_id);
CREATE INDEX IF NOT EXISTS idx_ledger_order     ON ledger(order_id);
`;
}

function _runnableReadme({ title, slug, deployId }) {
  return `# ${title}
> MRL Deploy Pack — origin_signature: MrLiouWord
> deploy_pack_id: ${deployId}

## 快速啟動

### 本地開發
\`\`\`bash
cp .env.example .env   # 填入 API keys
npm install
npm run dev            # http://localhost:3000
\`\`\`

### Docker 部署（DL580）
\`\`\`bash
# 準備目錄
sudo mkdir -p /opt/${slug}/{storage,logs/nginx}

# 設定環境變數
cp .env.example .env
nano .env  # 填入真實金鑰

# 啟動
cd deploy/
docker compose up -d --build

# 健康確認
bash health-check.sh
\`\`\`

## 健康檢查

\`\`\`bash
bash deploy/health-check.sh
# ✓ health: ok | status 200
\`\`\`

## 需要人工補完的地方

- [ ] \`.env\` 填入真實 \`ANTHROPIC_API_KEY\`、\`STRIPE_*\`、\`JWT_SECRET\`
- [ ] \`backend/routes/api.js\` 接上 Core_Generator
- [ ] \`backend/routes/payment.js\` 接上 Stripe checkout
- [ ] \`backend/routes/webhook.js\` 接上 Stripe webhook + confirmation
- [ ] 前端頁面補充實際文案與樣式

## 相關文件

- \`docs/deploy-pack-notes.md\` — 詳細架構說明
- 參考 MRL_Product_v1（完整成熟版本）

---
*origin_signature: MrLiouWord*
`;
}

// ── New Files ──────────────────────────────────────────────────────

function _healthCheckSh({ slug, deployId }) {
  return `#!/usr/bin/env bash
# health-check.sh — MRL Deploy Pack
# deploy_pack_id: ${deployId}
# origin_signature: MrLiouWord
set -euo pipefail

HOST=\${1:-localhost}
PORT=\${2:-3000}
URL="http://\${HOST}:\${PORT}/health"

echo "[health-check] Checking \${URL} ..."

HTTP_STATUS=\$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "\${URL}" 2>/dev/null || echo "000")

if [ "\${HTTP_STATUS}" = "200" ]; then
  BODY=\$(curl -s --max-time 10 "\${URL}" 2>/dev/null || echo '{}')
  echo "✓ health: ok | status \${HTTP_STATUS}"
  echo "  response: \${BODY}"
  exit 0
else
  echo "✗ health: FAILED | status \${HTTP_STATUS}"
  echo "  url: \${URL}"
  exit 1
fi
`;
}

function _healthRoute({ deployId }) {
  return `'use strict';
// routes/health.js — MRL Deploy Pack
// deploy_pack_id: ${deployId}
// origin_signature: MrLiouWord

const express = require('express');
const router  = express.Router();

router.get('/health', (_req, res) => {
  const config = require('../config');
  res.json({
    status:           'ok',
    service:          config.nodeEnv === 'production' ? 'mrl-product' : 'mrl-product-dev',
    origin_signature: 'MrLiouWord',
    deploy_pack_id:   '${deployId}',
    timestamp:        new Date().toISOString(),
  });
});

module.exports = router;
`;
}

function _dbInitModule({ deployId }) {
  return `'use strict';
// modules/db-init.js — MRL Deploy Pack
// deploy_pack_id: ${deployId}
// origin_signature: MrLiouWord
//
// DB 初始化：若 SQLite 不存在則建立 + 跑 schema.sql

const Database = require('better-sqlite3');
const fs       = require('fs');
const path     = require('path');
const config   = require('../config');

let _db = null;

async function initDb() {
  const dbPath    = path.resolve(config.dbPath);
  const schemaPath = path.join(__dirname, '../../storage/schema.sql');
  const dbDir     = path.dirname(dbPath);

  // 確保目錄存在
  if (!fs.existsSync(dbDir)) {
    fs.mkdirSync(dbDir, { recursive: true });
  }

  const isNew = !fs.existsSync(dbPath);
  _db = new Database(dbPath);

  // WAL + FK
  _db.exec("PRAGMA journal_mode=WAL");
  _db.exec("PRAGMA foreign_keys=ON");

  // 初始化 schema
  if (isNew || _needsInit(_db)) {
    const schema = fs.readFileSync(schemaPath, 'utf8');
    _db.exec(schema);
    console.log('[db-init] schema applied:', dbPath);
  }

  console.log('[db-init] ready:', dbPath, isNew ? '(new)' : '(existing)');
  return _db;
}

function _needsInit(db) {
  try {
    db.prepare("SELECT 1 FROM analyses LIMIT 1").get();
    return false;
  } catch {
    return true;
  }
}

function getDb() {
  if (!_db) throw new Error('DB not initialized. Call initDb() first.');
  return _db;
}

module.exports = { initDb, getDb };
`;
}

function _deployNotes({ title, deployId, packId, slug }) {
  return `# Deploy Pack Notes — ${title}
> deploy_pack_id: ${deployId}
> pack_id: ${packId}
> origin_signature: MrLiouWord

## 架構說明

\`\`\`
frontend/           ← HTML 頁面（stub，需補充文案）
backend/
  server.js         ← Express app，啟動 + DB init（runnable）
  config.js         ← 環境變數讀取（runnable）
  routes/
    health.js       ← /health endpoint（runnable）
    api.js          ← /api/session + /api/analyze（stub，需接 Core_Generator）
    payment.js      ← Stripe checkout（stub）
    webhook.js      ← Stripe webhook（stub）
  modules/
    db-init.js      ← SQLite 初始化（runnable）
storage/
  schema.sql        ← 最小 schema（runnable）
deploy/
  Dockerfile        ← Node 20 容器（runnable）
  docker-compose.yml ← app + nginx（runnable）
  nginx.conf        ← 反向代理（runnable）
  health-check.sh   ← 健康確認腳本（runnable）
.env.example        ← 環境變數範本
\`\`\`

## 啟動後可用的 endpoint

| 路徑 | 狀態 | 說明 |
|------|------|------|
| GET /health | ✅ runnable | 健康檢查 |
| POST /api/session | ✅ runnable | 取 JWT token |
| POST /api/analyze | ⚠️ stub | 需接 Core_Generator |
| POST /payment/once | ⚠️ stub | 需配 Stripe |
| POST /webhook/stripe | ⚠️ stub | 需配 Stripe webhook |

## 下一步：接上完整商業邏輯

1. 複製 MRL_Product_v1/backend/modules/ai.js → backend/modules/ai.js
2. 複製 MRL_Product_v1/backend/core/generator/ → backend/core/generator/
3. 更新 backend/routes/api.js 呼叫 Core_Generator
4. 複製 MRL_Product_v1/backend/modules/order.js、ledger.js、confirmation.js
5. 更新 backend/routes/payment.js 與 webhook.js
`;
}


function _entrypointSh({ slug, deployId }) {
  return `#!/bin/sh
# deploy/entrypoint.sh — MRL Deploy Pack
# deploy_pack_id: ${deployId}
# origin_signature: MrLiouWord
set -e

echo "[${slug}] ── 啟動序列 ────────────────────────────────"
echo "[${slug}] origin_signature: MrLiouWord"
echo "[${slug}] env: \${NODE_ENV:-production}"
echo "[${slug}] db:  \${SQLITE_PATH:-/app/storage/db.sqlite}"

mkdir -p "$(dirname "\${SQLITE_PATH:-/app/storage/db.sqlite}")"
mkdir -p /app/logs

echo "[${slug}] ── 啟動 Node.js app ─────────────────────────"
exec node backend/server.js
`;
}

function _setupSh({ slug, deployId }) {
  return `#!/usr/bin/env bash
# deploy/setup.sh — DL580 一鍵部署腳本
# deploy_pack_id: ${deployId}
# origin_signature: MrLiouWord
set -euo pipefail

SLUG="${slug}"
BASE_DIR="/opt/\${SLUG}"

echo "===================================================="
echo " MRL Deploy Pack — Setup Script"
echo " slug: \${SLUG}"
echo " target: DL580"
echo " origin_signature: MrLiouWord"
echo "===================================================="
echo ""

# ── 1. 確認 .env 存在 ──────────────────────────────────────────
if [ ! -f "../.env" ]; then
  echo "[WARN] .env 不存在，正在從 .env.example 複製..."
  cp "../.env.example" "../.env"
  echo "[WARN] 請先編輯 ../.env 填入真實金鑰，然後重新執行此腳本"
  echo "       需要填入：ANTHROPIC_API_KEY / STRIPE_* / JWT_SECRET / BASE_URL"
  exit 1
fi
echo "[ OK ] .env 存在"

# ── 2. 建立 host 目錄 ───────────────────────────────────────────
echo "[    ] 建立 host 目錄..."
sudo mkdir -p "\${BASE_DIR}/storage"
sudo mkdir -p "\${BASE_DIR}/logs/nginx"
sudo chown -R "\$(whoami):\$(id -gn)" "\${BASE_DIR}"
echo "[ OK ] host 目錄: \${BASE_DIR}"

# ── 3. Pre-deploy 健康前置檢查 ─────────────────────────────────
echo "[    ] 執行 pre-deploy-check..."
bash pre-deploy-check.sh || { echo "[FAIL] Pre-deploy check 失敗，中止部署"; exit 1; }

# ── 4. Build & Start ────────────────────────────────────────────
echo "[    ] docker compose up --build..."
docker compose up -d --build
echo "[ OK ] compose started"

# ── 5. 等待健康狀態 ─────────────────────────────────────────────
echo "[    ] 等待服務健康（最多 60s）..."
for i in \$(seq 1 12); do
  sleep 5
  STATUS=\$(docker inspect --format='{{.State.Health.Status}}' "\${SLUG}-app" 2>/dev/null || echo "unknown")
  echo "       [\${i}/12] health status: \${STATUS}"
  if [ "\${STATUS}" = "healthy" ]; then
    break
  fi
done

# ── 6. 最終 health-check ───────────────────────────────────────
echo "[    ] 執行最終 health-check..."
bash health-check.sh && echo "" && echo "[ OK ] 部署完成 ✓" || {
  echo "[FAIL] health-check 失敗"
  echo "       docker logs: docker compose logs app"
  exit 1
}

echo ""
echo "===================================================="
echo " 部署完成"
echo " service : \${SLUG}"
echo " health  : http://localhost/health"
echo " logs    : docker compose logs -f app"
echo " stop    : docker compose down"
echo "===================================================="
`;
}

function _preDeployCheck({ slug, deployId }) {
  return `#!/usr/bin/env bash
# deploy/pre-deploy-check.sh — 部署前置確認
# deploy_pack_id: ${deployId}
# origin_signature: MrLiouWord
set -euo pipefail

PASS=0
FAIL=0

check() {
  local desc="$1"
  local cmd="$2"
  if eval "$cmd" > /dev/null 2>&1; then
    echo "  [ OK ] $desc"
    PASS=$((PASS+1))
  else
    echo "  [FAIL] $desc"
    FAIL=$((FAIL+1))
  fi
}

echo "── Pre-deploy Check ──────────────────────────────"

# 必要工具
check "docker installed"         "command -v docker"
check "docker compose available" "docker compose version"
check "curl installed"           "command -v curl"

# .env 必填項目
check "ANTHROPIC_API_KEY set"    "grep -q 'ANTHROPIC_API_KEY=sk-' '../.env'"
check "JWT_SECRET set"           "grep -vq 'JWT_SECRET=REPLACE' '../.env'"
check "BASE_URL set"             "grep -vq 'BASE_URL=https://your-domain' '../.env'"

# 關鍵檔案
check "Dockerfile exists"        "[ -f Dockerfile ]"
check "docker-compose.yml exists" "[ -f docker-compose.yml ]"
check "nginx.conf exists"        "[ -f nginx.conf ]"
check "backend/server.js exists" "[ -f ../backend/server.js ]"
check "storage/schema.sql exists" "[ -f ../storage/schema.sql ]"

echo "──────────────────────────────────────────────────"
echo "  Pass: $PASS  Fail: $FAIL"

if [ $FAIL -gt 0 ]; then
  echo "  [FAIL] pre-deploy check 未通過，請修正後再部署"
  exit 1
else
  echo "  [ OK ] 所有檢查通過，可以部署"
fi
`;
}

module.exports = { buildDeployPlan };
