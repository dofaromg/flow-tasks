'use strict';
// origin_signature: MrLiouWord; parent: PR #694 ddd011c00497bb03bb52892b9c12582a554e734f
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
function invalid(message) { return Object.assign(new Error(message), { code: 'INVALID_PATH' }); }
function validateName(value, windows = process.platform === 'win32') {
  if (typeof value !== 'string' || !value || /[\x00-\x1f]/.test(value)) throw invalid('invalid path');
  const parts = value.split(/[\\/]/);
  if (parts.some(p => p === '.' || p === '..')) throw invalid('traversal');
  if (windows) {
    if (!/^[a-z]:\\/i.test(value) || value.includes('/')) throw invalid('absolute drive path required');
    for (const p of value.slice(3).split('\\')) {
      if (!p || /[<>:"|?*]/.test(p) || /[. ]$/.test(p) || /^(con|prn|aux|nul|com[1-9¹²³]|lpt[1-9¹²³])(?:\.|$)/i.test(p) || p.includes('~')) throw invalid('Windows alias/device/ADS');
    }
  } else if (!path.isAbsolute(value) || value.includes('\\')) throw invalid('absolute path required');
}
function createWriter(root, io = fs) {
  if (!root) return null;
  validateName(root);
  root = path.resolve(root);
  function directory(p) {
    const st = io.lstatSync(p);
    if (!st.isDirectory() || st.isSymbolicLink() || io.realpathSync(p).toLowerCase() !== p.toLowerCase()) throw invalid('symlink, junction or alias parent');
  }
  // Every ancestor must be an ordinary directory. ACLs must prevent untrusted local mutation.
  function ancestors(p) {
    const chain = []; for (let q = p;; q = path.dirname(q)) { chain.unshift(q); if (q === path.dirname(q)) break; }
    for (const q of chain) directory(q);
  }
  ancestors(root);
  return function createOnly(filepath, data) {
    validateName(filepath);
    const target = path.resolve(filepath);
    const rel = path.relative(root, target);
    if (!rel || rel.startsWith('..' + path.sep) || rel === '..' || path.isAbsolute(rel)) throw invalid('outside configured write root');
    ancestors(root);
    let parent = root;
    for (const part of rel.split(path.sep).slice(0, -1)) {
      parent = path.join(parent, part);
      try { io.mkdirSync(parent); } catch (e) { if (e.code !== 'EEXIST') throw e; }
      directory(parent);
    }
    let fd; let identity;
    try {
      // O_EXCL is the atomic no-clobber decision, never exists()+write().
      fd = io.openSync(target, 'wx+', 0o600);
      identity = io.fstatSync(fd);
      io.writeFileSync(fd, data);
      io.fsyncSync(fd);
      const raw = Buffer.alloc(data.length);
      let offset = 0;
      while (offset < raw.length) {
        const n = io.readSync(fd, raw, offset, raw.length - offset, offset);
        if (!n) throw Object.assign(new Error('short readback'), { code: 'EIO' });
        offset += n;
      }
      if (!raw.equals(data)) throw Object.assign(new Error('readback mismatch'), { code: 'EIO' });
      return { filepath, size: raw.length, sha256: crypto.createHash('sha256').update(raw).digest('hex'), created_exclusively: true };
    } catch (e) {
      // Remove only this operation's incomplete inode; never unlink a conflict winner.
      if (identity) {
        try { const current = io.lstatSync(target); if (current.dev === identity.dev && current.ino === identity.ino && !current.isSymbolicLink()) io.unlinkSync(target); }
        catch (cleanup) { if (cleanup.code !== 'ENOENT') e.rollback_failed = true; }
      }
      throw e;
    } finally { if (fd !== undefined) io.closeSync(fd); }
  };
}
function status(error) {
  if (error.code === 'EEXIST') return 409;
  if (error.code === 'INVALID_PATH') return 400;
  if (['EACCES', 'EPERM', 'EROFS'].includes(error.code)) return 403;
  return 500;
}
module.exports = { createWriter, validateName, status };
