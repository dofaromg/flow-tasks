'use strict';
// routes/deploypack.js — Deploy Pack API
// origin_signature: MrLiouWord

const express  = require('express');
const router   = express.Router();
const { authMiddleware } = require('../modules/identity');
const Deploy   = require('../core/deploy');
const config   = require('../config');
const logger   = require('../utils/logger');

// POST /api/deploypack/generate
router.post('/generate', authMiddleware, async (req, res) => {
  const { scaffold_id, pack_id } = req.body || {};
  const id = pack_id || scaffold_id;
  if (!id) return res.status(400).json({ error: 'pack_id (or scaffold_id) required' });

  try {
    const result = await Deploy.generateDeployPackFromScaffold(id);
    res.json({ ok: true, ...result });
  } catch (e) {
    logger.error('DeployPack generate error', { err: e.message });
    res.status(e.status || 500).json({ error: e.message });
  }
});

// GET /api/deploypack/:id
router.get('/:packId', authMiddleware, (req, res) => {
  const manifest = Deploy.getDeployPack(req.params.packId);
  if (!manifest) return res.status(404).json({ error: 'Deploy pack not found' });
  res.json({ ok: true, manifest });
});

// GET /api/deploypack/:id/validate
router.get('/:packId/validate', authMiddleware, (req, res) => {
  const v = Deploy.validatePack(req.params.packId);
  res.json({ ok: true, ...v });
});

// GET /api/deploypack/:id/files
router.get('/:packId/files', authMiddleware, (req, res) => {
  const files = Deploy.getDeployPackFiles(req.params.packId);
  if (!files) return res.status(404).json({ error: 'Deploy pack not found' });
  res.json({ ok: true, pack_id: req.params.packId, file_count: files.length, files });
});

// GET /api/deploypack — admin only
router.get('/', (req, res) => {
  const key = req.headers['x-admin-key'] || req.query.key;
  if (key !== config.adminKey) return res.status(403).json({ error: 'Forbidden' });
  res.json({ ok: true, packs: Deploy.getAllDeployPacks() });
});

module.exports = router;
