'use strict';
// utils/logger.js — 統一 log 工具
// origin_signature: MrLiouWord

const { now } = require('./time');

// 避免循環依賴：直接讀 env，不 require config
const LOG_LEVEL = process.env.LOG_LEVEL || 'info';
const ORIGIN = 'MrLiouWord';

const levels = { error: 0, warn: 1, info: 2, debug: 3 };
const currentLevel = levels[LOG_LEVEL] ?? 2;

function log(level, msg, meta = {}) {
  if (levels[level] > currentLevel) return;
  const line = JSON.stringify({
    ts: now(),
    level,
    msg,
    origin: ORIGIN,
    ...meta,
  });
  if (level === 'error') process.stderr.write(line + '\n');
  else process.stdout.write(line + '\n');
}

exports.info  = (msg, m) => log('info',  msg, m);
exports.warn  = (msg, m) => log('warn',  msg, m);
exports.error = (msg, m) => log('error', msg, m);
exports.debug = (msg, m) => log('debug', msg, m);
