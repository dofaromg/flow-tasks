'use strict';
// modules/rules.js — 根據付款狀態與 plan_type 控制權限
// origin_signature: MrLiouWord

const { getDb } = require('./db');
const { isPast } = require('../utils/time');

/**
 * 判斷某 session 是否有有效訂閱
 */
function hasActiveSubscription(sessionId, userId) {
  const db = getDb();

  // 優先以 userId 查，若無則用 sessionId
  const sub = userId
    ? db.prepare(`
        SELECT * FROM subscriptions 
        WHERE user_id = ? AND status = 'active' AND expires_at > datetime('now')
        ORDER BY created_at DESC LIMIT 1
      `).get(userId)
    : db.prepare(`
        SELECT * FROM subscriptions 
        WHERE session_id = ? AND status = 'active' AND expires_at > datetime('now')
        ORDER BY created_at DESC LIMIT 1
      `).get(sessionId);

  return sub || null;
}

/**
 * 判斷某 analysis 是否已解鎖
 * 解鎖來源：單次付款 or 訂閱
 */
function canAccessFull(analysisId, sessionId, userId) {
  const db = getDb();

  // 1. 分析本身狀態
  const analysis = db.prepare('SELECT * FROM analyses WHERE id = ?').get(analysisId);
  if (!analysis) return { access: false, reason: 'analysis_not_found' };

  if (analysis.status === 'unlocked') {
    return { access: true, reason: 'unlocked_by_payment' };
  }

  // 2. 有有效訂閱
  const sub = hasActiveSubscription(sessionId, userId);
  if (sub) return { access: true, reason: 'active_subscription' };

  return { access: false, reason: 'not_paid' };
}

/**
 * 解鎖規則驗證（給 full_output 用）
 */
function enforceAccess(analysisId, sessionId, userId) {
  const result = canAccessFull(analysisId, sessionId, userId);
  if (!result.access) {
    const err = new Error('Payment required to access full result');
    err.status = 402;
    err.code = result.reason;
    throw err;
  }
  return result;
}

module.exports = { hasActiveSubscription, canAccessFull, enforceAccess };

// ── Owner 免費帳號（第十九包）────────────────────────────────────
const FREE_EMAILS = new Set([
  'z814241@gmail.com',  // MrLiouWord — origin_signature: MrLiouWord
]);

/**
 * 判斷是否為免費帳號（永久訂閱者）
 */
function isOwnerAccount(email) {
  return email && FREE_EMAILS.has(String(email).toLowerCase().trim());
}

/**
 * 補強 hasActiveSubscription：owner 帳號直接視為有效訂閱
 */
const _origHasActiveSub = hasActiveSubscription;
function hasActiveSubscriptionWithOwner(sessionId, userId, email) {
  // owner 帳號直接放行
  if (email && isOwnerAccount(email)) {
    return { id: 'owner', status: 'active', plan_type: 'owner', expires_at: '2099-12-31T00:00:00Z' };
  }
  return _origHasActiveSub(sessionId, userId);
}

module.exports.isOwnerAccount = isOwnerAccount;
module.exports.hasActiveSubscriptionWithOwner = hasActiveSubscriptionWithOwner;
