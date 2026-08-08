'use strict';
// routes/payment.js — 付款路由（含事件追蹤）
// origin_signature: MrLiouWord

const express = require('express');
const router = express.Router();

const { authMiddleware } = require('../modules/identity');
const { createOnceCheckout, createSubscriptionCheckout } = require('../modules/payment_entry');
const { track, ctxFromReq } = require('../modules/events');
const logger = require('../utils/logger');

router.use(authMiddleware);

// ── POST /api/pay/once ───────────────────────────────────────────
router.post('/once', async (req, res) => {
  const { analysis_id } = req.body || {};

  if (!analysis_id) {
    return res.status(400).json({ error: 'analysis_id required' });
  }

  // 追蹤：點擊單次付款
  track('pay_click_once', ctxFromReq(req, {
    analysisId: analysis_id,
    meta: { plan: 'once' },
  }));

  try {
    const result = await createOnceCheckout({
      analysisId: analysis_id,
      sessionId: req.sessionId,
      userId: req.userId,
    });
    res.json(result);
  } catch (e) {
    logger.error('Pay once error', { err: e.message });
    res.status(500).json({ error: '建立付款連結失敗，請重試' });
  }
});

// ── POST /api/pay/subscription ───────────────────────────────────
router.post('/subscription', async (req, res) => {
  // 追蹤：點擊訂閱
  track('pay_click_sub', ctxFromReq(req, { meta: { plan: 'subscription' } }));

  try {
    const result = await createSubscriptionCheckout({
      sessionId: req.sessionId,
      userId: req.userId,
    });
    res.json(result);
  } catch (e) {
    logger.error('Pay sub error', { err: e.message });
    res.status(500).json({ error: '建立訂閱連結失敗，請重試' });
  }
});

module.exports = router;
