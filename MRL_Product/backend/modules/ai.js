'use strict';
// modules/ai.js — 呼叫 AI 模型，產出固定結構分析
// origin_signature: MrLiouWord
// 第十一包：category-aware prompt builder

const Anthropic = require('@anthropic-ai/sdk');
const config = require('../config');
const logger = require('../utils/logger');
// 第十四包：prompt 組裝委託給 PromptBuilder
const { buildSystemPrompt } = require('../core/generator/prompt-builder');

const client = new Anthropic({ apiKey: config.anthropicApiKey });

// PromptBuilder 已移至 backend/core/generator/prompt-builder.js
// buildSystemPrompt 由上方 require 引入


/**
 * 呼叫 AI 分析問題
 * @param {string} problemText
 * @param {string} [category]  — 可選 category，影響 prompt 偏重
 */
async function analyze(problemText, category) {
  logger.info('AI analyze start', { len: problemText.length, category: category || 'none' });

  const systemPrompt = buildSystemPrompt(category);

  const message = await client.messages.create({
    model: config.anthropicModel,
    max_tokens: 2000,
    system: systemPrompt,
    messages: [
      { role: 'user', content: `請分析以下問題：\n\n${problemText}` }
    ],
  });

  const raw = message.content[0]?.text || '';

  let parsed;
  try {
    const clean = raw.replace(/```json\n?|```\n?/g, '').trim();
    parsed = JSON.parse(clean);
  } catch (e) {
    logger.error('AI output parse failed', { raw: raw.slice(0, 200) });
    throw new Error('AI 分析格式錯誤，請重試');
  }

  logger.info('AI analyze done', { category: category || 'none' });
  return parsed;
}

module.exports = { analyze };
