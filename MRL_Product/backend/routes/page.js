'use strict';
// routes/page.js — 頁面路由 + 頁面瀏覽事件追蹤
// origin_signature: MrLiouWord

const express = require('express');
const path = require('path');
const router = express.Router();
const { track } = require('../modules/events');
const { verifyToken } = require('../modules/identity');

const frontendDir = path.join(__dirname, '../../frontend');

// ── 追蹤 helper ───────────────────────────────────────────────────
function trackPage(eventName) {
  return (req, res, next) => {
    // 嘗試從 token 解出 session（非強制）
    const auth = req.headers['authorization'] || '';
    const tokenStr = auth.replace(/^Bearer\s+/i, '').trim();
    const payload = tokenStr ? verifyToken(tokenStr) : null;

    setImmediate(() => {
      track(eventName, {
        sessionId: payload?.sessionId || req.cookies?.mrl_sid || null,
        userId:    payload?.userId    || null,
        page:      req.path,
        ip:        req.ip,
        ua:        req.headers['user-agent'],
      });
    });
    next();
  };
}

// ── 頁面路由 ──────────────────────────────────────────────────────
router.get('/',           trackPage('page_view_home'),    (req, res) => res.sendFile('index.html',   { root: frontendDir }));
router.get('/index.html', trackPage('page_view_home'),    (req, res) => res.sendFile('index.html',   { root: frontendDir }));
router.get('/app.html',   trackPage('page_view_app'),     (req, res) => res.sendFile('app.html',     { root: frontendDir }));
router.get('/app',        trackPage('page_view_app'),     (req, res) => res.sendFile('app.html',     { root: frontendDir }));
router.get('/interface',  trackPage('page_view_interface'), (req, res) => res.sendFile('interface.html', { root: frontendDir }));
router.get('/interface.html', trackPage('page_view_interface'), (req, res) => res.sendFile('interface.html', { root: frontendDir }));
router.get('/pricing.html', trackPage('page_view_pricing'), (req, res) => res.sendFile('pricing.html', { root: frontendDir }));
router.get('/pricing',    trackPage('page_view_pricing'), (req, res) => res.sendFile('pricing.html', { root: frontendDir }));
router.get('/success.html', (req, res) => res.sendFile('success.html', { root: frontendDir }));
router.get('/cancel.html',  (req, res) => res.sendFile('cancel.html',  { root: frontendDir }));
router.get('/success',    (req, res) => res.sendFile('success.html', { root: frontendDir }));
router.get('/cancel',     (req, res) => res.sendFile('cancel.html',  { root: frontendDir }));
router.get('/product',    trackPage('page_view_product'), (req, res) => res.sendFile('product.html', { root: frontendDir }));
router.get('/product.html', trackPage('page_view_product'), (req, res) => res.sendFile('product.html', { root: frontendDir }));
router.get('/admin',      (req, res) => res.sendFile('admin.html',   { root: frontendDir }));
router.get('/admin.html', (req, res) => res.sendFile('admin.html',   { root: frontendDir }));

module.exports = router;
