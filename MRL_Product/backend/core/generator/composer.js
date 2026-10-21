'use strict';
// backend/core/generator/composer.js
// MRL_Core_Generator — Composer
// origin_signature: MrLiouWord
//
// 職責：組裝最終 analyze response payload（給前端 renderer 使用）
// 輸入：{ rawResult, normalizedResult, templateId, isPartial, meta }
// 輸出：標準化 response payload

const { buildPartial } = require('../../modules/partial_output');
const { now } = require('../../utils/time');

/**
 * 組裝完整 analyze response payload
 *
 * @param {object} opts
 * @param {string}  opts.analysisId
 * @param {string}  opts.problemText
 * @param {object}  opts.rawResult        — AI 原始輸出
 * @param {object}  [opts.normalizedResult] — template normalized（可 null）
 * @param {string}  [opts.templateId]     — template_id（可 null）
 * @param {boolean} opts.isPartial
 * @param {string}  [opts.category]
 * @param {boolean} [opts.requiresPayment]
 * @param {object}  [opts.meta]           — 額外 meta（mode / plan_type 等）
 * @returns {object} response payload
 */
function composeAnalyzeResponse({
  analysisId,
  problemText,
  rawResult,
  normalizedResult,
  templateId,
  isPartial,
  category,
  requiresPayment,
  meta = {},
}) {
  // 決定要回傳的 result 資料
  // - 有 template 且已 normalize → 回傳 normalized（前端 renderer 用）
  // - 無 template → 回傳 partial 或 raw
  const resultData = isPartial
    ? buildPartial(rawResult)
    : (normalizedResult || rawResult);

  return {
    analysis_id:     analysisId,
    category:        category || null,
    template_id:     templateId || null,
    is_partial:      isPartial,
    requires_payment: isPartial ? (requiresPayment ?? true) : false,
    problem_text:    problemText,
    result:          resultData,
    meta: {
      generated_at: now(),
      ...meta,
    },
  };
}

/**
 * 組裝失敗時的 error payload（讓 api.js 呼叫，保持統一格式）
 */
function composeErrorResponse(message) {
  return { error: message };
}

module.exports = {
  composeAnalyzeResponse,
  composeErrorResponse,
};
