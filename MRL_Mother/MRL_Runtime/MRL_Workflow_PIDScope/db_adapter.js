"use strict";
// MRL_Workflow_PIDScope — DB adapter
// origin_signature=MrLiouWord
//
// 權位：正式持久化目標為 MRL_BaseWorld_DB_v1（Supabase）。
// 在取得目標 ref + 明確授權前，遠端 adapter 保持 inert（拒絕連線/寫入），
// 不誤連、不誤寫。本地 adapter 僅供本地驗收（acceptance-only），非正式平行 DB。

const fs = require("fs");
const path = require("path");
const os = require("os");

const TABLES = [
  "runtime_pidscope",
  "workflow_registry",
  "runtime_recovery_chain",
  "runtime_process_lineage",
  "runtime_scope_isolation",
];

// 本地 JSON 持久化：acceptance-only，明確標示非正式平行 DB
class LocalJsonAdapter {
  constructor(dir) {
    this.dir = dir || path.join(os.tmpdir(), "mrl_pidscope_data");
    fs.mkdirSync(this.dir, { recursive: true });
    this.kind = "local-json (acceptance-only; NOT a production parallel DB)";
    this.canonical_target = "MRL_BaseWorld_DB_v1";
  }
  _file(t) { return path.join(this.dir, t + ".json"); }
  _read(t) { try { return JSON.parse(fs.readFileSync(this._file(t), "utf8")); } catch (e) { return []; } }
  _write(t, rows) { fs.writeFileSync(this._file(t), JSON.stringify(rows, null, 2)); }
  insert(t, row) { const rows = this._read(t); rows.push(row); this._write(t, rows); return row; }
  all(t) { return this._read(t); }
  find(t, pred) { return this._read(t).filter(pred); }
  update(t, keyFn, patch) { this._write(t, this._read(t).map((r) => (keyFn(r) ? Object.assign({}, r, patch) : r))); }
  clear(t) { this._write(t, []); }
  reset() { for (const t of TABLES) this.clear(t); }
}

// 正式目標 adapter：MRL_BaseWorld_DB_v1。未授權即 inert，所有寫入/讀取拒絕。
class BaseWorldAdapter {
  constructor(opts = {}) {
    this.url = opts.url || process.env.MRL_BASEWORLD_DB_URL || null;
    this.key = opts.key || process.env.MRL_BASEWORLD_DB_KEY || null;
    this.kind = "MRL_BaseWorld_DB_v1 (supabase)";
    this.canonical_target = "MRL_BaseWorld_DB_v1";
    this._inert = !(this.url && this.key && opts.authorized === true);
  }
  _guard() {
    if (this._inert) {
      throw new Error(
        "MRL_BaseWorld_DB_v1 adapter is inert: requires project ref/URL + key + explicit authorization. " +
        "No remote DB writes will occur until the target is named and authorized."
      );
    }
  }
  insert() { this._guard(); throw new Error("BaseWorld remote write not yet implemented (pending authorized integration)"); }
  all() { this._guard(); return []; }
  find() { this._guard(); return []; }
  update() { this._guard(); }
  clear() { this._guard(); }
  reset() { this._guard(); }
}

function makeAdapter(target) {
  // target.kind === 'baseworld' -> 正式目標（需授權，否則 inert）
  if (target && target.kind === "baseworld") return new BaseWorldAdapter(target);
  return new LocalJsonAdapter(target && target.dir);
}

module.exports = { TABLES, LocalJsonAdapter, BaseWorldAdapter, makeAdapter };
