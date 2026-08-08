'use strict';
// routes/webhook.js — Stripe Webhook 接收與處理
// origin_signature: MrLiouWord
// ⚠ rawBody 必須在 express.json() 之前掛載

const express = require('express');
const router = express.Router();

const { constructWebhookEvent, retrieveCheckoutSession } = require('../modules/payment_entry');
const { confirm } = require('../modules/confirmation');
const { createSubscription, renewSubscription, cancelSubscription } = require('../modules/subscription');
const { getOrderByStripeSession } = require('../modules/order');
const { writeEvent } = require('../modules/ledger');
const logger = require('../utils/logger');

// ── POST /webhook/stripe ─────────────────────────────────────────
// ⚠ 必須用 raw body — 在 server.js 中對此路由不加 express.json()
router.post('/stripe', express.raw({ type: 'application/json' }), async (req, res) => {
  const sig = req.headers['stripe-signature'];

  let event;
  try {
    event = constructWebhookEvent(req.body, sig);
  } catch (e) {
    logger.error('Webhook signature failed', { err: e.message });
    return res.status(400).send(`Webhook Error: ${e.message}`);
  }

  logger.info('Webhook received', { type: event.type });

  try {
    switch (event.type) {

      // 單次付款成功
      case 'checkout.session.completed': {
        const session = event.data.object;
        if (session.payment_status !== 'paid') break;

        // 找訂單
        const order = getOrderByStripeSession(session.id);
        if (!order) {
          logger.warn('Webhook: order not found for stripe session', { stripeSession: session.id });
          break;
        }

        if (order.plan_type === 'once') {
          // 單次解鎖
          const paymentIntentId = session.payment_intent;
          const amount = session.amount_total;
          const currency = session.currency;

          await confirm({
            orderId: order.id,
            providerTxId: paymentIntentId,
            amount,
            currency,
            rawEvent: event,
          });
        } else if (order.plan_type === 'subscription') {
          // 訂閱啟動
          const subId = session.subscription;
          createSubscription({
            userId: order.user_id,
            sessionId: order.session_id,
            providerSubId: subId,
            amount: session.amount_total || 49900,
            currency: session.currency || 'twd',
          });
          // 訂閱不需要 confirm 單次分析，但更新訂單狀態
          const { updateOrderStatus } = require('../modules/order');
          updateOrderStatus(order.id, 'unlocked');
        }
        break;
      }

      // 訂閱續費
      case 'invoice.payment_succeeded': {
        const invoice = event.data.object;
        if (invoice.subscription) {
          renewSubscription(invoice.subscription);
        }
        break;
      }

      // 訂閱取消
      case 'customer.subscription.deleted': {
        const sub = event.data.object;
        cancelSubscription(sub.id);
        break;
      }

      // 付款失敗
      case 'payment_intent.payment_failed': {
        const pi = event.data.object;
        writeEvent({
          eventType: 'error',
          meta: { reason: 'payment_failed', providerTxId: pi.id },
        });
        break;
      }

      default:
        logger.debug('Webhook: unhandled event', { type: event.type });
    }
  } catch (e) {
    logger.error('Webhook handler error', { type: event.type, err: e.message });
    return res.status(500).json({ error: 'Webhook handler failed' });
  }

  res.json({ received: true });
});

module.exports = router;
