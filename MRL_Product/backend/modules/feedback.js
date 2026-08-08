'use strict';
// modules/feedback.js — 使用者回饋 + 錯誤記錄
// origin_signature: MrLiouWord

const { getDb } = require('./db');
const { uuid } = require('../utils/ids');
const { now } = require('../utils/time');
const logger = require('../utils/logger');

// ── 使用者回饋 ────────────────────────────────────────────────────

/**
 * 寫入使用者回饋
 * @param {object} p
 * @param {string} p.sessionId
 * @param {string} [p.userId]
 * @param {string} [p.analysisId]
 * @param {number} [p.rating]       1–5
 * @param {string} [p.comment]
 * @param {string} [p.feedbackType] general|result_quality|pricing
 * @param {object} [p.meta]
 */
function writeFeedback({ sessionId, userId, analysisId, rating, comment, feedbackType, meta }) {
  const db = getDb();
  const id = uuid();

  if (rating !== undefined && rating !== null) {
    const r = parseInt(rating, 10);
    if (r < 1 || r > 5) throw Object.assign(new Error('rating 必須為 1–5'), { status: 400 });
  }

  db.prepare(`
    INSERT INTO feedback (id, session_id, user_id, analysis_id, rating, comment, feedback_type, meta_json, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
  `).run(
    id,
    sessionId || null,
    userId    || null,
    analysisId || null,
    rating    ?? null,
    comment   ? String(comment).slice(0, 2000) : null,
    feedbackType || 'general',
    meta ? JSON.stringify(meta) : null,
    now()
  );

  logger.debug('Feedback written', { id, rating, feedbackType });
  return id;
}

/**
 * 取得回饋摘要（管理用）
 */
function getFeedbackSummary() {
  const db = getDb();
  const total    = db.prepare('SELECT COUNT(*) as c FROM feedback').get().c;
  const avgRating = db.prepare('SELECT ROUND(AVG(rating),2) as a FROM feedback WHERE rating IS NOT NULL').get().a;
  const byRating = db.prepare(`
    SELECT rating, COUNT(*) as count FROM feedback
    WHERE rating IS NOT NULL GROUP BY rating ORDER BY rating
  `).all();

  return { total, avgRating, byRating };
}

/**
 * 列出最近回饋
 */
function recentFeedback(limit = 30) {
  return getDb().prepare(`
    SELECT id, session_id, analysis_id, rating, comment, feedback_type, created_at
    FROM feedback ORDER BY created_at DESC LIMIT ?
  `).all(limit);
}

// ── 錯誤記錄 ──────────────────────────────────────────────────────

/**
 * 記錄錯誤（非阻塞，失敗不影響主流程）
 */
function logError({ errorType, message, stack, sessionId, analysisId, orderId, context }) {
  try {
    const db = getDb();
    db.prepare(`
      INSERT INTO error_logs (id, error_type, message, stack, session_id, analysis_id, order_id, context_json, created_at)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    `).run(
      uuid(),
      errorType || 'server_error',
      message   ? String(message).slice(0, 1000) : null,
      stack     ? String(stack).slice(0, 3000)   : null,
      sessionId  || null,
      analysisId || null,
      orderId    || null,
      context ? JSON.stringify(context) : null,
      now()
    );
  } catch (e) {
    logger.debug('Error log write failed', { err: e.message });
  }
}

/**
 * 列出最近錯誤
 */
function recentErrors(limit = 50) {
  return getDb().prepare(`
    SELECT id, error_type, message, session_id, analysis_id, created_at
    FROM error_logs ORDER BY created_at DESC LIMIT ?
  `).all(limit);
}

/**
 * 近 N 日錯誤統計
 */
function errorStats(days = 7) {
  const db = getDb();
  return db.prepare(`
    SELECT error_type, COUNT(*) as count
    FROM error_logs
    WHERE created_at >= datetime('now', '-${days} days')
    GROUP BY error_type
    ORDER BY count DESC
  `).all();
}

module.exports = { writeFeedback, getFeedbackSummary, recentFeedback, logError, recentErrors, errorStats };
