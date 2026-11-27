'use strict';
// modules/identity.js — 建立 session / user 身份
// origin_signature: MrLiouWord

const jwt = require('jsonwebtoken');
const { createHash, scryptSync, timingSafeEqual } = require('crypto');
const { getDb } = require('./db');
const { uuid, token } = require('../utils/ids');
const { now, addDays } = require('../utils/time');
const config = require('../config');

function verifyOwnerCredentials(email, password) {
  if (typeof email !== 'string' || typeof password !== 'string' || password.length < 12) return false;
  const parts = String(config.ownerPasswordScrypt || '').split(':');
  if (parts.length !== 2 || !/^[a-fA-F0-9]{32}$/.test(parts[0]) || !/^[a-fA-F0-9]{128}$/.test(parts[1])) return false;
  const actual = scryptSync(password, Buffer.from(parts[0], 'hex'), 64);
  return timingSafeEqual(actual, Buffer.from(parts[1], 'hex')) &&
    !!config.ownerEmail && email.trim().toLowerCase() === config.ownerEmail;
}

/**
 * 建立訪客 session（無需 email）
 */
function createSession(userId = null, email = null, ownerVerified = false) {
  const db = getDb();
  const sessionId = uuid();
  const rawToken = token(32);
  const tokenHash = createHash('sha256').update(rawToken).digest('hex');
  const expiresAt = addDays(30);

  db.prepare(`
    INSERT INTO sessions (id, user_id, token_hash, created_at, expires_at)
    VALUES (?, ?, ?, ?, ?)
  `).run(sessionId, userId, tokenHash, now(), expiresAt);

  // 發 JWT（第十九包：加 email 供 owner 識別）
  const jwtToken = jwt.sign(
    { sessionId, userId, email: email || null, ownerVerified: ownerVerified === true },
    config.jwtSecret,
    { expiresIn: config.jwtExpiry }
  );

  return { sessionId, token: jwtToken };
}

/**
 * 驗證 JWT token → 回傳 payload
 */
function verifyToken(jwtStr) {
  try {
    return jwt.verify(jwtStr, config.jwtSecret);
  } catch {
    return null;
  }
}

/**
 * 取得或建立使用者（by email）
 */
function upsertUser(email) {
  const db = getDb();
  let user = db.prepare('SELECT * FROM users WHERE email = ?').get(email);
  if (!user) {
    const id = uuid();
    db.prepare('INSERT INTO users (id, email, created_at) VALUES (?, ?, ?)')
      .run(id, email, now());
    user = db.prepare('SELECT * FROM users WHERE id = ?').get(id);
  }
  return user;
}

/**
 * Express middleware：從 Authorization Bearer 解 session
 */
function authMiddleware(req, res, next) {
  const header = req.headers['authorization'] || '';
  const tokenStr = header.replace(/^Bearer\s+/i, '').trim();

  if (!tokenStr) {
    // 允許匿名，建立新 session
    const sess = createSession();
    req.sessionId = sess.sessionId;
    req.userId = null;
    req.sessionToken = sess.token;
    return next();
  }

  const payload = verifyToken(tokenStr);
  if (!payload) {
    return res.status(401).json({ error: 'Invalid or expired token' });
  }

  req.sessionId = payload.sessionId;
  req.userId    = payload.userId || null;
  req.email = payload.email || null;
  req.isVerifiedOwner = payload.ownerVerified === true && !!config.ownerEmail && payload.email === config.ownerEmail;
  next();
}

/**
 * 建立新 session 並回傳 token（登入用）
 */
function login(email, password) {
  if (!verifyOwnerCredentials(email, password)) return null;
  const normalized = email.trim().toLowerCase();
  const user = upsertUser(normalized);
  return {
    ...createSession(user.id, normalized, true),
    userId: user.id, email: normalized,
    has_subscription: true,
    subscription_expires: '2099-12-31T00:00:00Z',
    is_owner: true,
  };
}

module.exports = { createSession, verifyToken, authMiddleware, upsertUser, login, verifyOwnerCredentials };
