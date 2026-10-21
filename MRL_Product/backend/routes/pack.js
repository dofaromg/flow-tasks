'use strict';
// routes/pack.js — ProductPack Generation API
// origin_signature: MrLiouWord
//
// POST /api/pack/generate  → 從 analysis_id 生成 ProductPack
// GET  /api/pack/:pack_id  → 取回已生成 pack
// GET  /api/pack            → 列出所有 pack（admin token 才可用）

const express = require('express');
const router  = express.Router();
const { authMiddleware } = require('../modules/identity');
const Packs   = require('../core/packs');
const { packToJson } = require('../core/packs/pack-exporter');
const config  = require('../config');
const logger  = require('../utils/logger');

// ── POST /api/pack/generate ───────────────────────────────────────
router.post('/generate', authMiddleware, async (req, res) => {
  const { analysis_id, mode } = req.body || {};

  if (!analysis_id) {
    return res.status(400).json({ error: 'analysis_id required' });
  }

  try {
    const pack = await Packs.generateFromAnalysis({
      analysisId: analysis_id,
      mode:       mode || 'website',
      sessionId:  req.sessionId,
      userId:     req.userId,
    });

    // 回傳 pack summary + pack_id（讓前端可用 pack_id 下載）
    res.json({
      ok:          true,
      pack_id:     pack.pack_id,
      title:       pack.title,
      mode:        pack.mode,
      mode_label:  pack.mode_label,
      summary:     pack.summary,
      template_id: pack.template_id,
      pages_count: pack.pages?.length,
      flows_count: pack.flows?.length,
      pack,          // 完整 pack
    });
  } catch (e) {
    logger.error('Pack generate error', { err: e.message });
    res.status(e.status || 500).json({ error: e.message });
  }
});

// ── GET /api/pack/:pack_id ────────────────────────────────────────
router.get('/:packId', authMiddleware, (req, res) => {
  const pack = Packs.getPack(req.params.packId);
  if (!pack) return res.status(404).json({ error: 'Pack not found' });
  res.json({ ok: true, pack });
});

// ── GET /api/pack/:pack_id/download ──────────────────────────────
// 回傳 JSON 檔案下載
router.get('/:packId/download', authMiddleware, (req, res) => {
  const pack = Packs.getPack(req.params.packId);
  if (!pack) return res.status(404).json({ error: 'Pack not found' });

  const json = packToJson(pack);
  res.setHeader('Content-Type', 'application/json');
  res.setHeader('Content-Disposition', `attachment; filename="${req.params.packId}.json"`);
  res.send(json);
});

// ── GET /api/pack（admin only）────────────────────────────────────
router.get('/', (req, res) => {
  const key = req.headers['x-admin-key'] || req.query.key;
  if (key !== config.adminKey) {
    return res.status(403).json({ error: 'Forbidden' });
  }
  const packs = Packs.getAllPacks(50);
  res.json({ ok: true, count: packs.length, packs });
});

module.exports = router;
