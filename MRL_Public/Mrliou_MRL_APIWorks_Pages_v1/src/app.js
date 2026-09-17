(() => {
  'use strict';
  const hex40 = /^[0-9a-f]{40}$/;
  const hex64 = /^[0-9a-f]{64}$/;
  const mrlId = /^MRL_[A-Za-z0-9_.:-]+$/;
  const byId = (id) => document.getElementById(id);
  const setResult = (element, ok, message) => {
    element.className = `result ${ok === null ? 'neutral' : ok ? 'pass' : 'fail'}`;
    element.textContent = message;
  };
  const isText = (value) => typeof value === 'string' && value.trim().length > 0;
  // origin_signature: MrLiouWord. Hash private model bytes locally in bounded chunks.
  const MODEL_CHUNK_BYTES = 4 * 1024 * 1024;
  const SHA256_K = new Uint32Array([
    0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
    0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
    0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
    0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
    0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
    0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
    0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
    0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2,
  ]);
  const rotate = (value, bits) => (value >>> bits) | (value << (32 - bits));
  async function hashModelFile(file, progress = () => {}) {
    if (!Number.isSafeInteger(file.size) || file.size < 0) throw new Error('model file: invalid size');
    const state = new Uint32Array([0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19]);
    const words = new Uint32Array(64);
    const block = (bytes, offset) => {
      for (let i = 0; i < 16; i++) {
        const p = offset + i * 4;
        words[i] = (bytes[p] << 24) | (bytes[p + 1] << 16) | (bytes[p + 2] << 8) | bytes[p + 3];
      }
      for (let i = 16; i < 64; i++) {
        const x = words[i - 15], y = words[i - 2];
        words[i] = (words[i - 16] + (rotate(x, 7) ^ rotate(x, 18) ^ (x >>> 3)) + words[i - 7] + (rotate(y, 17) ^ rotate(y, 19) ^ (y >>> 10))) >>> 0;
      }
      let [a,b,c,d,e,f,g,h] = state;
      for (let i = 0; i < 64; i++) {
        const t1 = (h + (rotate(e, 6) ^ rotate(e, 11) ^ rotate(e, 25)) + ((e & f) ^ (~e & g)) + SHA256_K[i] + words[i]) >>> 0;
        const t2 = ((rotate(a, 2) ^ rotate(a, 13) ^ rotate(a, 22)) + ((a & b) ^ (a & c) ^ (b & c))) >>> 0;
        h=g; g=f; f=e; e=(d+t1)>>>0; d=c; c=b; b=a; a=(t1+t2)>>>0;
      }
      [a,b,c,d,e,f,g,h].forEach((value, i) => { state[i] = (state[i] + value) >>> 0; });
    };
    let tail = new Uint8Array(0);
    for (let offset = 0; offset < file.size; offset += MODEL_CHUNK_BYTES) {
      const end = Math.min(offset + MODEL_CHUNK_BYTES, file.size);
      const bytes = new Uint8Array(await file.slice(offset, end).arrayBuffer());
      if (bytes.length !== end - offset) throw new Error('model file: short read');
      const complete = bytes.length - bytes.length % 64;
      for (let p = 0; p < complete; p += 64) block(bytes, p);
      tail = bytes.slice(complete);
      progress(end, file.size);
      await new Promise(resolve => setTimeout(resolve, 0));
    }
    const final = new Uint8Array(tail.length < 56 ? 64 : 128);
    final.set(tail); final[tail.length] = 0x80;
    new DataView(final.buffer).setBigUint64(final.length - 8, BigInt(file.size) * 8n, false);
    for (let p = 0; p < final.length; p += 64) block(final, p);
    return Array.from(state, value => value.toString(16).padStart(8, '0')).join('');
  }

  function isLoopbackEndpoint(value) {
    // Check the original spelling too: WHATWG URL normalizes 127.1/decimal hosts.
    if (typeof value !== 'string' || /[\s\\]/.test(value) || !/^https?:\/\/(localhost|127\.0\.0\.1|\[::1\])(?::[0-9]+)?(?:\/[^?#]*)?$/i.test(value)) return false;
    try {
      const url = new URL(value);
      return ['http:', 'https:'].includes(url.protocol) && ['localhost', '127.0.0.1', '[::1]'].includes(url.hostname) && !url.username && !url.password && !url.search && !url.hash;
    } catch { return false; }
  }

  function verifyLive(receipt) {
    if (!receipt || typeof receipt !== 'object' || Array.isArray(receipt)) return ['root: expected object'];
    const failures = [];
    const exact = {
      schema: 'MRL_AI_Mother_Live_Acceptance_v1', canonical_id: 'MRL_AI_Mother_Autonomous_Runtime_Baseline_v1',
      origin_signature: 'MrLiouWord', model_sha256_verified: true, health_ready: true,
      external_model_disconnected: true, acceptance_gate: 'MRL_AI_MOTHER_AUTONOMOUS_RUNTIME_ACCEPTANCE_PASS',
    };
    for (const [key, value] of Object.entries(exact)) if (receipt[key] !== value) failures.push(`${key}: expected ${value}`);
    if (!hex40.test(receipt.git_head || '')) failures.push('git_head: invalid SHA-1');
    for (const key of ['model_release_manifest_sha256','model_artifact_sha256','memory_chain_head','evidence_chain_head','passport_hash','return_anchor','evidence_ref','request_sha256','result_sha256']) if (!hex64.test(receipt[key] || '')) failures.push(`${key}: invalid SHA-256`);
    for (const key of ['hardware_id','model_release_id','operator_id']) if (!mrlId.test(receipt[key] || '')) failures.push(`${key}: invalid MRL identifier`);
    for (const key of ['runtime_id','model','model_endpoint']) if (!isText(receipt[key])) failures.push(`${key}: required`);
    if (!isLoopbackEndpoint(receipt.model_endpoint)) failures.push('model_endpoint: HTTP(S) loopback without credentials/query/fragment required');
    if (!['ollama','llamacpp'].includes(receipt.backend)) failures.push('backend: unsupported');
    if (!Number.isInteger(receipt.model_artifact_size_bytes) || receipt.model_artifact_size_bytes < 1) failures.push('model_artifact_size_bytes: invalid');
    if (!isText(receipt.accepted_at) || Number.isNaN(Date.parse(receipt.accepted_at))) failures.push('accepted_at: invalid date-time');
    return failures;
  }

  function verifyRoutes(receipt) {
    if (!receipt || typeof receipt !== 'object' || Array.isArray(receipt)) return ['root: expected object'];
    const failures = [];
    if (receipt.schema !== 'MRL_APIWorks_Public_Route_Receipt_v1') failures.push('schema: unsupported');
    if (receipt.origin_signature !== 'MrLiouWord') failures.push('origin_signature: mismatch');
    if (!['PUBLIC_HTTPS','TEST_LOOPBACK'].includes(receipt.capture_mode)) failures.push('capture_mode: invalid');
    if (!hex40.test(receipt.probe_git_head || '')) failures.push('probe_git_head: invalid');
    if (!hex64.test(receipt.route_map_sha256 || '')) failures.push('route_map_sha256: invalid');
    if (!Array.isArray(receipt.routes) || receipt.routes.length < 1) failures.push('routes: empty');
    else receipt.routes.forEach((route, index) => {
      if (!route || typeof route !== 'object' || Array.isArray(route)) { failures.push(`routes[${index}]: expected object`); return; }
      const expectedMatch = route.error === null && route.http_status !== 0 && route.http_status === route.expected_status;
      if (route.status_match !== expectedMatch) failures.push(`routes[${index}].status_match: disagrees with observation`);
      if (!Number.isInteger(route.expected_status) || route.expected_status < 100 || route.expected_status > 599) failures.push(`routes[${index}].expected_status: invalid`);
      if (!Number.isInteger(route.http_status) || (route.http_status !== 0 && (route.http_status < 100 || route.http_status > 599))) failures.push(`routes[${index}].http_status: invalid`);
      if (route.http_status === 0 && (!isText(route.error) || route.response_size_bytes !== 0)) failures.push(`routes[${index}]: transport failure requires error and zero response bytes`);
      if (!hex64.test(route.response_sha256 || '')) failures.push(`routes[${index}].response_sha256: invalid`);
    });
    const allPass = Array.isArray(receipt.routes) && receipt.routes.length > 0 && receipt.routes.every(route => route && Number.isInteger(route.http_status) && route.http_status >= 100 && route.http_status <= 599 && route.error === null && route.http_status === route.expected_status);
    const expectedGate = receipt.capture_mode === 'PUBLIC_HTTPS' ? (allPass ? 'PUBLIC_ROUTE_HTTP_PASS' : 'PUBLIC_ROUTE_HTTP_FAIL') : (allPass ? 'PUBLIC_ROUTE_TEST_PASS' : 'PUBLIC_ROUTE_TEST_FAIL');
    if (receipt.public_route_gate !== expectedGate) failures.push(`public_route_gate: expected ${expectedGate}`);
    return failures;
  }

  async function verifyReceipt() {
    const output = byId('verify-result');
    const receiptFile = byId('receipt-file').files[0];
    const modelFile = byId('model-file').files[0];
    if (!receiptFile) return setResult(output, false, 'FAIL｜請先選取 JSON 收據。');
    byId('verify-receipt').disabled = true;
    try {
      const receipt = JSON.parse(await receiptFile.text());
      let failures;
      if (receipt.schema === 'MRL_AI_Mother_Live_Acceptance_v1') failures = verifyLive(receipt);
      else if (receipt.schema === 'MRL_APIWorks_Public_Route_Receipt_v1') failures = verifyRoutes(receipt);
      else failures = ['schema: unknown receipt type'];
      if (modelFile) {
        if (receipt.schema !== 'MRL_AI_Mother_Live_Acceptance_v1') failures.push('model file: only valid with a live acceptance receipt');
        else {
          if (modelFile.size !== receipt.model_artifact_size_bytes) failures.push('model file: size mismatch');
          if (!failures.length) {
            const digest = await hashModelFile(modelFile, (done, total) => setResult(output, null, `核對中｜${Math.floor(done / total * 100)}%｜模型僅在本機分塊讀取，不上傳。`));
            if (digest !== receipt.model_artifact_sha256) failures.push('model file: SHA-256 mismatch');
          }
        }
      }
      if (failures.length) setResult(output, false, `FAIL｜${failures.length} 個問題\n- ${failures.join('\n- ')}`);
      else setResult(output, true, `PASS｜${receipt.schema}\n結構與內部一致性通過${modelFile ? '；模型檔 hash／size 相符' : ''}。\n此結果不是作者、部署、付款或實際載入權重的獨立證明。`);
    } catch (error) { setResult(output, false, `FAIL｜無法解析：${error.message}`); }
    finally { byId('verify-receipt').disabled = false; }
  }

  async function checkStatus() {
    const output = byId('status-result');
    try {
      const root = new URL(byId('worker-url').value);
      if (root.protocol !== 'https:' || root.username || root.password || root.search || root.hash) throw new Error('只接受無帳密、無 query/fragment 的 HTTPS 根網址');
      const endpoint = new URL('/api/mrl/status', root);
      setResult(output, null, `檢查中｜${endpoint.origin}/api/mrl/status`);
      const response = await fetch(endpoint, {method:'GET',headers:{accept:'application/json'},credentials:'omit',cache:'no-store',redirect:'error'});
      const text = await response.text();
      if (!response.ok) throw new Error(`HTTP ${response.status}｜${text.slice(0,160)}`);
      const data = JSON.parse(text);
      if (!data || !isText(data.platform) || !isText(data.timestamp)) throw new Error('回應不是預期的 MRL status 結構');
      setResult(output, true, `PASS｜HTTP ${response.status}\nPlatform: ${data.platform}\nRuntime: ${data.canonical_runtime || '未提供'}\nTimestamp: ${data.timestamp}`);
    } catch (error) { setResult(output, false, `FAIL｜${error.message}\n這可能是 HTTP、CORS、路由或回應結構問題；不會改寫成成功。`); }
  }

  byId('verify-receipt').addEventListener('click', verifyReceipt);
  byId('check-status').addEventListener('click', checkStatus);
  window.MRLPages = { verifyLive, verifyRoutes, hashModelFile, MODEL_CHUNK_BYTES };
})();
