// config.js — MRL_Product_v1 系統設定
// origin_signature: MrLiouWord
'use strict';

require('dotenv').config();

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
  stripeSecretKey: process.env.STRIPE_SECRET_KEY || '',
  stripeWebhookSecret: process.env.STRIPE_WEBHOOK_SECRET || '',
  stripePriceOnce: process.env.STRIPE_PRICE_ONCE || '',        // 單次 NT$299
  stripePriceSub: process.env.STRIPE_PRICE_SUB || '',          // 月費 NT$499

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
// production 模式下，缺少關鍵變數直接中止，不帶空 key 運行
if (process.env.NODE_ENV === 'production') {
  const _required = [
    'JWT_SECRET',
    'ANTHROPIC_API_KEY',
    'STRIPE_SECRET_KEY',
    'STRIPE_WEBHOOK_SECRET',
    'STRIPE_PRICE_ONCE',
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

module.exports.logLevel = process.env.LOG_LEVEL || 'info';
