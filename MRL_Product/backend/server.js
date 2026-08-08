'use strict';
// server.js — MRL_Product_v1 主程式
// origin_signature: MrLiouWord
// U = MRL_World_Gateway_v1

const express = require('express');
const path = require('path');
const config = require('./config');
const { initDb, runCategoryMigration } = require('./modules/db');
const logger = require('./utils/logger');

const app = express();

// ── DB Init ───────────────────────────────────────────────────────
initDb();
runCategoryMigration(); // 第七包：冪等補 category 欄位

// ── Static Assets ─────────────────────────────────────────────────
app.use('/assets', express.static(path.join(__dirname, '../frontend/assets')));

// ── Webhook（必須在 express.json 之前，保留 raw body）────────────
app.use('/webhook', require('./routes/webhook'));

// ── Body Parsers ──────────────────────────────────────────────────
app.use(express.json({ limit: '512kb' }));
app.use(express.urlencoded({ extended: false }));

// ── CORS（開發用）────────────────────────────────────────────────
if (config.nodeEnv !== 'production') {
  app.use((req, res, next) => {
    res.set('Access-Control-Allow-Origin', '*');
    res.set('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Admin-Key');
    res.set('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
    if (req.method === 'OPTIONS') return res.sendStatus(204);
    next();
  });
}

// ── Security Headers ──────────────────────────────────────────────
app.use((req, res, next) => {
  res.set('X-Content-Type-Options', 'nosniff');
  res.set('X-Frame-Options', 'DENY');
  res.set('X-Powered-By', 'MRL_World_Gateway_v1');
  res.set('X-Origin-Signature', 'MrLiouWord');
  next();
});

// ── Routes ────────────────────────────────────────────────────────
app.use('/', require('./routes/page'));
app.use('/api', require('./routes/api'));
app.use('/api/pay', require('./routes/payment'));
app.use('/admin', require('./routes/admin'));
app.use('/api/pack', require('./routes/pack'));
app.use('/api/scaffold',   require('./routes/scaffold'));
app.use('/api/deploypack', require('./routes/deploypack'));

// ── Health Check ──────────────────────────────────────────────────
app.get('/health', (req, res) => {
  res.json({
    status: 'ok',
    service: 'MRL_Product_v1',
    gateway: 'MRL_World_Gateway_v1',
    origin: 'MrLiouWord',
    ts: new Date().toISOString(),
  });
});

// ── 404 ───────────────────────────────────────────────────────────
app.use((req, res) => {
  if (req.path.startsWith('/api') || req.path.startsWith('/admin')) {
    return res.status(404).json({ error: 'Not found' });
  }
  res.status(404).sendFile('index.html', {
    root: path.join(__dirname, '../frontend'),
  });
});

// ── Error Handler ─────────────────────────────────────────────────
app.use((err, req, res, _next) => {
  logger.error('Unhandled error', { err: err.message, stack: err.stack });
  const status = err.status || 500;
  res.status(status).json({ error: err.message || 'Internal server error' });
});

// ── Start ─────────────────────────────────────────────────────────
app.listen(config.port, () => {
  logger.info(`MRL_Product_v1 started`, {
    port: config.port,
    env: config.nodeEnv,
    gateway: 'MRL_World_Gateway_v1',
    origin: config.originSignature,
  });
});

module.exports = app;
