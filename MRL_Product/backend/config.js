// config.js — MRL_Product_v1 系統設定
// origin_signature: MrLiouWord
'use strict';

require('dotenv').config();

const stripeMode = process.env.STRIPE_MODE || 'test';
if (!['test', 'live'].includes(stripeMode)) {
  console.error(`[MRL] FATAL: STRIPE_MODE 必須是 test 或 live，實際為: ${stripeMode}`);
  process.exit(1);
}

module.exports = {
  // 服務基本設定
  port: parseInt(process.env.PORT || '3000', 10),
  nodeEnv: process.env.NODE_ENV || 'development',
  baseUrl: process.env.BASE_URL || 'http://localhost:3000',

  // JWT
  jwtSecret: process.env.JWT_SECRET || 'mrl-dev-secret-change-in-production',
  jwtExpiry: process.env.JWT_EXPIRY || '7d',

  // SQLite
  dbPath: process.env.DB_PATH || './storage/db.sqlite',

  // Anthropic AI
  anthropicApiKey: process.env.ANTHROPIC_API_KEY || '',
  anthropicModel: process.env.ANTHROPIC_MODEL || 'claude-opus-4-5',

  // Stripe
  stripeMode,
  stripeSecretKey: process.env.STRIPE_SECRET_KEY || '',
  stripeWebhookSecret: process.env.STRIPE_WEBHOOK_SECRET || '',
  // 單次付款目前使用 price_data 動態建立 NT$299，不依賴固定 Price ID。
  stripePriceOnce: process.env.STRIPE_PRICE_ONCE || '',
  // 訂閱付款使用固定 Stripe Price ID。
  stripePriceSub: process.env.STRIPE_PRICE_SUB || '',

  // 產品設定
  product: {
    onceAmount: 29900,    // 分（NT$299）
    subAmount: 49900,     // 分（NT$499）
    currency: 'twd',
    partialRatio: 0.30,   // 前 30% 免費預覽
  },

  // 管理員
  adminKey: process.env.ADMIN_KEY || 'mrl-admin-dev',

  // Origin signature（不可變）
  originSignature: 'MrLiouWord',
};

// ── 啟動時 env 必填驗證 ─────────────────────────────────────────────
// production 模式下，缺少關鍵變數直接中止，不帶空 key 運行。
if (process.env.NODE_ENV === 'production') {
  const _required = [
    'JWT_SECRET',
    'ANTHROPIC_API_KEY',
    'STRIPE_MODE',
    'STRIPE_SECRET_KEY',
    'STRIPE_WEBHOOK_SECRET',
    'STRIPE_PRICE_SUB',
    'ADMIN_KEY',
  ];
  const _missing = _required.filter(
    k => !process.env[k] || process.env[k].startsWith('REPLACE')
  );
  if (_missing.length > 0) {
    console.error('[MRL] FATAL: 以下必填 env 變數未設定或仍為範本值：');
    _missing.forEach(k => console.error(`  - ${k}`));
    console.error('[MRL] 請編輯 .env 後重新啟動。origin_signature: MrLiouWord');
    process.exit(1);
  }
}

// ── Stripe test/live 防呆 ───────────────────────────────────────────
// 驗收與 staging 固定使用 test；只有商業 Gate 通過後才切 live。
const _stripeKey = process.env.STRIPE_SECRET_KEY || '';
if (_stripeKey) {
  const expectedPrefix = stripeMode === 'live' ? 'sk_live_' : 'sk_test_';
  if (!_stripeKey.startsWith(expectedPrefix)) {
    console.error(`[MRL] FATAL: STRIPE_MODE=${stripeMode} 但 STRIPE_SECRET_KEY 不是 ${expectedPrefix} 開頭。拒絕啟動以避免 test/live 接反。`);
    process.exit(1);
  }
}

module.exports.logLevel = process.env.LOG_LEVEL || 'info';
