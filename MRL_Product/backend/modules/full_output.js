'use strict';
// modules/full_output.js — 已付款者取得完整分析結果
// origin_signature: MrLiouWord

const { getDb } = require('./db');
const { enforceAccess } = require('./rules');
const { buildFull, buildPartial } = require('./partial_output');
const { selectTemplate } = require('../core/generator/template-selector');

/**
 * 取得分析結果（自動判斷 partial 或 full）
 */
function getResult(analysisId, sessionId, userId) {
  const db = getDb();
  const analysis = db.prepare('SELECT * FROM analyses WHERE id = ?').get(analysisId);

  if (!analysis) {
    const err = new Error('Analysis not found');
    err.status = 404;
    throw err;
  }

  // 嘗試取得完整結果
  try {
    enforceAccess(analysisId, sessionId, userId);
    // 有權限，回傳完整結果
    const _cat = analysis.category || null;
    return {
      analysisId,
      category:    _cat,
      template_id: selectTemplate({ category: _cat }),
      status: analysis.status,
      problemText: analysis.problem_text,
      result: buildFull(analysis.full_result),
      is_partial: false,
      isPartial: false,
      createdAt: analysis.created_at,
    };
  } catch (e) {
    if (e.status === 402) {
      // 未付款，回傳預覽
      return {
        analysisId,
        category:    analysis.category || null,
        template_id: selectTemplate({ category: analysis.category || null }),
        status: analysis.status,
        problemText: analysis.problem_text,
        result: buildPartial(analysis.full_result),
        is_partial: true,
        isPartial: true,
        requiresPayment: true,
        createdAt: analysis.created_at,
      };
    }
    throw e;
  }
}

module.exports = { getResult };
