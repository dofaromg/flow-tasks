'use strict';
// backend/core/deploy/deploy-writer.js
// MRL Deploy Pack Writer
// origin_signature: MrLiouWord

const fs   = require('fs');
const path = require('path');
const logger = require('../../utils/logger');

const DEPLOYPACKS_DIR = path.join(__dirname, '../../../storage/deploypacks');

function writeDeployPack(packId, { manifest, files }) {
  const deployDir = path.join(DEPLOYPACKS_DIR, packId);
  fs.mkdirSync(deployDir, { recursive: true });

  const written = [];

  // manifest
  fs.writeFileSync(path.join(deployDir, 'manifest.json'), JSON.stringify(manifest, null, 2), 'utf8');
  written.push('manifest.json');

  // all files
  for (const { path: relPath, content } of files) {
    if (relPath === 'manifest.json' || content === null) continue;
    const abs = path.join(deployDir, relPath);
    fs.mkdirSync(path.dirname(abs), { recursive: true });
    fs.writeFileSync(abs, content, 'utf8');
    written.push(relPath);
  }

  // chmod health-check.sh executable
  const healthSh = path.join(deployDir, 'deploy/health-check.sh');
  if (fs.existsSync(healthSh)) {
    try { fs.chmodSync(healthSh, 0o755); } catch {}
  }

  logger.info('DeployPack written', {
    packId,
    deployDir: deployDir.replace(process.cwd(), '.'),
    fileCount: written.length,
  });

  return {
    deployDir: deployDir.replace(process.cwd(), '.'),
    fileCount: written.length,
    fileList:  written,
  };
}

function readDeployManifest(packId) {
  const file = path.join(DEPLOYPACKS_DIR, packId, 'manifest.json');
  if (!fs.existsSync(file)) return null;
  try { return JSON.parse(fs.readFileSync(file, 'utf8')); } catch { return null; }
}

function listDeployFiles(packId) {
  const dir = path.join(DEPLOYPACKS_DIR, packId);
  if (!fs.existsSync(dir)) return null;
  return _walkDir(dir, dir);
}

function listAllDeployPacks() {
  if (!fs.existsSync(DEPLOYPACKS_DIR)) return [];
  return fs.readdirSync(DEPLOYPACKS_DIR)
    .filter(d => fs.statSync(path.join(DEPLOYPACKS_DIR, d)).isDirectory())
    .map(packId => {
      const m = readDeployManifest(packId);
      return m ? { pack_id: packId, deploy_pack_id: m.deploy_pack_id, title: m.title, generated_at: m.generated_at } : null;
    })
    .filter(Boolean);
}

function _walkDir(base, dir) {
  const result = [];
  for (const entry of fs.readdirSync(dir)) {
    const abs = path.join(dir, entry);
    const rel = path.relative(base, abs);
    if (fs.statSync(abs).isDirectory()) result.push(..._walkDir(base, abs));
    else result.push(rel);
  }
  return result;
}

module.exports = { writeDeployPack, readDeployManifest, listDeployFiles, listAllDeployPacks };
