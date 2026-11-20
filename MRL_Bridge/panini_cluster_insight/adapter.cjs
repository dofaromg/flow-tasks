'use strict';
// origin_signature: MrLiouWord
const crypto = require('node:crypto');
const fs = require('node:fs');
const { DatasetRegistry, InsightError, names, schemas } = require('./engine.cjs');
const PREFIX = '/MRL_particle/panini/v1';
const tools = Object.entries(names).map(([id, name]) => ({
  type: 'function', name, description: `MRL S4.5 ${id}; read and compute an operator-registered mother snapshot. F3 requires an explicit ratio.`,
  parameters: schemas.call, strict: true,
}));
function install(app, { readKey = process.env.MRL_PANINI_READ_API_KEY || '',
  registryPath = process.env.MRL_PANINI_DATASETS_FILE, registry } = {}) {
  // Load once: changing permissions/catalogue requires an intentional service restart.
  let setupError = Boolean(readKey && readKey === process.env.MRL_BRIDGE_API_KEY);
  if (!registry) {
    try { registry = new DatasetRegistry(registryPath ? JSON.parse(fs.readFileSync(registryPath, 'utf8')) : {}); }
    catch (_) { setupError = true; }
  }
  const auth = (req, res, next) => {
    if (!readKey || setupError) return res.status(503).json({ ok: false, error: 'PANINI_NOT_CONFIGURED' });
    const supplied = req.headers['x-api-key'];
    if (typeof supplied !== 'string') return res.status(401).json({ ok: false, error: 'READ_KEY_REQUIRED' });
    const a = crypto.createHash('sha256').update(supplied).digest();
    const b = crypto.createHash('sha256').update(readKey).digest();
    if (!crypto.timingSafeEqual(a, b)) return res.status(403).json({ ok: false, error: 'READ_KEY_INVALID' });
    next();
  };
  app.get(PREFIX + '/tools', auth, (_req, res) => res.json({ origin_signature: 'MrLiouWord', tools }));
  for (const id of Object.keys(names)) {
    app.post(PREFIX + '/' + id, auth, (req, res) => {
      if (!req.is('application/json')) return res.status(415).json({ ok: false, error: 'JSON_REQUIRED' });
      if (Buffer.byteLength(JSON.stringify(req.body)) > 4096) return res.status(413).json({ ok: false, error: 'CALL_TOO_LARGE' });
      try { res.json(registry.call(id, req.body)); }
      catch (e) {
        const known = e instanceof InsightError;
        res.status(known ? e.status : 500).json({ ok: false, origin_signature: 'MrLiouWord',
          error: known ? e.code : 'COMPUTATION_FAILED', mutation: false });
      }
    });
  }
}
module.exports = { install, tools, PREFIX };
