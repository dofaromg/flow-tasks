'use strict';
// modules/ledger.js — 帳本，唯一真相層
// origin_signature: MrLiouWord
// 規則：只寫入，不修改，不刪除（Liou Closure Law: NO_DELETE + ADDITIVE_RESOLUTION）

const { getDb } = require('./db');
const { uuid } = require('../utils/ids');
const { now } = require('../utils/time');
const logger = require('../utils/logger');
const config = require('../config');

const EVENT_TYPES = [
  'payment_success',
  'order_paid',
  'result_unlock',
  'sub_activated',
  'sub_expired',
  'sub_renewed',
  'refund',
  'analysis_created',
  'error',
];

/**
 * 寫入帳本事件（不可修改）
 */
function writeEvent({ eventType, analysisId, orderId, paymentId, sessionId, amount, meta, status = 'ok' }) {
  if (!EVENT_TYPES.includes(eventType)) {
    logger.warn('Unknown ledger event_type', { eventType });
  }

  const db = getDb();
  const id = uuid();

  db.prepare(`
    INSERT INTO ledger (id, event_type, analysis_id, order_id, payment_id, session_id, amount, status, meta_json, origin_sig, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
  `).run(
    id,
    eventType,
    analysisId || null,
    orderId || null,
    paymentId || null,
    sessionId || null,
    amount || null,
    status,
    meta ? JSON.stringify(meta) : null,
    config.originSignature,
    now()
  );

  logger.info('Ledger written', { id, eventType, orderId });
  return id;
}

/**
 * 查詢帳本（管理用）
 */
function queryLedger({ limit = 50, offset = 0, eventType, orderId } = {}) {
  const db = getDb();
  let sql = 'SELECT * FROM ledger WHERE 1=1';
  const params = [];

  if (eventType) { sql += ' AND event_type = ?'; params.push(eventType); }
  if (orderId)   { sql += ' AND order_id = ?';   params.push(orderId); }

  sql += ' ORDER BY created_at DESC LIMIT ? OFFSET ?';
  params.push(limit, offset);

  return db.prepare(sql).all(...params);
}

/**
 * 確認某訂單是否已有解鎖事件（防重複解鎖）
 */
function hasUnlockEvent(orderId) {
  const row = getDb().prepare(`
    SELECT id FROM ledger WHERE order_id = ? AND event_type = 'result_unlock' LIMIT 1
  `).get(orderId);
  return !!row;
}

module.exports = { writeEvent, queryLedger, hasUnlockEvent };
