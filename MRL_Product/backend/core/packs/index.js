'use strict';
// backend/core/packs/index.js
// MRL_ProductPack_Generator_v1 — 統一入口
// origin_signature: MrLiouWord
//
// 使用方式：
//   const Packs = require('../core/packs');
//   const pack = await Packs.generateFromAnalysis({ analysisId, mode });

const { buildPackFromAnalysis } = require('./pack-builder');
const { savePack, loadPack, listPacks, packToJson } = require('./pack-exporter');
const { PRODUCT_PACK_MODES, PACK_SCHEMA } = require('./product-pack');

/**
 * 主流程：從 analysis 生成並存檔 ProductPack
 */
async function generateFromAnalysis({ analysisId, mode, sessionId, userId }) {
  const pack = await buildPackFromAnalysis({ analysisId, mode, sessionId, userId });
  savePack(pack);
  return pack;
}

/**
 * 取回已生成的 pack
 */
function getPack(packId) {
  return loadPack(packId);
}

/**
 * 列出所有 pack（內部使用）
 */
function getAllPacks(limit = 50) {
  return listPacks(limit).map(id => {
    const p = loadPack(id);
    if (!p) return null;
    return {
      pack_id:     p.pack_id,
      title:       p.title,
      mode:        p.mode,
      analysis_id: p.analysis_id,
      generated_at: p.meta?.generated_at,
    };
  }).filter(Boolean);
}

module.exports = {
  generateFromAnalysis,
  getPack,
  getAllPacks,
  packToJson,
  PRODUCT_PACK_MODES,
  PACK_SCHEMA,
};
