'use strict';
// routes/api.js — 核心 API 路由（含事件追蹤）
// origin_signature: MrLiouWord

const express = require('express');
const router = express.Router();

const { authMiddleware, createSession, login } = require('../modules/identity');
const { analyze: aiAnalyze } = require('../modules/ai');
const { getDb } = require('../modules/db');
const { buildPartial } = require('../modules/partial_output');
const { getResult } = require('../modules/full_output');
const { writeEvent } = require('../modules/ledger');
// 第十四包：Core Generator
const CoreGenerator = require('../core/generator');
const { selectTemplate } = require('../core/generator/template-selector');
const { normalizeProductResult, TEMPLATE_SCHEMA } = require('../templates/product-template'); // 保留相容
const { track, ctxFromReq } = require('../modules/events');
const { getOrder } = require('../modules/order');
const { hasActiveSubscription,
        hasActiveSubscriptionWithOwner,
        isOwnerAccount } = require('../modules/rules');
const { uuid } = require('../utils/ids');
const { now } = require('../utils/time');
const { requireFields, sanitizeText } = require('../utils/validate');
const logger = require('../utils/logger');

router.use(authMiddleware);

// ── POST /api/session ────────────────────────────────────────────
router.post('/session', (req, res) => {
  const sess = createSession(req.userId || null);
  res.set('X-Session-Token', sess.token);
  // 第十九包：回傳訂閱狀態，讓前端知道是否為訂閱者
  // 第十九包：owner 帳號直接有效訂閱
  const _email = req.body?.email || req.email || null;
  const sub = hasActiveSubscriptionWithOwner(sess.sessionId, req.userId, _email);
  res.json({
    token: sess.token,
    sessionId: sess.sessionId,
    has_subscription: !!sub,
    subscription_expires: sub ? sub.expires_at : null,
  });
});

// ── GET /api/session/status ───────────────────────────────────────
// 已登入者查詢自己的訂閱狀態
router.get('/session/status', (req, res) => {
  const sub = hasActiveSubscriptionWithOwner(req.sessionId, req.userId, req.email);
  res.json({
    session_id: req.sessionId,
    has_subscription: !!sub,
    subscription_expires: sub ? sub.expires_at : null,
    plan_type: sub ? 'subscription' : 'free',
  });
});

// ── POST /api/login ──────────────────────────────────────────────
router.post('/login', (req, res) => {
  const { email } = req.body || {};
  if (!email) return res.status(400).json({ error: 'email required' });
  const result = login(email);
  // 第十九包：owner 帳號登入直接有效訂閱
  const isOwner = isOwnerAccount(email);
  res.json({
    ...result,
    has_subscription:     isOwner || !!result.has_subscription,
    subscription_expires: isOwner ? '2099-12-31T00:00:00Z' : result.subscription_expires,
    is_owner:             isOwner,
  });
});

