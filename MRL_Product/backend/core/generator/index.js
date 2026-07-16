'use strict';
// backend/core/generator/index.js
// MRL_Core_Generator — 統一入口
// origin_signature: MrLiouWord
//
// 使用方式：
//   const Generator = require('../core/generator');
//   const payload = await Generator.analyze({ problemText, category, ... });

const { buildSystemPrompt }  = require('./prompt-builder');
const { normalizeResult }    = require('./result-normalizer');
const { selectTemplate }     = require('./template-selector');
const { composeAnalyzeResponse, composeErrorResponse } = require('./composer');
const { analyze: callAI }    = require('../../modules/ai');
const logger                 = require('../../utils/logger');

/**
 * Core Generator 主流程
 * 串接 PromptBuilder → AnalyzeEngine → ResultNormalizer → TemplateSelector → Composer
 *
 * @param {object} opts
 * @param {string}  opts.problemText
 * @param {string}  [opts.category]
 * @param {string}  [opts.mode]
 * @param {string}  [opts.analysisId]
 * @param {boolean} [opts.isPartial]
 * @param {boolean} [opts.requiresPayment]
 * @param {object}  [opts.meta]
 * @returns {Promise<object>} composeAnalyzeResponse payload
 */
async function analyze({
  problemText,
  category,
  mode,
  analysisId,
  isPartial = true,
  requiresPayment = true,
  meta = {},
}) {
  logger.debug('Core.Generator.analyze start', { category, isPartial });

  // 1. AnalyzeEngine：呼叫 AI（ai.js 負責 prompt building + model call）
  const rawResult = await callAI(problemText, category);

  // 2. TemplateSelector：選 template_id
  const templateId = selectTemplate({ category, mode });

  // 3. ResultNormalizer：normalize（若有對應 template）
  const normalizedResult = normalizeResult(rawResult, category);

  // 4. Composer：組裝 response
  const payload = composeAnalyzeResponse({
    analysisId,
    problemText,
    rawResult,
    normalizedResult,
    templateId,
    isPartial,
    category,
    requiresPayment,
    meta,
  });

  logger.debug('Core.Generator.analyze done', { templateId, isPartial });
  return { rawResult, payload };
}

module.exports = {
  analyze,
  // 各子模組也可直接取用
  PromptBuilder:    require('./prompt-builder'),
  ResultNormalizer: require('./result-normalizer'),
  TemplateSelector: require('./template-selector'),
  Composer:         require('./composer'),
};
