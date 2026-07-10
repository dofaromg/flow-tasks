'use strict';
// backend/core/scaffolds/index.js
// MRL Scaffold Generator — 統一入口
// origin_signature: MrLiouWord
//
// 使用方式：
//   const Scaffolds = require('../core/scaffolds');
//   const result = await Scaffolds.generateFromPack(pack);

const { buildScaffoldPlan }  = require('./scaffold-builder');
const { writeScaffold, readManifest, listScaffoldFiles, listAllScaffolds } = require('./scaffold-writer');
const { loadPack }           = require('../packs/pack-exporter');
const logger                 = require('../../utils/logger');

/**
 * 主流程：從 packId 讀 pack → build plan → write → 回傳結果
 */
async function generateFromPackId(packId) {
  // 1. 讀 pack
  const pack = loadPack(packId);
  if (!pack) throw Object.assign(new Error(`Pack not found: ${packId}`), { status: 404 });

  return generateFromPack(pack);
}

/**
 * 從 pack object 直接生成（測試用）
 */
async function generateFromPack(pack) {
  // 2. Build plan
  const plan = buildScaffoldPlan(pack);

  // 3. Write
  const writeResult = writeScaffold(pack.pack_id, plan);

  logger.info('Scaffold generated', {
    pack_id:     pack.pack_id,
    scaffold_id: plan.manifest.scaffold_id,
    files:       writeResult.fileCount,
  });

  return {
    scaffold_id:  plan.manifest.scaffold_id,
    pack_id:      pack.pack_id,
    scaffold_dir: writeResult.scaffoldDir,
    file_count:   writeResult.fileCount,
    file_list:    writeResult.fileList,
    manifest:     plan.manifest,
  };
}

/**
 * 取得已生成 scaffold 的 manifest
 */
function getScaffold(packId) {
  return readManifest(packId);
}

/**
 * 列出 scaffold 下的所有檔案
 */
function getScaffoldFiles(packId) {
  return listScaffoldFiles(packId);
}

/**
 * 列出所有已生成的 scaffolds
 */
function getAllScaffolds() {
  return listAllScaffolds();
}

module.exports = {
  generateFromPackId,
  generateFromPack,
  getScaffold,
  getScaffoldFiles,
  getAllScaffolds,
};
