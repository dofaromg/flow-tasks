"use strict";
// MRL_PIDScope_Core — runtime PID ownership
// origin_signature=MrLiouWord
// 規則：禁止 anonymous runtime（runtime_id / workflow_scope / pid 三者缺一即拒絕）。

const REQUIRED = ["runtime_id", "workflow_scope", "pid"];

class PIDScopeCore {
  constructor(db) { this.db = db; }

  registerRuntime(rec) {
    for (const k of REQUIRED) {
      if (rec[k] === undefined || rec[k] === null || rec[k] === "") {
        throw new Error("anonymous runtime rejected: missing " + k);
      }
    }
    const row = {
      runtime_id: rec.runtime_id,
      workflow_scope: rec.workflow_scope,
      pid: rec.pid,
      pid_owner: rec.pid_owner || "MRL_PIDScope_Core",
      runtime_layer: rec.runtime_layer || "MRL_Mother_Runtime",
      replay_binding: rec.replay_binding !== false,
      verification_binding: rec.verification_binding !== false,
      world_binding: rec.world_binding !== false,
      ts: Date.now(),
    };
    this.db.insert("runtime_pidscope", row);
    return row;
  }

  owner(runtime_id) {
    const rows = this.db.find("runtime_pidscope", (r) => r.runtime_id === runtime_id);
    return rows.length ? rows[rows.length - 1] : null; // 最後一筆為現行 owner
  }

  all() { return this.db.all("runtime_pidscope"); }

  isAlive(pid) {
    try { process.kill(pid, 0); return true; }
    catch (e) { return e.code === "EPERM"; } // 存在但無權限仍視為存活
  }

  listOrphans() {
    const latest = new Map();
    for (const r of this.all()) latest.set(r.runtime_id, r); // 取每個 runtime 最新一筆
    return [...latest.values()].filter((r) => !this.isAlive(r.pid));
  }

  updatePid(runtime_id, pid) {
    this.db.insert("runtime_pidscope", {
      runtime_id, pid, pid_owner: "MRL_PIDScope_Core",
      workflow_scope: (this.owner(runtime_id) || {}).workflow_scope || "MRL_RuntimeScope",
      runtime_layer: "MRL_Mother_Runtime",
      replay_binding: true, verification_binding: true, world_binding: true,
      ts: Date.now(), restart_update: true,
    });
  }
}

module.exports = { PIDScopeCore };
