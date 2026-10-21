'use strict';
// backend/core/deploy/index.js
// MRL Deploy Pack — 統一入口
// origin_signature: MrLiouWord

const { buildDeployPlan }   = require('./deploy-builder');
const { writeDeployPack, readDeployManifest, listDeployFiles, listAllDeployPacks } = require('./deploy-writer');
const { validateDeployPack } = require('./deploy-validator');
const { readManifest }       = require('../scaffolds/scaffold-writer');
const logger                 = require('../../utils/logger');

/**
 * 主流程：從 scaffold_id → deploy pack
 */
async function generateDeployPackFromScaffold(packId) {
  // 1. 讀 scaffold manifest（用 pack_id 找）
  const scaffoldManifest = readManifest(packId);
  if (!scaffoldManifest) {
    throw Object.assign(new Error(`Scaffold not found for pack: ${packId}`), { status: 404 });
  }

  // 2. Build plan
  const plan = buildDeployPlan(scaffoldManifest);

  // 3. Write
  const writeResult = writeDeployPack(packId, plan);

  // 4. Validate immediately
  const validation = validateDeployPack(packId);

  logger.info('DeployPack generated', {
    pack_id:       packId,
    deploy_pack_id: plan.manifest.deploy_pack_id,
    files:         writeResult.fileCount,
    score:         validation.runnable_score,
  });

  return {
    deploy_pack_id: plan.manifest.deploy_pack_id,
    pack_id:        packId,
    deploy_dir:     writeResult.deployDir,
    file_count:     writeResult.fileCount,
    file_list:      writeResult.fileList,
    manifest:       plan.manifest,
    validation,
  };
}

function getDeployPack(packId) {
  return readDeployManifest(packId);
}

function getDeployPackFiles(packId) {
  return listDeployFiles(packId);
}

function validatePack(packId) {
  return validateDeployPack(packId);
}

function getAllDeployPacks() {
  return listAllDeployPacks();
}

module.exports = {
  generateDeployPackFromScaffold,
  getDeployPack,
  getDeployPackFiles,
  validatePack,
  getAllDeployPacks,
};
