'use strict';
// modules/identity.js — 建立 session / user 身份
// origin_signature: MrLiouWord

const jwt = require('jsonwebtoken');
const { createHash } = require('crypto');
const { getDb } = require('./db');
const { uuid, token } = require('../utils/ids');
const { now, addDays } = require('../utils/time');
const config = require('../config');

// 第十九包：owner 帳號識別（lazy init 避免循環 require）
const FREE_OWNER_EMAILS = new Set(['z814241@gmail.com']);
function isOwner(email) {
  if (!email) return false;
  return FREE_OWNER_EMAILS.has(String(email).toLowerCase().trim());
}

/**
 * 建立訪客 session（無需 email）
 */
function createSession(userId = null, email = null) {
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
    { sessionId, userId, email: email || null },
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
  req.email     = payload.email  || null;   // 第十九包：owner 識別用
  next();
}

/**
 * 建立新 session 並回傳 token（登入用）
 */
function login(email) {
  const user = upsertUser(email);
  const sess = createSession(user.id, email);  // 把 email 帶入 JWT
  // 第十九包：isOwner = 包裝函式，在本檔頂部定義
  const owner = isOwner(email);  // 呼叫頂部的 isOwner wrapper
  return {
    ...sess,
    userId: user.id,
    email,
    has_subscription:      owner,
    subscription_expires:  owner ? '2099-12-31T00:00:00Z' : null,
    is_owner:              owner,
  };
}

module.exports = { createSession, verifyToken, authMiddleware, upsertUser, login };
