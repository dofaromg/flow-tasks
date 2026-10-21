'use strict';
// routes/admin.js — 管理 API（metrics / funnel / events / reconcile）
// origin_signature: MrLiouWord

const express = require('express');
const router = express.Router();
const config = require('../config');
const { queryLedger } = require('../modules/ledger');
const { getDb } = require('../modules/db');
const { writeFeedback, getFeedbackSummary, recentFeedback, logError, recentErrors, errorStats } = require('../modules/feedback');
const { getMetrics, getFunnel, recentEvents, dailyCounts, getCategoryFunnel } = require('../modules/events');
const { runReconciliation } = require('../modules/reconciliation');

// ── Admin 認證 middleware ─────────────────────────────────────────
router.use((req, res, next) => {
  const key = req.headers['x-admin-key'] || req.query.key;
  if (key !== config.adminKey) {
    return res.status(403).json({ error: 'Forbidden' });
  }
  next();
});

// ── GET /admin/metrics ───────────────────────────────────────────
// 今日 + 近 7 日核心統計
router.get('/metrics', (req, res) => {
  try {
    res.json({ ok: true, origin: 'MrLiouWord', ...getMetrics() });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// ── GET /admin/funnel ────────────────────────────────────────────
// 漏斗轉換率
router.get('/funnel', (req, res) => {
  const days = parseInt(req.query.days || '7');
  try {
    res.json({ ok: true, days, funnel: getFunnel(days) });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// ── GET /admin/events ────────────────────────────────────────────
// 最近事件（debug）
router.get('/events', (req, res) => {
  const limit = parseInt(req.query.limit || '30');
  try {
    res.json({ ok: true, events: recentEvents(limit) });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// ── GET /admin/trend ─────────────────────────────────────────────
// 近 N 天每日趨勢
router.get('/trend', (req, res) => {
  const days = parseInt(req.query.days || '14');
  try {
    res.json({
      ok: true,
      days,
      home:     dailyCounts('page_view_home',   days),
      app:      dailyCounts('page_view_app',    days),
      analyze:  dailyCounts('analyze_success',  days),
      payment:  dailyCounts('payment_success',  days),
      unlock:   dailyCounts('unlock_success',   days),
    });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// ── GET /admin/orders ────────────────────────────────────────────
router.get('/orders', (req, res) => {
  const db = getDb();
  const limit  = parseInt(req.query.limit  || '50');
  const offset = parseInt(req.query.offset || '0');
  const orders = db.prepare('SELECT * FROM orders ORDER BY created_at DESC LIMIT ? OFFSET ?')
    .all(limit, offset);
  res.json({ orders, count: orders.length });
});

// ── GET /admin/payments ──────────────────────────────────────────
router.get('/payments', (req, res) => {
  const db = getDb();
  const payments = db.prepare('SELECT id, order_id, provider_tx_id, amount, currency, status, created_at FROM payments ORDER BY created_at DESC LIMIT 100').all();
  res.json({ payments });
});

// ── GET /admin/ledger ────────────────────────────────────────────
router.get('/ledger', (req, res) => {
  const entries = queryLedger({
    limit:     parseInt(req.query.limit     || '100'),
    offset:    parseInt(req.query.offset    || '0'),
    eventType: req.query.event_type,
    orderId:   req.query.order_id,
  });
  res.json({ ledger: entries });
});

// ── GET /admin/stats ─────────────────────────────────────────────
router.get('/stats', (req, res) => {
  const db = getDb();
  const totalOrders   = db.prepare("SELECT COUNT(*) as c FROM orders").get().c;
  const paidOrders    = db.prepare("SELECT COUNT(*) as c FROM orders WHERE status IN ('paid','unlocked')").get().c;
  const totalRevenue  = db.prepare("SELECT COALESCE(SUM(amount),0) as s FROM payments WHERE status='succeeded'").get().s;
  const activeSubs    = db.prepare("SELECT COUNT(*) as c FROM subscriptions WHERE status='active'").get().c;
  const totalAnalyses = db.prepare("SELECT COUNT(*) as c FROM analyses").get().c;
  const totalUsers    = db.prepare("SELECT COUNT(*) as c FROM users").get().c;

  res.json({
    origin: 'MrLiouWord',
    totalOrders, paidOrders,
    totalRevenueTWD: Math.floor(totalRevenue / 100),
    activeSubscriptions: activeSubs,
    totalAnalyses,
    totalUsers,
  });
});

// ── GET /admin/health ────────────────────────────────────────────
router.get('/health', (req, res) => {
  const db = getDb();
  try {
    const dbOk  = !!db.prepare('SELECT 1').get();
    const tables = db.prepare("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").all().map(r => r.name);
    const ledgerCount   = db.prepare('SELECT COUNT(*) as c FROM ledger').get().c;
    const orderCount    = db.prepare('SELECT COUNT(*) as c FROM orders').get().c;
    const eventCount    = db.prepare('SELECT COUNT(*) as c FROM event_logs').get().c;
    const unlockedCount = db.prepare("SELECT COUNT(*) as c FROM orders WHERE status='unlocked'").get().c;
    res.json({ ok: true, db: dbOk, tables, ledgerCount, orderCount, eventCount, unlockedCount, origin: 'MrLiouWord', ts: new Date().toISOString() });
  } catch (e) {
    res.status(500).json({ ok: false, error: e.message });
  }
});

// ── POST /admin/reconcile ────────────────────────────────────────
router.post('/reconcile', (req, res) => {
  try {
    const result = runReconciliation();
    res.json({ ok: true, ...result });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});


// ── POST /admin/feedback ─────────────────────────────────────────
// 管理員查看所有使用者回饋
router.get('/feedback', (req, res) => {
  try {
    const limit = parseInt(req.query.limit || '50');
    const summary = getFeedbackSummary();
    const items = recentFeedback(limit);
    res.json({ ok: true, summary, items });
  } catch (e) { res.status(500).json({ error: e.message }); }
});

// ── POST /api/feedback（公開端點，使用者提交）────────────────────
// 注意：此端點掛在 admin router，需另在 server.js 或 api router 中加公開版
// 這裡先建 admin 查詢端

// ── GET /admin/errors ────────────────────────────────────────────
router.get('/errors', (req, res) => {
  try {
    const limit = parseInt(req.query.limit || '50');
    const days  = parseInt(req.query.days  || '7');
    const stats = errorStats(days);
    const recent = recentErrors(limit);
    res.json({ ok: true, days, stats, recent });
  } catch (e) { res.status(500).json({ error: e.message }); }
});

// ── GET /admin/category ───────────────────────────────────────────
// 各問題分類的分析→點擊→解鎖 funnel
router.get('/category', (req, res) => {
  const days = parseInt(req.query.days || '7');
  try {
    const breakdown = getCategoryFunnel(days);
    res.json({ ok: true, days, breakdown });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

module.exports = router;
