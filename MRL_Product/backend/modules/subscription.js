'use strict';
// modules/subscription.js — 管理月費訂閱狀態
// origin_signature: MrLiouWord

const { getDb } = require('./db');
const { uuid } = require('../utils/ids');
const { now, addMonths, isPast } = require('../utils/time');
const { writeEvent } = require('./ledger');
const logger = require('../utils/logger');

/**
 * 建立訂閱記錄
 */
function createSubscription({ userId, sessionId, providerSubId, amount, currency }) {
  const db = getDb();
  const id = uuid();
  const startedAt = now();
  const expiresAt = addMonths(1);

  db.prepare(`
    INSERT INTO subscriptions (id, user_id, session_id, provider_sub_id, status, plan_type, amount, currency, started_at, expires_at, created_at, updated_at)
    VALUES (?, ?, ?, ?, 'active', 'monthly', ?, ?, ?, ?, ?, ?)
  `).run(id, userId || null, sessionId || null, providerSubId, amount, currency, startedAt, expiresAt, now(), now());

  writeEvent({
    eventType: 'sub_activated',
    sessionId,
    amount,
    meta: { subscriptionId: id, providerSubId },
  });

  logger.info('Subscription created', { id, providerSubId });
  return db.prepare('SELECT * FROM subscriptions WHERE id = ?').get(id);
}

/**
 * 取得使用者訂閱狀態
 */
function getSubscription(userId, sessionId) {
  const db = getDb();
  return userId
    ? db.prepare(`SELECT * FROM subscriptions WHERE user_id = ? ORDER BY created_at DESC LIMIT 1`).get(userId)
    : db.prepare(`SELECT * FROM subscriptions WHERE session_id = ? ORDER BY created_at DESC LIMIT 1`).get(sessionId);
}

/**
 * 更新訂閱（renewall from webhook）
 */
function renewSubscription(providerSubId) {
  const db = getDb();
  const expiresAt = addMonths(1);
  db.prepare(`
    UPDATE subscriptions SET status = 'active', expires_at = ?, updated_at = ?
    WHERE provider_sub_id = ?
  `).run(expiresAt, now(), providerSubId);
  logger.info('Subscription renewed', { providerSubId, expiresAt });
}

/**
 * 取消訂閱
 */
function cancelSubscription(providerSubId) {
  const db = getDb();
  db.prepare(`UPDATE subscriptions SET status = 'cancelled', updated_at = ? WHERE provider_sub_id = ?`)
    .run(now(), providerSubId);
  writeEvent({ eventType: 'sub_expired', meta: { providerSubId } });
  logger.info('Subscription cancelled', { providerSubId });
}

module.exports = { createSubscription, getSubscription, renewSubscription, cancelSubscription };
