'use strict';
// backend/core/packs/pack-builder.js
// MRL_ProductPack_Generator_v1 — Pack Builder
// origin_signature: MrLiouWord
//
// 職責：接收 analysis_id / category / mode，
//       從 DB 取出 result，組成完整 ProductPack
// 輸入：{ analysisId, mode, sessionId, userId }
// 輸出：ProductPack object

const { getDb }              = require('../../modules/db');
const { normalizeResult }    = require('../generator/result-normalizer');
const { selectTemplate }     = require('../generator/template-selector');
const { buildProductPack }   = require('./product-pack');
const logger                 = require('../../utils/logger');

/**
 * 從現有 analysis 建立 ProductPack
 */
async function buildPackFromAnalysis({ analysisId, mode, sessionId, userId }) {
  const db = getDb();

  // 1. 取 analysis
  const analysis = db.prepare('SELECT * FROM analyses WHERE id = ?').get(analysisId);
  if (!analysis) {
    throw Object.assign(new Error(`Analysis not found: ${analysisId}`), { status: 404 });
  }
  if (analysis.status === 'pending' || analysis.status === 'failed') {
    throw Object.assign(new Error('Analysis not ready'), { status: 400 });
  }

  // 2. 確認 category 是 product（第一版只支援 product）
  const category = analysis.category || 'product';
  if (category !== 'product') {
    throw Object.assign(
      new Error(`Pack generation for category "${category}" not yet supported. Only "product" is available.`),
      { status: 400 }
    );
  }

  // 3. 解析 raw result
  let rawResult;
  try {
    rawResult = analysis.full_result
      ? JSON.parse(analysis.full_result)
      : JSON.parse(analysis.partial_result || '{}');
  } catch {
    throw Object.assign(new Error('Analysis result corrupted'), { status: 500 });
  }

  // 4. Normalize
  const normalizedResult = normalizeResult(rawResult, category);

  // 5. Select template（確認）
  const templateId = selectTemplate({ category });

  // 6. Build pack
  const pack = buildProductPack({
    analysisId,
    problemText: analysis.problem_text,
    normalizedResult,
    rawResult,
    mode: mode || 'website',
    sessionId: sessionId || analysis.session_id,
  });

  logger.info('Pack built', { pack_id: pack.pack_id, mode: pack.mode, analysisId });
  return pack;
}

module.exports = { buildPackFromAnalysis };
