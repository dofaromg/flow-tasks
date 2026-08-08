'use strict';
// backend/core/generator/template-selector.js
// MRL_Core_Generator — TemplateSelector
// origin_signature: MrLiouWord
//
// 職責：根據 category（未來也可接 mode / plan / audience）決定 template_id
// 輸入：{ category, mode?, plan? }
// 輸出：template_id string | null

// ── Category → Template 映射 ──────────────────────────────────────
const CATEGORY_TEMPLATE_MAP = {
  product:  'MRL_Delivery_Template_Product_v1',
  // decision: 'MRL_Delivery_Template_Decision_v1',   ← 未來擴充
  // system:   'MRL_Delivery_Template_System_v1',
  // business: 'MRL_Delivery_Template_Business_v1',
  // content:  'MRL_Delivery_Template_Content_v1',
};

/**
 * 選擇 template_id
 * @param {object} opts
 * @param {string} opts.category
 * @param {string} [opts.mode]       — 未來擴充：quick mode 可影響 template 變體
 * @param {string} [opts.planType]   — 未來擴充：once / subscription 可選不同 template
 * @returns {string|null} template_id or null
 */
function selectTemplate({ category, mode, planType } = {}) {
  // 目前只用 category 決定
  return category ? (CATEGORY_TEMPLATE_MAP[category] || null) : null;
}

/**
 * 判斷某 template_id 是否已有對應的 renderer
 * （與前端 TEMPLATE_REGISTRY 的 key 一致）
 */
function isTemplateAvailable(templateId) {
  const available = new Set(Object.values(CATEGORY_TEMPLATE_MAP));
  return available.has(templateId);
}

/**
 * 取得所有可用的 template_id 清單
 */
function getAvailableTemplates() {
  return [...new Set(Object.values(CATEGORY_TEMPLATE_MAP))];
}

/**
 * 取得 category → template 完整 mapping
 */
function getCategoryTemplateMap() {
  return { ...CATEGORY_TEMPLATE_MAP };
}

module.exports = {
  selectTemplate,
  isTemplateAvailable,
  getAvailableTemplates,
  getCategoryTemplateMap,
};
