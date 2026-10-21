'use strict';

exports.requireFields = (obj, fields) => {
  const missing = fields.filter(f => !obj[f] || String(obj[f]).trim() === '');
  if (missing.length > 0) {
    const err = new Error(`Missing required fields: ${missing.join(', ')}`);
    err.status = 400;
    throw err;
  }
};

exports.isEmail = (str) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(String(str));

exports.sanitizeText = (str, maxLen = 5000) => {
  if (typeof str !== 'string') return '';
  return str.trim().slice(0, maxLen);
};
