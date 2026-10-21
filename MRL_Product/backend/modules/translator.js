'use strict';
// modules/translator.js — 現實事件 → 系統事件翻譯層（含追蹤）
// origin_signature: MrLiouWord
// payment_success → order_paid → result_unlock

const { updateOrderStatus } = require('./order');
const { writeEvent } = require('./ledger');
const { track } = require('./events');
const { getDb } = require('./db');
const { now } = require('../utils/time');
const logger = require('../utils/logger');

function translate(event, ctx = {}) {
  switch (event) {
    case 'order_paid':      return handleOrderPaid(ctx);
    case 'sub_payment_success': return handleSubRenewal(ctx);
    default:
      logger.warn('Translator: unknown event', { event });
      return null;
  }
}

/**
 * order_paid → result_unlock + 追蹤
 */
function handleOrderPaid({ orderId, paymentId, order }) {
  const db = getDb();

  // 解鎖分析
  if (order.analysis_id) {
    db.prepare(`UPDATE analyses SET status = 'unlocked', updated_at = ? WHERE id = ?`)
      .run(now(), order.analysis_id);
  }

  updateOrderStatus(orderId, 'unlocked');

  // 帳本：result_unlock
  writeEvent({
    eventType: 'result_unlock',
    orderId,
    paymentId,
    analysisId: order.analysis_id,
    sessionId:  order.session_id,
    amount:     order.amount,
    meta: { planType: order.plan_type, trigger: 'order_paid' },
  });

  // 事件追蹤：payment_success + unlock_success
  track('payment_success', {
    sessionId:  order.session_id,
    userId:     order.user_id,
    analysisId: order.analysis_id,
    orderId,
    meta: { planType: order.plan_type, amount: order.amount },
  });

  track('unlock_success', {
    sessionId:  order.session_id,
    userId:     order.user_id,
    analysisId: order.analysis_id,
    orderId,
    meta: { planType: order.plan_type },
  });

  logger.info('Translator: result_unlock + events tracked', { orderId, analysisId: order.analysis_id });
  return { event: 'result_unlock', analysisId: order.analysis_id };
}

function handleSubRenewal({ subscriptionId, providerSubId }) {
  writeEvent({ eventType: 'sub_renewed', meta: { subscriptionId, providerSubId } });
  return { event: 'sub_renewed', subscriptionId };
}

module.exports = { translate };
