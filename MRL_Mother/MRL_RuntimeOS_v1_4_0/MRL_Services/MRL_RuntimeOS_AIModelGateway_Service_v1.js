const http = require('http');
const https = require('https');
const fs = require('fs');
const path = require('path');

function MRL_jsonRequest(urlString, payload, headers = {}, timeoutMs = 30000) {
  return new Promise((resolve, reject) => {
    const url = new URL(urlString);
    const lib = url.protocol === 'https:' ? https : http;
    const body = payload === null ? '' : JSON.stringify(payload);
    const req = lib.request({
      method: payload === null ? 'GET' : 'POST',
      hostname: url.hostname,
      port: url.port || (url.protocol === 'https:' ? 443 : 80),
      path: url.pathname + url.search,
      headers: {
        'content-type': 'application/json',
        'content-length': Buffer.byteLength(body),
        ...headers,
      },
      timeout: timeoutMs,
    }, (res) => {
      let data = '';
      res.on('data', c => data += c);
      res.on('end', () => {
        try { resolve({ statusCode: res.statusCode, body: data ? JSON.parse(data) : {} }); }
        catch (e) { resolve({ statusCode: res.statusCode, body: data }); }
      });
    });
    req.on('timeout', () => { req.destroy(new Error('MRL_AI_GATEWAY_TIMEOUT')); });
    req.on('error', reject);
    if (body) req.write(body);
    req.end();
  });
}

class MRLRuntimeOSAIModelGatewayService {
  constructor(root, options = {}) {
    this.root = root;
    this.ollamaHost = options.ollamaHost || process.env.OLLAMA_HOST || 'http://127.0.0.1:11434';
    this.openAIBaseURL = options.openAIBaseURL || process.env.MRL_OPENAI_COMPAT_BASE_URL || '';
    this.openAIAPIKey = options.openAIAPIKey || process.env.MRL_OPENAI_COMPAT_API_KEY || '';
    this.defaultModel = options.defaultModel || process.env.MRL_AI_MODEL || 'llama3.2:3b';
    this.origin_signature = 'MrLiouWord';
  }

  describe() {
    return {
      origin_signature: this.origin_signature,
      product: 'MRL_RuntimeOS_EnterpriseRuntimePlatform_CoreExecutable_v1_4_0',
      service: 'MRL_RuntimeOS_AIModelGateway_Service_v1',
      supported_backends: ['ollama', 'openai_compatible'],
      ollama_host: this.ollamaHost,
      openai_compatible_configured: Boolean(this.openAIBaseURL && this.openAIAPIKey),
      default_model: this.defaultModel,
      truth_status: 'real_connector; model availability depends on configured runtime host'
    };
  }

  async health() {
    const result = { ...this.describe(), live: {} };
    try {
      const r = await MRL_jsonRequest(`${this.ollamaHost}/api/tags`, null, {}, 3000);
      result.live.ollama = { reachable: r.statusCode >= 200 && r.statusCode < 500, statusCode: r.statusCode, models: r.body.models || [] };
    } catch (e) {
      result.live.ollama = { reachable: false, error: e.message };
    }
    return result;
  }

  async listModels(backend = 'ollama') {
    if (backend === 'ollama') {
      const r = await MRL_jsonRequest(`${this.ollamaHost}/api/tags`, null, {}, 10000);
      return { origin_signature: this.origin_signature, backend, statusCode: r.statusCode, models: r.body.models || [] };
    }
    if (backend === 'openai_compatible') {
      if (!this.openAIBaseURL || !this.openAIAPIKey) throw new Error('MRL_OPENAI_COMPAT_NOT_CONFIGURED');
      const r = await MRL_jsonRequest(`${this.openAIBaseURL.replace(/\/$/,'')}/models`, null, { authorization: `Bearer ${this.openAIAPIKey}` }, 10000);
      return { origin_signature: this.origin_signature, backend, statusCode: r.statusCode, models: r.body.data || r.body.models || [] };
    }
    throw new Error(`MRL_UNKNOWN_AI_BACKEND:${backend}`);
  }

  async generate({ prompt, model, backend = 'ollama', system = '', stream = false }) {
    if (!prompt) throw new Error('MRL_AI_PROMPT_REQUIRED');
    const selectedModel = model || this.defaultModel;
    if (backend === 'ollama') {
      const r = await MRL_jsonRequest(`${this.ollamaHost}/api/generate`, {
        model: selectedModel,
        prompt: system ? `${system}\n\n${prompt}` : prompt,
        stream: Boolean(stream)
      }, {}, 120000);
      return {
        origin_signature: this.origin_signature,
        service: 'MRL_RuntimeOS_AIModelGateway_Service_v1',
        backend,
        model: selectedModel,
        statusCode: r.statusCode,
        output: r.body.response || r.body.output || r.body,
        raw: r.body
      };
    }
    if (backend === 'openai_compatible') {
      if (!this.openAIBaseURL || !this.openAIAPIKey) throw new Error('MRL_OPENAI_COMPAT_NOT_CONFIGURED');
      const r = await MRL_jsonRequest(`${this.openAIBaseURL.replace(/\/$/,'')}/chat/completions`, {
        model: selectedModel,
        messages: [
          ...(system ? [{ role: 'system', content: system }] : []),
          { role: 'user', content: prompt }
        ],
        stream: false
      }, { authorization: `Bearer ${this.openAIAPIKey}` }, 120000);
      return {
        origin_signature: this.origin_signature,
        service: 'MRL_RuntimeOS_AIModelGateway_Service_v1',
        backend,
        model: selectedModel,
        statusCode: r.statusCode,
        output: r.body.choices?.[0]?.message?.content || r.body,
        raw: r.body
      };
    }
    throw new Error(`MRL_UNKNOWN_AI_BACKEND:${backend}`);
  }
}

module.exports = { MRLRuntimeOSAIModelGatewayService, MRL_jsonRequest };
