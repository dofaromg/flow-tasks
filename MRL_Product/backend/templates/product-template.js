'use strict';
// backend/templates/product-template.js
// MRL_Delivery_Template_Product_v1
// origin_signature: MrLiouWord
//
// 三層結構：
//   Data Layer   — 語義欄位定義（section names）
//   Render Layer — 每個欄位對應的前端渲染角色
//   Style Role   — 視覺角色定義（與前端 CSS class 解耦）

// ── Template Schema（Data Layer）────────────────────────────────────
const TEMPLATE_SCHEMA = {
  template_id: 'MRL_Delivery_Template_Product_v1',
  category:    'product',
  version:     '1.0',
  origin:      'MrLiouWord',
  description: '第一版產品 / 網站方案交付模板',

  // 區塊正式名稱（語義欄位）
  sections: [
    'core_judgment',        // 核心判斷：第一版真正該做的事
    'problem_breakdown',    // 問題拆解：卡點分析
    'first_version_scope',  // 第一版範圍：包含 / 不包含什麼
    'execution_steps',      // 執行順序：先做 A → 再做 B
    'do_vs_not_do',         // 先做 vs 先不做
    'next_actions',         // 下一步建議
    'common_failures',      // 常見失敗原因（warning）
    'delivery_footer',      // 交付說明 footer
  ],

  // 各欄位的 AI 來源欄位對應
  ai_field_map: {
    core_judgment:       'summary',
    problem_breakdown:   'breakdown',
    first_version_scope: 'directions',
    execution_steps:     'steps',
    do_vs_not_do:        'priorities',
    next_actions:        'supplements',
    common_failures:     'warning',
    delivery_footer:     null,   // 前端靜態生成
  },

  // 各欄位顯示標籤
  labels: {
    core_judgment:       '核心判斷',
    problem_breakdown:   '問題拆解',
    first_version_scope: '第一版範圍建議',
    execution_steps:     '執行順序',
    do_vs_not_do:        '先做 vs 先不做',
    next_actions:        '下一步建議',
    common_failures:     '常見失敗原因',
  },

  // 各欄位的樣式角色（Style Role Layer）
  style_roles: {
    core_judgment:       'accent',          // 金色強調
    problem_breakdown:   'doc_section',     // 標準文件段
    first_version_scope: 'doc_section',
    execution_steps:     'step_list',       // 有序執行清單
    do_vs_not_do:        'contrast_warning',// 對比警示
    next_actions:        'doc_section',
    common_failures:     'failure_warning', // 失敗警示
    delivery_footer:     'footer_cta',      // 交付 footer
  },

  // 各欄位的 block type（給 renderer 用）
  block_types: {
    core_judgment:       'text',
    problem_breakdown:   'list',
    first_version_scope: 'list',
    execution_steps:     'numbered',
    do_vs_not_do:        'list',
    next_actions:        'list',
    common_failures:     'text',
    delivery_footer:     'footer',
  },
};

// ── Normalize（AI output → Template Data）───────────────────────────
/**
 * 把 AI 原始輸出映射成 product template 標準欄位
 * @param {object} rawResult — ai.js 輸出的原始物件
 * @returns {object} normalizedData — template section 欄位
 */
function normalizeProductResult(rawResult) {
  if (!rawResult) return null;

  const map = TEMPLATE_SCHEMA.ai_field_map;
  const normalized = {
    _template_id: TEMPLATE_SCHEMA.template_id,
    _version:     TEMPLATE_SCHEMA.version,
    _normalized:  true,
  };

  // 逐欄位映射
  for (const [section, aiField] of Object.entries(map)) {
    if (aiField === null) {
      normalized[section] = null;  // 前端靜態生成的欄位
      continue;
    }
    const val = rawResult[aiField];
    // 空值保護：確保 list 欄位是陣列
    const blockType = TEMPLATE_SCHEMA.block_types[section];
    if (blockType === 'list' || blockType === 'numbered') {
      normalized[section] = Array.isArray(val) ? val : (val ? [val] : []);
    } else {
      normalized[section] = val || null;
    }
  }

  // 額外保留原始欄位（debug 用）
  normalized._raw = rawResult;
  return normalized;
}

/**
 * 快速判斷：某個 AI 結果是否已被 normalize
 */
function isNormalized(result) {
  return result && result._normalized === true;
}

/**
 * 取得某 section 的 label
 */
function getSectionLabel(section) {
  return TEMPLATE_SCHEMA.labels[section] || section;
}

/**
 * 取得某 section 的 style role
 */
function getStyleRole(section) {
  return TEMPLATE_SCHEMA.style_roles[section] || 'doc_section';
}

/**
 * 取得某 section 的 block type
 */
function getBlockType(section) {
  return TEMPLATE_SCHEMA.block_types[section] || 'text';
}

module.exports = {
  TEMPLATE_SCHEMA,
  normalizeProductResult,
  isNormalized,
  getSectionLabel,
  getStyleRole,
  getBlockType,
};
