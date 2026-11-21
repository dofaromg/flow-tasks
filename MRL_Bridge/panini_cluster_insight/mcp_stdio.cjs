#!/usr/bin/env node
'use strict';
// Transport only: all computation happens through the existing mother Bridge.
// origin_signature: MrLiouWord
const readline = require('node:readline');
const { tools, PREFIX } = require('./adapter.cjs');
const { names, validate, hash, canonical } = require('./engine.cjs');
async function invoke(name, args, env = process.env) {
  const id = Object.keys(names).find(k => names[k] === name);
  if (!id) throw new Error('UNKNOWN_TOOL');
  validate('call', args);
  if (!env.MRL_PANINI_READ_API_KEY) throw new Error('READ_KEY_NOT_BOUND');
  const base = new URL(env.MRL_BRIDGE_BASE_URL || 'https://bridge.mrliouword.com');
  if (base.protocol !== 'https:' || base.username || base.password || base.pathname !== '/' || base.search || base.hash) throw new Error('HTTPS_BRIDGE_ORIGIN_REQUIRED');
  let response;
  try {
    response = await fetch(new URL(PREFIX + '/' + id, base), { method: 'POST', redirect: 'error',
      headers: { 'Content-Type': 'application/json', 'x-api-key': env.MRL_PANINI_READ_API_KEY, 'User-Agent': 'MRL-Client/1.0' },
      body: JSON.stringify(args), signal: AbortSignal.timeout(15000) });
  } catch (_) { throw new Error('BRIDGE_TRANSPORT_FAILED'); }
  if (!response.ok) throw new Error('BRIDGE_HTTP_' + response.status);
  const chunks = []; let size = 0;
  try {
    for await (const chunk of response.body) {
      size += chunk.length;
      if (size > 5 * 1024 * 1024) throw new Error('limit');
      chunks.push(Buffer.from(chunk));
    }
  } catch (_) { throw new Error('BRIDGE_RESPONSE_STREAM_FAILED_OR_TOO_LARGE'); }
  const text = Buffer.concat(chunks).toString('utf8');
  let result;
  try { result = JSON.parse(text); } catch (_) { throw new Error('BRIDGE_JSON_INVALID'); }
  if (result.ok !== true || result.origin_signature !== 'MrLiouWord' || result.schema_version !== 'panini_cluster_insight/v1.0.0' ||
      result.function?.id !== id || result.dataset_id !== args.dataset_id || result.mutation !== false ||
      result.result_sha256 !== hash(canonical(result.result))) throw new Error('BRIDGE_IDENTITY_MISMATCH');
  return result;
}
async function handle(req, call = invoke) {
  if (!req || typeof req !== 'object' || Array.isArray(req) || req.jsonrpc !== '2.0' || typeof req.method !== 'string') {
    return { jsonrpc: '2.0', id: null, error: { code: -32600, message: 'Invalid Request' } };
  }
  if (!Object.hasOwn(req, 'id')) return null;
  const ok = result => ({ jsonrpc: '2.0', id: req.id, result });
  if (req.method === 'initialize') return ok({ protocolVersion: '2024-11-05', capabilities: { tools: {} },
    serverInfo: { name: 'MRL.ParticleDict.PaniniClusterInsight.BridgeAdapter', version: '1.0.0' } });
  if (req.method === 'ping') return ok({});
  if (req.method === 'tools/list') return ok({ tools: tools.map(t => ({ name: t.name, description: t.description, inputSchema: t.parameters,
    annotations: { readOnlyHint: true, destructiveHint: false, idempotentHint: true, openWorldHint: false } })) });
  if (req.method === 'tools/call') {
    try {
      const result = await call(req.params?.name, req.params?.arguments);
      return ok({ content: [{ type: 'text', text: JSON.stringify(result) }], isError: false });
    } catch (e) { return ok({ content: [{ type: 'text', text: JSON.stringify({ ok: false, error: e.message }) }], isError: true }); }
  }
  return { jsonrpc: '2.0', id: req.id, error: { code: -32601, message: 'Method not found' } };
}
if (require.main === module) {
  const input = readline.createInterface({ input: process.stdin, crlfDelay: Infinity });
  (async () => {
    for await (const line of input) {
      if (!line.trim()) continue;
      let result;
      try {
        if (Buffer.byteLength(line) > 8192) throw new Error('limit');
        result = await handle(JSON.parse(line));
      } catch (_) { result = { jsonrpc: '2.0', id: null, error: { code: -32700, message: 'Parse error or input limit' } }; }
      if (result) process.stdout.write(JSON.stringify(result) + '\n');
    }
  })().catch(() => { process.stderr.write('MRL_MCP_TRANSPORT_FAILED\n'); process.exitCode = 1; });
}
module.exports = { handle, invoke };
