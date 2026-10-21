"use strict";
// MRL_Runtime_Recovery — checkpoint / restore (recovery chain) + restart lineage
// origin_signature=MrLiouWord

class RuntimeRecovery {
  constructor(db, structureField) { this.db = db; this.sf = structureField; }

  checkpoint(label) {
    const cp = {
      type: "checkpoint",
      checkpoint_id: "cp_" + Date.now() + "_" + Math.floor(Math.random() * 1e6),
      label: label || null,
      structureField: this.sf.snapshot(), // canonical (v2)
      graph: this.sf.snapshot(),          // 歷史相容 alias
      ts: Date.now(),
    };
    this.db.insert("runtime_recovery_chain", cp);
    return cp;
  }

  restore(checkpoint_id) {
    const cp = this.db.find("runtime_recovery_chain",
      (r) => r.type === "checkpoint" && r.checkpoint_id === checkpoint_id)[0];
    if (!cp) throw new Error("no checkpoint: " + checkpoint_id);
    this.sf.restore(cp.structureField || cp.graph); // 相容舊格式 cp.graph
    return cp;
  }

  recordRestart(runtime_id, old_pid, new_pid) {
    this.db.insert("runtime_recovery_chain", { type: "restart", runtime_id, old_pid, new_pid, ts: Date.now() });
  }

  restartChain(runtime_id) {
    return this.db.find("runtime_recovery_chain", (r) => r.type === "restart" && r.runtime_id === runtime_id)
      .sort((a, b) => a.ts - b.ts);
  }
}

module.exports = { RuntimeRecovery };
