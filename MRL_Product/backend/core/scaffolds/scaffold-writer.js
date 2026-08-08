'use strict';
// backend/core/scaffolds/scaffold-writer.js
// MRL Scaffold Generator — Writer
// origin_signature: MrLiouWord
//
// 職責：將 scaffold plan（manifest + files）寫入 storage/scaffolds/{pack_id}/

const fs   = require('fs');
const path = require('path');
const logger = require('../../utils/logger');

const SCAFFOLDS_DIR = path.join(__dirname, '../../../storage/scaffolds');

/**
 * 將 scaffold plan 寫入 disk
 * @param {string} packId
 * @param {{ manifest, files }} plan
 * @returns {{ scaffoldDir, fileCount, fileList }}
 */
function writeScaffold(packId, { manifest, files }) {
  const scaffoldDir = path.join(SCAFFOLDS_DIR, packId);

  // 建目錄
  fs.mkdirSync(scaffoldDir, { recursive: true });

  const fileList = [];

  // 寫 manifest
  fs.writeFileSync(
    path.join(scaffoldDir, 'manifest.json'),
    JSON.stringify(manifest, null, 2),
    'utf8'
  );
  fileList.push('manifest.json');

  // 寫其他檔案
  for (const { path: relPath, content } of files) {
    if (relPath === 'manifest.json') continue; // 已寫

    const absPath = path.join(scaffoldDir, relPath);
    const dir = path.dirname(absPath);
    fs.mkdirSync(dir, { recursive: true });
    fs.writeFileSync(absPath, content, 'utf8');
    fileList.push(relPath);
  }

  logger.info('Scaffold written', {
    packId,
    scaffoldDir: scaffoldDir.replace(process.cwd(), '.'),
    fileCount: fileList.length,
  });

  return {
    scaffoldDir: scaffoldDir.replace(process.cwd(), '.'),
    fileCount: fileList.length,
    fileList,
  };
}

/**
 * 讀取 scaffold manifest
 */
function readManifest(packId) {
  const file = path.join(SCAFFOLDS_DIR, packId, 'manifest.json');
  if (!fs.existsSync(file)) return null;
  try { return JSON.parse(fs.readFileSync(file, 'utf8')); } catch { return null; }
}

/**
 * 列出 scaffold 的所有檔案
 */
function listScaffoldFiles(packId) {
  const dir = path.join(SCAFFOLDS_DIR, packId);
  if (!fs.existsSync(dir)) return null;
  return _walkDir(dir, dir);
}

function _walkDir(base, dir) {
  const result = [];
  for (const entry of fs.readdirSync(dir)) {
    const abs = path.join(dir, entry);
    const rel = path.relative(base, abs);
    if (fs.statSync(abs).isDirectory()) {
      result.push(..._walkDir(base, abs));
    } else {
      result.push(rel);
    }
  }
  return result;
}

/**
 * 列出所有已生成的 scaffold（依 packId）
 */
function listAllScaffolds() {
  if (!fs.existsSync(SCAFFOLDS_DIR)) return [];
  return fs.readdirSync(SCAFFOLDS_DIR)
    .filter(d => fs.statSync(path.join(SCAFFOLDS_DIR, d)).isDirectory())
    .map(packId => {
      const m = readManifest(packId);
      return m ? {
        pack_id:      packId,
        scaffold_id:  m.scaffold_id,
        title:        m.title,
        mode:         m.mode_label || m.mode,
        generated_at: m.generated_at,
      } : null;
    })
    .filter(Boolean);
}

module.exports = { writeScaffold, readManifest, listScaffoldFiles, listAllScaffolds };
