'use strict';
// backend/core/generator/result-normalizer.js
// MRL_Core_Generator — ResultNormalizer
// origin_signature: MrLiouWord
//
// 職責：將 AI raw output 映射成 template-friendly 標準格式
// 輸入：rawResult（AI JSON）+ category
// 輸出：normalizedData（含 _template_id / _normalized / sections）

const { normalizeProductResult, TEMPLATE_SCHEMA } = require('../../templates/product-template');

// ── Category → normalizer 映射 ────────────────────────────────────
// 未來新增 template 時，只需要在這裡加
const NORMALIZER_MAP = {
  product: normalizeProductResult,
  // decision: normalizeDecisionResult,   ← 未來擴充
  // system:   normalizeSystemResult,
};

/**
 * 根據 category normalize AI raw result
 * @param {object} rawResult — AI 輸出
 * @param {string} category
 * @returns {object|null} normalized data，或 null（category 無對應 normalizer）
 */
function normalizeResult(rawResult, category) {
  if (!rawResult || !category) return null;

  const normalizer = NORMALIZER_MAP[category];
  if (!normalizer) return null;   // 無 normalizer → 前端 fallback

  return normalizer(rawResult);
}

/**
 * 判斷某 category 是否有 normalizer
 */
function hasNormalizer(category) {
  return !!(category && NORMALIZER_MAP[category]);
}

/**
 * 取得 normalizer 支援的 categories
 */
function getNormalizedCategories() {
  return Object.keys(NORMALIZER_MAP);
}

module.exports = {
  normalizeResult,
  hasNormalizer,
  getNormalizedCategories,
};
