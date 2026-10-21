'use strict';
// modules/order.js — 建立與管理訂單
// origin_signature: MrLiouWord

const { getDb } = require('./db');
const { uuid } = require('../utils/ids');
const { now } = require('../utils/time');
const config = require('../config');

const VALID_STATUSES = ['pending', 'paid', 'unlocked', 'failed', 'refunded'];

/**
 * 建立新訂單
 */
function createOrder({ analysisId, sessionId, userId, planType }) {
  const db = getDb();

  const amount = planType === 'subscription'
    ? config.product.subAmount
    : config.product.onceAmount;

  const id = uuid();
  db.prepare(`
    INSERT INTO orders (id, analysis_id, session_id, user_id, plan_type, amount, currency, status, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?)
  `).run(id, analysisId || null, sessionId, userId || null, planType, amount, config.product.currency, now(), now());

  return getOrder(id);
}

/**
 * 取得訂單
 */
function getOrder(orderId) {
  return getDb().prepare('SELECT * FROM orders WHERE id = ?').get(orderId);
}

/**
 * 根據 Stripe session id 取得訂單
 */
function getOrderByStripeSession(stripeSessionId) {
  return getDb().prepare('SELECT * FROM orders WHERE stripe_session_id = ?').get(stripeSessionId);
}

/**
 * 更新訂單狀態
 */
function updateOrderStatus(orderId, status, extra = {}) {
  if (!VALID_STATUSES.includes(status)) throw new Error(`Invalid status: ${status}`);
  const db = getDb();
  const sets = ['status = ?', 'updated_at = ?'];
  const vals = [status, now()];

  if (extra.stripeSessionId !== undefined) {
    sets.push('stripe_session_id = ?');
    vals.push(extra.stripeSessionId);
  }

  db.prepare(`UPDATE orders SET ${sets.join(', ')} WHERE id = ?`)
    .run(...vals, orderId);

  return getOrder(orderId);
}

/**
 * 列出 session 的訂單
 */
function listOrdersBySession(sessionId) {
  return getDb().prepare('SELECT * FROM orders WHERE session_id = ? ORDER BY created_at DESC').all(sessionId);
}

module.exports = { createOrder, getOrder, getOrderByStripeSession, updateOrderStatus, listOrdersBySession };
