'use strict';
// backend/core/packs/pack-exporter.js
// MRL_ProductPack_Generator_v1 — Pack Exporter
// origin_signature: MrLiouWord
//
// 職責：將 ProductPack 存成 JSON 檔，並提供讀回介面
// storage/packs/{pack_id}.json

const fs   = require('fs');
const path = require('path');
const logger = require('../../utils/logger');

const PACKS_DIR = path.join(__dirname, '../../../storage/packs');

// 確保目錄存在
function ensureDir() {
  if (!fs.existsSync(PACKS_DIR)) {
    fs.mkdirSync(PACKS_DIR, { recursive: true });
  }
}

/**
 * 寫出 pack JSON 到 storage/packs/{pack_id}.json
 */
function savePack(pack) {
  ensureDir();
  const file = path.join(PACKS_DIR, `${pack.pack_id}.json`);
  fs.writeFileSync(file, JSON.stringify(pack, null, 2), 'utf8');
  logger.info('Pack saved', { pack_id: pack.pack_id, file });
  return file;
}

/**
 * 讀回 pack JSON
 */
function loadPack(packId) {
  const file = path.join(PACKS_DIR, `${packId}.json`);
  if (!fs.existsSync(file)) return null;
  try {
    return JSON.parse(fs.readFileSync(file, 'utf8'));
  } catch {
    return null;
  }
}

/**
 * 列出所有 pack ID（最近 50 個，依時間倒序）
 */
function listPacks(limit = 50) {
  ensureDir();
  return fs.readdirSync(PACKS_DIR)
    .filter(f => f.endsWith('.json'))
    .map(f => {
      const stat = fs.statSync(path.join(PACKS_DIR, f));
      return { pack_id: f.replace('.json', ''), mtime: stat.mtime };
    })
    .sort((a, b) => b.mtime - a.mtime)
    .slice(0, limit)
    .map(f => f.pack_id);
}

/**
 * 取 pack JSON 字串（供下載用）
 */
function packToJson(pack) {
  return JSON.stringify(pack, null, 2);
}

module.exports = { savePack, loadPack, listPacks, packToJson };
