'use strict';
// MRL橋接轉譯中心 — origin_signature: MrLiouWord
const crypto = require('node:crypto');
const fs = require('node:fs');
const path = require('node:path');

function canonical(value) {
  if (Array.isArray(value)) return '[' + value.map(canonical).join(',') + ']';
  if (value !== null && typeof value === 'object') {
    return '{' + Object.keys(value).sort().map(k => JSON.stringify(k) + ':' + canonical(value[k])).join(',') + '}';
  }
  return JSON.stringify(value);
}
const hash = value => crypto.createHash('sha256').update(value).digest('hex');

class TranslationCenter {
  constructor(ledgerPath) {
    this.ledgerPath = ledgerPath;
    this.previous = 'GENESIS';
    this.sequence = 0;
    this.recent = [];
    this.lastError = null;
    if (ledgerPath && fs.existsSync(ledgerPath)) {
      for (const line of fs.readFileSync(ledgerPath, 'utf8').split('\n').filter(Boolean)) {
        const record = JSON.parse(line);
        const digest = record.record_sha256;
        delete record.record_sha256;
        if (record.sequence !== this.sequence || record.previous_sha256 !== this.previous || hash(canonical(record)) !== digest) {
          throw new Error('MRL bridge ledger integrity failure');
        }
        this.previous = digest;
        this.sequence++;
      }
    }
  }

  label(payloadDigest, payloadSize, context) {
    const record = {
      schema: 'MRL.BridgeTranslationCenter.v1', bridge_center: 'MRL橋接轉譯中心',
      mrl_affiliation: 'MRL', canonical_authority: 'Mr.liou', origin_signature: 'MrLiouWord',
      payload_origin_signature: context.payload_origin_signature || null,
      producer_persona: context.producer_persona || null,
      timestamp: new Date().toISOString(), event_id: crypto.randomUUID(),
      trace_id: context.trace_id, parent_ref: context.parent_ref || null,
      peer_trace_id: context.peer_trace_id || null, peer_trace_trust: 'unverified',
      source_ref: context.source_ref, destination_ref: context.destination_ref,
      direction: context.direction, status: context.status,
      http_status: context.http_status || null,
      payload_sha256: payloadDigest, payload_size: payloadSize, hash_scope: 'bytes',
      storage: this.ledgerPath ? 'append-only-file' : 'memory-only',
      sequence: this.sequence, previous_sha256: this.previous,
    };
    record.record_sha256 = hash(canonical(record));
    if (this.ledgerPath) {
      fs.mkdirSync(path.dirname(this.ledgerPath), { recursive: true });
      fs.appendFileSync(this.ledgerPath, JSON.stringify(record) + '\n', { encoding: 'utf8', flush: true });
    }
    this.sequence++;
    this.previous = record.record_sha256;
    this.recent.push(record);
    if (this.recent.length > 1024) this.recent.shift();
    return record;
  }

  middleware() {
    return (req, res, next) => {
      // Each boundary creates its own trace: client-provided MRL headers never
      // become an authority assertion. Request/response bytes remain untouched.
      const traceId = crypto.randomUUID();
      const input = crypto.createHash('sha256');
      const output = crypto.createHash('sha256');
      let inputSize = 0, outputSize = 0, inbound = null, recorded = false;
      const safeRecord = (...args) => {
        try { return this.label(...args); }
        catch (error) { this.lastError = error.code || 'AUDIT_APPEND_FAILED'; return null; }
      };
      const reserve = safeRecord(hash(Buffer.alloc(0)), 0, {
        trace_id: traceId, source_ref: 'external', destination_ref: 'MRL_Bridge',
        direction: 'external_to_mrl', status: 'started',
        peer_trace_id: typeof req.headers['x-mrl-trace-id'] === 'string' &&
          /^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$/i.test(req.headers['x-mrl-trace-id'])
          ? req.headers['x-mrl-trace-id'] : null,
      });
      res.setHeader('X-MRL-Affiliation', 'MRL');
      res.setHeader('X-MRL-Bridge-Center', 'MRL-Bridge-Translation-Center-v1');
      res.setHeader('X-MRL-Trace-Id', traceId);
      req.mrlBridge = { trace_id: traceId, bridge_center: 'MRL橋接轉譯中心' };
      if (!reserve) { res.statusCode = 503; res.end('MRL bridge audit unavailable'); return; }
      req.on('data', chunk => { input.update(chunk); inputSize += chunk.length; });
      req.once('end', () => {
        inbound = safeRecord(input.digest('hex'), inputSize, {
          trace_id: traceId, parent_ref: reserve.event_id,
          source_ref: 'external', destination_ref: 'MRL_Bridge',
          direction: 'external_to_mrl', status: 'received',
        });
      });
      const capture = (chunk, encoding) => {
        if (chunk === undefined || chunk === null || typeof chunk === 'function') return;
        const bytes = Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk, typeof encoding === 'string' ? encoding : undefined);
        output.update(bytes); outputSize += bytes.length;
      };
      const write = res.write;
      const end = res.end;
      res.write = function(chunk, encoding, callback) { capture(chunk, encoding); return write.apply(this, arguments); };
      res.end = function(chunk, encoding, callback) { capture(chunk, encoding); return end.apply(this, arguments); };
      const finish = status => {
        if (recorded) return;
        recorded = true;
        safeRecord(output.digest('hex'), outputSize, {
          trace_id: traceId, parent_ref: inbound ? inbound.event_id : reserve.event_id,
          source_ref: 'MRL_Bridge', destination_ref: 'external',
          direction: 'mrl_to_external', status, http_status: res.statusCode,
        });
      };
      res.once('finish', () => finish('sent'));
      res.once('close', () => finish('connection_closed'));
      next();
    };
  }
}

module.exports = { TranslationCenter };
