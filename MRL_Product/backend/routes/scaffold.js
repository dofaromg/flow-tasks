'use strict';
// routes/scaffold.js — Scaffold Generation API
// origin_signature: MrLiouWord
//
// POST /api/scaffold/generate   → 從 pack_id 生成 scaffold
// GET  /api/scaffold/:id        → manifest
// GET  /api/scaffold/:id/files  → 檔案清單
// GET  /api/scaffold            → 所有 scaffolds（admin）

const express   = require('express');
const router    = express.Router();
const { authMiddleware } = require('../modules/identity');
const Scaffolds = require('../core/scaffolds');
const config    = require('../config');
const logger    = require('../utils/logger');

// ── POST /api/scaffold/generate ──────────────────────────────────
router.post('/generate', authMiddleware, async (req, res) => {
  const { pack_id } = req.body || {};
  if (!pack_id) return res.status(400).json({ error: 'pack_id required' });

  try {
    const result = await Scaffolds.generateFromPackId(pack_id);
    res.json({ ok: true, ...result });
  } catch (e) {
    logger.error('Scaffold generate error', { err: e.message });
    res.status(e.status || 500).json({ error: e.message });
  }
});

// ── GET /api/scaffold/:id ─────────────────────────────────────────
router.get('/:packId', authMiddleware, (req, res) => {
  const manifest = Scaffolds.getScaffold(req.params.packId);
  if (!manifest) return res.status(404).json({ error: 'Scaffold not found' });
  res.json({ ok: true, manifest });
});

// ── GET /api/scaffold/:id/files ───────────────────────────────────
router.get('/:packId/files', authMiddleware, (req, res) => {
  const files = Scaffolds.getScaffoldFiles(req.params.packId);
  if (!files) return res.status(404).json({ error: 'Scaffold not found' });
  res.json({ ok: true, pack_id: req.params.packId, file_count: files.length, files });
});

// ── GET /api/scaffold（admin only）───────────────────────────────
router.get('/', (req, res) => {
  const key = req.headers['x-admin-key'] || req.query.key;
  if (key !== config.adminKey) return res.status(403).json({ error: 'Forbidden' });
  const all = Scaffolds.getAllScaffolds();
  res.json({ ok: true, count: all.length, scaffolds: all });
});

module.exports = router;
