'use strict';
// modules/confirmation.js — 驗證付款是否成立，防重複解鎖
// origin_signature: MrLiouWord
// 核心不可繞過：沒有 confirmation，不可解鎖

const { getDb } = require('./db');
const { uuid } = require('../utils/ids');
const { now } = require('../utils/time');
const { updateOrderStatus, getOrder } = require('./order');
const { writeEvent, hasUnlockEvent } = require('./ledger');
const logger = require('../utils/logger');

/**
 * 記錄付款成功
 * 由 webhook handler 呼叫（非使用者端觸發）
 */
function recordPayment({ orderId, providerTxId, amount, currency, rawEvent }) {
  const db = getDb();
  const id = uuid();

  // 防重複：同一 provider_tx_id 不可重複記錄
  const existing = db.prepare('SELECT id FROM payments WHERE provider_tx_id = ?').get(providerTxId);
  if (existing) {
    logger.warn('Duplicate payment ignored', { providerTxId });
    return existing.id;
  }

  db.prepare(`
    INSERT INTO payments (id, order_id, provider, provider_tx_id, amount, currency, status, raw_event, created_at)
    VALUES (?, ?, 'stripe', ?, ?, ?, 'succeeded', ?, ?)
  `).run(id, orderId, providerTxId, amount, currency, JSON.stringify(rawEvent), now());

  return id;
}

/**
 * 核心確認流程：
 * 1. 驗證 orderId 存在
 * 2. 驗證非重複解鎖
 * 3. 記錄 payment
 * 4. 更新 order 狀態
 * 5. 寫 ledger（payment_success → order_paid）
 * 6. 觸發 translator（order_paid → result_unlock）
 * @returns {{ success: boolean, paymentId: string, orderId: string }}
 */
function confirm({ orderId, providerTxId, amount, currency, rawEvent }) {
  const order = getOrder(orderId);
  if (!order) {
    logger.error('Confirmation: order not found', { orderId });
    throw new Error(`Order not found: ${orderId}`);
  }

  if (order.status === 'unlocked') {
    logger.warn('Confirmation: already unlocked', { orderId });
    return { success: true, alreadyDone: true, orderId };
  }

  if (hasUnlockEvent(orderId)) {
    logger.warn('Confirmation: duplicate unlock attempt blocked', { orderId });
    return { success: true, alreadyDone: true, orderId };
  }

  // 1. 寫付款記錄
  const paymentId = recordPayment({ orderId, providerTxId, amount, currency, rawEvent });

  // 2. 更新訂單狀態 paid
  updateOrderStatus(orderId, 'paid');

  // 3. 寫 ledger: payment_success
  writeEvent({
    eventType: 'payment_success',
    orderId,
    paymentId,
    analysisId: order.analysis_id,
    sessionId: order.session_id,
    amount,
    meta: { providerTxId, currency },
  });

  // 4. 寫 ledger: order_paid（translator 層）
  writeEvent({
    eventType: 'order_paid',
    orderId,
    paymentId,
    analysisId: order.analysis_id,
    sessionId: order.session_id,
    amount,
    meta: { planType: order.plan_type },
  });

  // 5. 觸發解鎖
  const unlockResult = require('./translator').translate('order_paid', { orderId, paymentId, order });

  logger.info('Confirmation complete', { orderId, paymentId, unlockResult });
  return { success: true, orderId, paymentId, unlockResult };
}

module.exports = { confirm, recordPayment };