// ── POST /api/analyze ────────────────────────────────────────────
router.post('/analyze', async (req, res) => {
  const { problem_text, category, example_prompt_used } = req.body || {};

  try { requireFields({ problem_text }, ['problem_text']); }
  catch (e) { return res.status(400).json({ error: e.message }); }

  const cleanText = sanitizeText(problem_text, 3000);
  if (cleanText.length < 10) {
    return res.status(400).json({ error: '問題描述太短，請輸入更多內容' });
  }

  // 追蹤：分析開始
  track('analyze_started', { ...ctxFromReq(req), category: category || null, meta: { len: cleanText.length, exampleUsed: !!example_prompt_used } });

  const db = getDb();
  const analysisId = uuid();

  const catVal = category ? String(category).slice(0, 50) : null;
  db.prepare(`
    INSERT INTO analyses (id, session_id, user_id, problem_text, category, example_prompt_used, status, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, 'pending', ?, ?)
  `).run(analysisId, req.sessionId, req.userId || null, cleanText, catVal, example_prompt_used ? 1 : 0, now(), now());

  writeEvent({
    eventType: 'analysis_created',
    analysisId,
    sessionId: req.sessionId,
    meta: { len: cleanText.length },
  });

  try {
    // 第十四包：Core Generator 主流程
    const hasSub = hasActiveSubscriptionWithOwner(req.sessionId, req.userId, req.email);

    // 呼叫 Core Generator（含 AnalyzeEngine + TemplateSelector + Normalizer + Composer）
    const { rawResult, payload } = await CoreGenerator.analyze({
      problemText: cleanText,
      category:    catVal || null,
      analysisId,
      isPartial:        !hasSub,
      requiresPayment:  !hasSub,
      meta: {
        example_prompt_used: !!example_prompt_used,
        plan_type: hasSub ? 'subscription' : null,
      },
    });

    // 寫入 DB（訂閱者直接設 unlocked，一般使用者設 done 等付款）
    db.prepare(`
      UPDATE analyses
      SET full_result = ?, partial_result = ?, status = ?, updated_at = ?
      WHERE id = ?
    `).run(
      JSON.stringify(rawResult),
      JSON.stringify(buildPartial(rawResult)),
      hasSub ? 'unlocked' : 'done',
      now(),
      analysisId
    );

    if (hasSub) {
      track('analyze_success',  { ...ctxFromReq(req), analysisId, category: catVal });
      track('result_full_view', ctxFromReq(req, { analysisId, meta: { via: 'subscription' } }));
    } else {
      track('analyze_success',  { ...ctxFromReq(req), analysisId, category: catVal });
    }

    return res.json(payload);

  } catch (aiErr) {
    db.prepare(`UPDATE analyses SET status = 'failed', updated_at = ? WHERE id = ?`)
      .run(now(), analysisId);
    track('analyze_failed', ctxFromReq(req, { analysisId, meta: { err: aiErr.message } }));
    require('../modules/feedback').logError({ errorType: 'ai_failed', message: aiErr.message, stack: aiErr.stack, sessionId: req.sessionId, analysisId });
    logger.error('Analyze AI error', { err: aiErr.message });
    return res.status(500).json({ error: 'AI 分析失敗，請重試' });
  }
});

// ── GET /api/result/:analysis_id ─────────────────────────────────
router.get('/result/:analysisId', (req, res) => {
  const { analysisId } = req.params;
  try {
    const result = getResult(analysisId, req.sessionId, req.userId);

    // 追蹤完整結果查看
    if (!result.isPartial) {
      track('result_full_view', ctxFromReq(req, { analysisId }));
    }

    res.json(result);
  } catch (e) {
    res.status(e.status || 500).json({ error: e.message });
  }
});

// ── GET /api/order/:orderId ──────────────────────────────────────
router.get('/order/:orderId', (req, res) => {
  const order = getOrder(req.params.orderId);
  if (!order) return res.status(404).json({ error: 'Order not found' });
  res.json({
    id: order.id,
    status: order.status,
    plan_type: order.plan_type,
    analysis_id: order.analysis_id,
    created_at: order.created_at,
  });
});


// ── POST /api/feedback ───────────────────────────────────────────
// 公開端點：使用者提交結果評分與回饋
router.post('/feedback', (req, res) => {
  const { analysis_id, rating, comment, feedback_type } = req.body || {};
  try {
    const { writeFeedback } = require('../modules/feedback');
    const { track, ctxFromReq } = require('../modules/events');
    const id = writeFeedback({
      sessionId: req.sessionId,
      userId:    req.userId,
      analysisId: analysis_id || null,
      rating:    rating ? parseInt(rating, 10) : null,
      comment:   comment || null,
      feedbackType: feedback_type || 'result_quality',
    });
    track('feedback_submitted', ctxFromReq(req, {
      analysisId: analysis_id,
      meta: { rating, feedbackType: feedback_type },
    }));
    res.json({ ok: true, id });
  } catch (e) {
    res.status(e.status || 500).json({ error: e.message });
  }
});

module.exports = router;
