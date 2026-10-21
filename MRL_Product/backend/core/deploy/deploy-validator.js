'use strict';
// backend/core/deploy/deploy-validator.js
// MRL Deploy Pack Validator
// origin_signature: MrLiouWord
//
// 檢查 deploy pack 是否具備關鍵檔案，計算 runnable_score，產生驗收報告

const { listDeployFiles } = require('./deploy-writer');

// ── 必要檔案清單（缺一 score -= 10）─────────────────────────────
const REQUIRED_FILES = [
  { path: 'package.json',               weight: 15, desc: 'Node 依賴清單' },
  { path: 'backend/server.js',          weight: 15, desc: 'Express 應用入口' },
  { path: 'backend/config.js',          weight: 5,  desc: '環境設定' },
  { path: 'backend/routes/health.js',   weight: 10, desc: '/health endpoint' },
  { path: 'backend/modules/db-init.js', weight: 10, desc: 'SQLite 初始化' },
  { path: 'storage/schema.sql',         weight: 10, desc: 'DB schema' },
  { path: 'deploy/Dockerfile',          weight: 10, desc: 'Docker 容器定義' },
  { path: 'deploy/docker-compose.yml',  weight: 10, desc: 'Compose 服務設定' },
  { path: 'deploy/nginx.conf',          weight: 5,  desc: '反向代理設定' },
  { path: '.env.example',               weight: 5,  desc: '環境變數範本' },
  { path: 'deploy/health-check.sh',     weight: 5,  desc: '健康確認腳本' },
];

// ── 警告清單（缺 stub 不扣分，但提醒）────────────────────────────
const STUB_FILES = [
  { path: 'backend/routes/api.js',     desc: 'analyze API（stub — 需接 Core_Generator）' },
  { path: 'backend/routes/payment.js', desc: 'Stripe 付款（stub — 需配 Stripe）' },
  { path: 'backend/routes/webhook.js', desc: 'Stripe webhook（stub — 需配 Stripe）' },
  { path: 'frontend/index.html',       desc: '首頁（stub — 需補充文案）' },
  { path: 'README.md',                 desc: '說明文件' },
];

/**
 * 驗證 deploy pack
 */
function validateDeployPack(packId) {
  const files = listDeployFiles(packId);
  if (!files) {
    return {
      pack_id: packId,
      valid: false,
      runnable_score: 0,
      required_files_present: false,
      missing_files: REQUIRED_FILES.map(f => f.path),
      warnings: [],
      stub_files_present: [],
      stub_files_missing: STUB_FILES.map(f => f.path),
      can_compose_up: false,
      summary: 'Deploy pack not found',
    };
  }

  const fileSet = new Set(files);
  let score = 100;

  const missing = [];
  const present = [];
  for (const req of REQUIRED_FILES) {
    if (fileSet.has(req.path)) {
      present.push(req.path);
    } else {
      missing.push(req.path);
      score -= req.weight;
    }
  }

  score = Math.max(0, score);

  // stub 檔案狀態（提醒，不扣分）
  const stubPresent = [];
  const stubMissing = [];
  for (const s of STUB_FILES) {
    if (fileSet.has(s.path)) stubPresent.push(s.path);
    else stubMissing.push(s.path);
  }

  // 是否可 compose up（必要檔案都在才算）
  const composeReady = [
    'deploy/Dockerfile', 'deploy/docker-compose.yml', 'package.json',
    'backend/server.js', '.env.example',
  ].every(f => fileSet.has(f));

  // 警告
  const warnings = [];
  if (!fileSet.has('.env.example'))                   warnings.push('缺 .env.example，無法快速設定環境變數');
  if (!fileSet.has('deploy/health-check.sh'))         warnings.push('缺 health-check.sh，無法自動驗收健康狀態');
  if (!fileSet.has('backend/modules/db-init.js'))     warnings.push('缺 db-init.js，DB 初始化可能失敗');
  if (stubMissing.includes('backend/routes/api.js'))  warnings.push('backend/routes/api.js 缺失，/api/analyze 不可用');

  return {
    pack_id:                packId,
    valid:                  missing.length === 0,
    runnable_score:         score,
    required_files_present: missing.length === 0,
    required_present:       present,
    missing_files:          missing,
    stub_files_present:     stubPresent,
    stub_files_missing:     stubMissing,
    can_compose_up:         composeReady,
    warnings,
    total_files:            files.length,
    summary: score >= 80
      ? `✓ Ready (score: ${score}/100)${composeReady ? ' — can compose up' : ''}`
      : score >= 50
        ? `⚠ Partially ready (score: ${score}/100) — missing: ${missing.join(', ')}`
        : `✗ Not ready (score: ${score}/100) — critical files missing`,
  };
}

module.exports = { validateDeployPack, REQUIRED_FILES, STUB_FILES };
