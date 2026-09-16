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
  const sha256 = async (bytes) => Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', bytes)), byte => byte.toString(16).padStart(2, '0')).join('');

  function verifyLive(receipt) {
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
    if (!['ollama','llamacpp'].includes(receipt.backend)) failures.push('backend: unsupported');
    if (!Number.isInteger(receipt.model_artifact_size_bytes) || receipt.model_artifact_size_bytes < 1) failures.push('model_artifact_size_bytes: invalid');
    if (!isText(receipt.accepted_at) || Number.isNaN(Date.parse(receipt.accepted_at))) failures.push('accepted_at: invalid date-time');
    return failures;
  }

  function verifyRoutes(receipt) {
    const failures = [];
    if (receipt.schema !== 'MRL_APIWorks_Public_Route_Receipt_v1') failures.push('schema: unsupported');
    if (receipt.origin_signature !== 'MrLiouWord') failures.push('origin_signature: mismatch');
    if (!['PUBLIC_HTTPS','TEST_LOOPBACK'].includes(receipt.capture_mode)) failures.push('capture_mode: invalid');
    if (!hex40.test(receipt.probe_git_head || '')) failures.push('probe_git_head: invalid');
    if (!hex64.test(receipt.route_map_sha256 || '')) failures.push('route_map_sha256: invalid');
    if (!Array.isArray(receipt.routes) || receipt.routes.length < 1) failures.push('routes: empty');
    else receipt.routes.forEach((route, index) => {
      const expectedMatch = route.error == null && route.http_status === route.expected_status;
      if (route.status_match !== expectedMatch) failures.push(`routes[${index}].status_match: disagrees with observation`);
      if (!Number.isInteger(route.http_status) || route.http_status < 0 || route.http_status > 599) failures.push(`routes[${index}].http_status: invalid`);
      if (!hex64.test(route.response_sha256 || '')) failures.push(`routes[${index}].response_sha256: invalid`);
    });
    const allPass = Array.isArray(receipt.routes) && receipt.routes.length > 0 && receipt.routes.every(route => route.error == null && route.http_status === route.expected_status);
    const expectedGate = receipt.capture_mode === 'PUBLIC_HTTPS' ? (allPass ? 'PUBLIC_ROUTE_HTTP_PASS' : 'PUBLIC_ROUTE_HTTP_FAIL') : (allPass ? 'PUBLIC_ROUTE_TEST_PASS' : 'PUBLIC_ROUTE_TEST_FAIL');
    if (receipt.public_route_gate !== expectedGate) failures.push(`public_route_gate: expected ${expectedGate}`);
    return failures;
  }

  async function verifyReceipt() {
    const output = byId('verify-result');
    const receiptFile = byId('receipt-file').files[0];
    const modelFile = byId('model-file').files[0];
    if (!receiptFile) return setResult(output, false, 'FAIL｜請先選取 JSON 收據。');
    try {
      const receipt = JSON.parse(await receiptFile.text());
      let failures;
      if (receipt.schema === 'MRL_AI_Mother_Live_Acceptance_v1') failures = verifyLive(receipt);
      else if (receipt.schema === 'MRL_APIWorks_Public_Route_Receipt_v1') failures = verifyRoutes(receipt);
      else failures = ['schema: unknown receipt type'];
      if (modelFile) {
        if (receipt.schema !== 'MRL_AI_Mother_Live_Acceptance_v1') failures.push('model file: only valid with a live acceptance receipt');
        else {
          const digest = await sha256(await modelFile.arrayBuffer());
          if (digest !== receipt.model_artifact_sha256) failures.push('model file: SHA-256 mismatch');
          if (modelFile.size !== receipt.model_artifact_size_bytes) failures.push('model file: size mismatch');
        }
      }
      if (failures.length) setResult(output, false, `FAIL｜${failures.length} 個問題\n- ${failures.join('\n- ')}`);
      else setResult(output, true, `PASS｜${receipt.schema}\n結構與內部一致性通過${modelFile ? '；模型檔 hash／size 相符' : ''}。\n此結果不是作者、部署、付款或實際載入權重的獨立證明。`);
    } catch (error) { setResult(output, false, `FAIL｜無法解析：${error.message}`); }
  }

  async function checkStatus() {
    const output = byId('status-result');
    try {
      const root = new URL(byId('worker-url').value);
      if (root.protocol !== 'https:' || root.username || root.password || root.search || root.hash) throw new Error('只接受無帳密、無 query/fragment 的 HTTPS 根網址');
      const endpoint = new URL('/api/mrl/status', root);
      setResult(output, null, `檢查中｜${endpoint.origin}/api/mrl/status`);
      const response = await fetch(endpoint, {method:'GET',headers:{accept:'application/json'},cache:'no-store',redirect:'error'});
      const text = await response.text();
      if (!response.ok) throw new Error(`HTTP ${response.status}｜${text.slice(0,160)}`);
      const data = JSON.parse(text);
      if (!data || !isText(data.platform) || !isText(data.timestamp)) throw new Error('回應不是預期的 MRL status 結構');
      setResult(output, true, `PASS｜HTTP ${response.status}\nPlatform: ${data.platform}\nRuntime: ${data.canonical_runtime || '未提供'}\nTimestamp: ${data.timestamp}`);
    } catch (error) { setResult(output, false, `FAIL｜${error.message}\n這可能是 HTTP、CORS、路由或回應結構問題；不會改寫成成功。`); }
  }

  byId('verify-receipt').addEventListener('click', verifyReceipt);
  byId('check-status').addEventListener('click', checkStatus);
  window.MRLPages = { verifyLive, verifyRoutes };
})();
