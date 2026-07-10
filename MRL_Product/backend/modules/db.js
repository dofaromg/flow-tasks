'use strict';
// modules/db.js — SQLite 連線單例
// origin_signature: MrLiouWord

const Database = require('better-sqlite3');
const fs = require('fs');
const path = require('path');
const config = require('../config');
const logger = require('../utils/logger');

let _db = null;

function getDb() {
  if (_db) return _db;
  _db = new Database(config.dbPath);
  _db.pragma('journal_mode = WAL');
  _db.pragma('foreign_keys = ON');
  logger.info('SQLite connected', { path: config.dbPath });
  return _db;
}

function initDb() {
  const db = getDb();
  const schema = fs.readFileSync(
    path.join(__dirname, '../../storage/schema.sql'),
    'utf8'
  );
  db.exec(schema);
  logger.info('DB schema applied');
  return db;
}

module.exports = { getDb, initDb };

/**
 * 執行 category migration（安全冪等版）
 * 若欄位已存在會 catch 並跳過
 */
function runCategoryMigration() {
  const db = getDb();
  const migrations = [
    'ALTER TABLE analyses ADD COLUMN category TEXT DEFAULT NULL',
    'ALTER TABLE analyses ADD COLUMN example_prompt_used INTEGER DEFAULT 0',
    'ALTER TABLE event_logs ADD COLUMN category TEXT DEFAULT NULL',
  ];

  migrations.forEach(sql => {
    try {
      db.exec(sql);
    } catch (e) {
      if (!e.message.includes('duplicate column')) {
        // 非重複欄位錯誤才記錄
        require('../utils/logger').debug('Migration skip', { sql: sql.slice(0, 40), msg: e.message });
      }
    }
  });

  // Index（冪等）
  try {
    db.exec('CREATE INDEX IF NOT EXISTS idx_analyses_category ON analyses(category)');
    db.exec('CREATE INDEX IF NOT EXISTS idx_evlog_category ON event_logs(category)');
  } catch { /* ignore */ }
}

module.exports.runCategoryMigration = runCategoryMigration;
