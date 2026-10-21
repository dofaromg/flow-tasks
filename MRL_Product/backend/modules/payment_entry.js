'use strict';
// modules/payment_entry.js — 建立 Stripe 付款入口
// origin_signature: MrLiouWord

const Stripe = require('stripe');
const config = require('../config');
const { createOrder, updateOrderStatus } = require('./order');
const logger = require('../utils/logger');

const stripe = Stripe(config.stripeSecretKey);

/**
 * 建立單次付款 Checkout Session
 */
async function createOnceCheckout({ analysisId, sessionId, userId }) {
  const order = createOrder({ analysisId, sessionId, userId, planType: 'once' });

  const session = await stripe.checkout.sessions.create({
    mode: 'payment',
    line_items: [{
      price_data: {
        currency: config.product.currency,
        unit_amount: config.product.onceAmount,
        product_data: {
          name: '完整分析報告（單次解鎖）',
          description: '解鎖本次分析的完整執行步驟、優先順序與補充建議',
        },
      },
      quantity: 1,
    }],
    metadata: {
      orderId: order.id,
      analysisId: analysisId || '',
      sessionId,
      planType: 'once',
      origin: config.originSignature,
    },
    success_url: `${config.baseUrl}/success?order=${order.id}&session_id={CHECKOUT_SESSION_ID}`,
    cancel_url:  `${config.baseUrl}/cancel?order=${order.id}`,
  });

  // 記錄 stripe session id 到訂單
  updateOrderStatus(order.id, 'pending', { stripeSessionId: session.id });

  logger.info('Stripe once checkout created', { orderId: order.id, stripeSession: session.id });
  return { checkoutUrl: session.url, orderId: order.id, stripeSessionId: session.id };
}

/**
 * 建立月費訂閱 Checkout Session
 */
async function createSubscriptionCheckout({ sessionId, userId }) {
  const order = createOrder({ analysisId: null, sessionId, userId, planType: 'subscription' });

  const session = await stripe.checkout.sessions.create({
    mode: 'subscription',
    line_items: [{
      price: config.stripePriceSub,
      quantity: 1,
    }],
    metadata: {
      orderId: order.id,
      sessionId,
      planType: 'subscription',
      origin: config.originSignature,
    },
    success_url: `${config.baseUrl}/success?order=${order.id}&session_id={CHECKOUT_SESSION_ID}`,
    cancel_url:  `${config.baseUrl}/cancel?order=${order.id}`,
  });

  updateOrderStatus(order.id, 'pending', { stripeSessionId: session.id });

  logger.info('Stripe subscription checkout created', { orderId: order.id, stripeSession: session.id });
  return { checkoutUrl: session.url, orderId: order.id, stripeSessionId: session.id };
}

/**
 * 驗證 Stripe webhook 簽名並解析事件
 */
function constructWebhookEvent(rawBody, sig) {
  return stripe.webhooks.constructEvent(rawBody, sig, config.stripeWebhookSecret);
}

/**
 * 取得 Stripe Checkout Session 詳細資料
 */
async function retrieveCheckoutSession(stripeSessionId) {
  return stripe.checkout.sessions.retrieve(stripeSessionId, {
    expand: ['payment_intent', 'subscription'],
  });
}

module.exports = { createOnceCheckout, createSubscriptionCheckout, constructWebhookEvent, retrieveCheckoutSession };
