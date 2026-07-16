'use strict';
// backend/core/packs/product-pack.js
// MRL_ProductPack_Generator_v1 — Schema & Factory
// origin_signature: MrLiouWord
//
// ProductPack：針對一個具體問題所生成的最小產品交付包
// Layer A（Pack Spec）：結構化描述，可直接拿去實作或交付
// Layer B（Pack Scaffold）：未來擴展

const { uuid } = require('../../utils/ids');
const { now }  = require('../../utils/time');

// ── Pack Mode 定義 ────────────────────────────────────────────────
const PRODUCT_PACK_MODES = {
  website:  { id: 'website',  label: '做第一版網站',    emoji: '🌐' },
  mvp:      { id: 'mvp',      label: '做第一版產品',    emoji: '🚀' },
  payment:  { id: 'payment',  label: '做收費入口',      emoji: '💳' },
  converge: { id: 'converge', label: '產品收斂 / MVP', emoji: '🎯' },
};

// ── 標準頁面清單（product 線通用）─────────────────────────────────
const STANDARD_PRODUCT_PAGES = [
  { name: 'index',   purpose: '首頁 / 對外入口',   priority: 'high',   path: '/' },
  { name: 'app',     purpose: '問題輸入 / 結果展示', priority: 'high',   path: '/app' },
  { name: 'pricing', purpose: '方案與定價',         priority: 'high',   path: '/pricing' },
  { name: 'product', purpose: '主打 category 入口', priority: 'medium', path: '/product' },
  { name: 'success', purpose: '付款成功',           priority: 'high',   path: '/success' },
  { name: 'cancel',  purpose: '付款取消',           priority: 'medium', path: '/cancel' },
];

// ── 標準使用者旅程（product 線）───────────────────────────────────
const STANDARD_PRODUCT_FLOW = [
  { step: 1, name: 'landing',     description: '使用者進入首頁或專屬入口頁' },
  { step: 2, name: 'input',       description: '選擇 category / mode，輸入問題' },
  { step: 3, name: 'partial',     description: '免費顯示 partial_result（核心判斷 + 問題拆解）' },
  { step: 4, name: 'payment_cta', description: '顯示鎖定區塊，提示付費解鎖' },
  { step: 5, name: 'checkout',    description: '進入 Stripe Checkout（單次 NT$299 或月費 NT$499）' },
  { step: 6, name: 'unlock',      description: 'webhook → confirmation → ledger → result_unlock' },
  { step: 7, name: 'full_result', description: '顯示完整方案（核心判斷 / 範圍 / 執行順序 / 先不做）' },
  { step: 8, name: 'retention',   description: '升級月費提示 + 評分回饋 + 再分析入口' },
];

// ── Pack Schema ────────────────────────────────────────────────────
const PACK_SCHEMA = {
  pack_type:    'product',
  template_id:  'MRL_Delivery_Template_Product_v1',
  version:      '1.0',
  origin:       'MrLiouWord',
};

// ── Pack Factory ──────────────────────────────────────────────────

/**
 * 從 normalized analysis result 建立 ProductPack
 * @param {object} opts
 * @param {string}  opts.analysisId
 * @param {string}  opts.problemText
 * @param {object}  opts.normalizedResult  — Core_Generator 輸出
 * @param {object}  opts.rawResult         — AI 原始輸出
 * @param {string}  opts.mode              — website|mvp|payment|converge
 * @param {string}  [opts.sessionId]
 * @returns {object} ProductPack
 */
