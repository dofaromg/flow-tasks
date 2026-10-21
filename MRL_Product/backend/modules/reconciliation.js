'use strict';
// modules/reconciliation.js — 對帳、退款處理、異常恢復
// origin_signature: MrLiouWord
// 後期補強模組：不在 Phase 1 主路徑，但結構先留

const { getDb } = require('./db');
const { writeEvent, queryLedger } = require('./ledger');
const { updateOrderStatus } = require('./order');
const { now } = require('../utils/time');
const logger = require('../utils/logger');

/**
 * 對帳：找出 paid 但未 unlocked 的訂單
 * 場景：webhook 遺失、伺服器重啟等邊緣情況
 */
function findInconsistentOrders() {
  const db = getDb();
  // 找狀態為 paid 但無 result_unlock 帳本事件的訂單
  return db.prepare(`
    SELECT o.* FROM orders o
    WHERE o.status = 'paid'
    AND NOT EXISTS (
      SELECT 1 FROM ledger l
      WHERE l.order_id = o.id AND l.event_type = 'result_unlock'
    )
    ORDER BY o.created_at DESC
    LIMIT 50
  `).all();
}

/**
 * 修復：對 paid 但未解鎖的訂單重新觸發解鎖
 */
function repairOrder(orderId) {
  const db = getDb();
  const order = db.prepare('SELECT * FROM orders WHERE id = ?').get(orderId);
  if (!order) {
    logger.warn('Reconciliation: order not found', { orderId });
    return false;
  }

  if (order.status !== 'paid') {
    logger.info('Reconciliation: order not in paid state, skip', { orderId, status: order.status });
    return false;
  }

  logger.info('Reconciliation: repairing order', { orderId });

  // 重新執行 translator
  const { translate } = require('./translator');
  translate('order_paid', { orderId, paymentId: null, order });

  writeEvent({
    eventType: 'order_paid',
    orderId,
    analysisId: order.analysis_id,
    sessionId: order.session_id,
    amount: order.amount,
    meta: { repaired: true, repairedAt: now() },
  });

  return true;
}

/**
 * 記錄退款事件（由 Stripe webhook 驅動）
 */
function recordRefund({ orderId, paymentId, amount, reason }) {
  const db = getDb();

  // 更新訂單狀態
  updateOrderStatus(orderId, 'refunded');

  // 鎖定已解鎖的分析（可選：視業務邏輯）
  const order = db.prepare('SELECT * FROM orders WHERE id = ?').get(orderId);
  if (order?.analysis_id) {
    db.prepare(`UPDATE analyses SET status = 'refunded', updated_at = ? WHERE id = ?`)
      .run(now(), order.analysis_id);
  }

  // 寫帳本
  writeEvent({
    eventType: 'refund',
    orderId,
    paymentId,
    analysisId: order?.analysis_id,
    sessionId: order?.session_id,
    amount,
    meta: { reason },
  });

  logger.info('Refund recorded', { orderId, amount });
  return true;
}

/**
 * 執行全量對帳（admin 用）
 */
function runReconciliation() {
  const inconsistent = findInconsistentOrders();
  logger.info('Reconciliation: found inconsistent orders', { count: inconsistent.length });

  const results = inconsistent.map(order => {
    try {
      const repaired = repairOrder(order.id);
      return { orderId: order.id, repaired };
    } catch (e) {
      logger.error('Reconciliation: repair failed', { orderId: order.id, err: e.message });
      return { orderId: order.id, repaired: false, error: e.message };
    }
  });

  return {
    checked: inconsistent.length,
    results,
    ranAt: now(),
  };
}

module.exports = { findInconsistentOrders, repairOrder, recordRefund, runReconciliation };