function buildProductPack({ analysisId, problemText, normalizedResult, rawResult, mode, sessionId }) {
  const packMode = PRODUCT_PACK_MODES[mode] || PRODUCT_PACK_MODES.website;

  // 從 result 抽取關鍵欄位
  const result = normalizedResult || rawResult || {};
  const summary = result.summary || result.core_judgment || '';
  const coreJudgment = result.core_judgment || result.summary || '';
  const scope = result.first_version_scope || result.directions || [];
  const steps = result.execution_steps || result.steps || [];
  const doVsNot = result.do_vs_not_do || result.priorities || [];
  const nextActions = result.next_actions || result.supplements || [];
  const warning = result.common_failures || result.warning || null;

  // 從 core_judgment 嘗試生成 title
  const title = _deriveTitle(coreJudgment || summary, mode);

  // 頁面清單（依 mode 調整 priority）
  const pages = _buildPages(mode);

  // 部署草案
  const deployment = _buildDeployment();

  // 定價模式（依 mode 推斷）
  const pricingModel = _buildPricingModel(mode);

  const pack_id = 'mrl_pack_' + uuid().replace(/-/g, '').slice(0, 12);

  return {
    pack_id,
    analysis_id:  analysisId,
    pack_type:    'product',
    template_id:  PACK_SCHEMA.template_id,
    category:     'product',
    mode:         packMode.id,
    mode_label:   packMode.label,
    title,
    summary,
    core_judgment:      coreJudgment,
    first_version_scope: Array.isArray(scope) ? scope : [scope],
    execution_steps:    Array.isArray(steps)  ? steps : [steps],
    do_vs_not_do:       Array.isArray(doVsNot) ? doVsNot : [doVsNot],
    next_actions:       Array.isArray(nextActions) ? nextActions : [nextActions],
    common_failures:    warning,
    pages,
    flows:        STANDARD_PRODUCT_FLOW,
    pricing_model: pricingModel,
    deployment,
    result:       normalizedResult || rawResult,
    meta: {
      pack_version:  PACK_SCHEMA.version,
      generated_at:  now(),
      problem_text:  problemText,
      session_id:    sessionId || null,
      origin:        PACK_SCHEMA.origin,
    },
  };
}

// ── Private Helpers ───────────────────────────────────────────────

function _deriveTitle(coreJudgment, mode) {
  const modeLabel = PRODUCT_PACK_MODES[mode]?.label || '產品方案';
  if (!coreJudgment) return `${modeLabel}（待命名）`;
  // 取前 20 字作為 title hint
  const hint = String(coreJudgment).slice(0, 20).replace(/[，。：:]/g, '').trim();
  return hint.length > 4 ? hint : modeLabel;
}

function _buildPages(mode) {
  return STANDARD_PRODUCT_PAGES.map(p => {
    // converge mode 不需要 product 專屬頁
    if (p.name === 'product' && mode === 'converge') {
      return { ...p, priority: 'low', note: 'converge mode 可暫緩' };
    }
    // payment mode 以 pricing 為核心
    if (p.name === 'pricing' && mode === 'payment') {
      return { ...p, priority: 'critical', note: '收費入口核心頁' };
    }
    return p;
  });
}

function _buildDeployment() {
  return {
    target:   'DL580',
    stack:    ['Node.js 20', 'SQLite', 'Docker', 'Nginx'],
    command:  'docker compose up -d --build',
    env:      [
      'ANTHROPIC_API_KEY',
      'STRIPE_SECRET_KEY',
      'STRIPE_WEBHOOK_SECRET',
      'STRIPE_PRICE_ONCE',
      'STRIPE_PRICE_SUB',
      'JWT_SECRET',
      'ADMIN_KEY',
      'BASE_URL',
    ],
    volumes: [
      '/opt/mrl_product_v1/storage:/app/storage',
      '/opt/mrl_product_v1/logs:/app/logs',
    ],
    ports: ['80:80', '443:443'],
    note:  '詳細步驟見 docs/deploy.md',
  };
}

function _buildPricingModel(mode) {
  const base = {
    currency:      'TWD',
    once_amount:   299,
    sub_amount:    499,
    sub_interval:  'monthly',
  };
  if (mode === 'payment') {
    return {
      ...base,
      primary: 'once',
      note: '收費入口模式，單次優先，用於快速驗證付費意願',
    };
  }
  return {
    ...base,
    primary: 'both',
    note: '單次適合試用，月費適合持續迭代',
  };
}

module.exports = {
  PRODUCT_PACK_MODES,
  STANDARD_PRODUCT_PAGES,
  STANDARD_PRODUCT_FLOW,
  PACK_SCHEMA,
  buildProductPack,
};
