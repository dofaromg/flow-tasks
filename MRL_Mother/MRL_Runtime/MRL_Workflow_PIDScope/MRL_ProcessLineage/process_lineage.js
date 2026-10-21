"use strict";
// MRL_ProcessLineage — runtime parent/child process lineage
// origin_signature=MrLiouWord

class ProcessLineage {
  constructor(db) { this.db = db; }

  record(parent_runtime_id, child_runtime_id) {
    const row = { parent_runtime_id, child_runtime_id, ts: Date.now() };
    this.db.insert("runtime_process_lineage", row);
    return row;
  }

  childrenOf(parent_runtime_id) {
    return this.db.find("runtime_process_lineage", (r) => r.parent_runtime_id === parent_runtime_id)
      .map((r) => r.child_runtime_id);
  }

  ancestorsOf(child_runtime_id) {
    const parentOf = new Map(this.db.all("runtime_process_lineage").map((e) => [e.child_runtime_id, e.parent_runtime_id]));
    const out = [];
    let cur = parentOf.get(child_runtime_id);
    const seen = new Set();
    while (cur && !seen.has(cur)) { out.push(cur); seen.add(cur); cur = parentOf.get(cur); }
    return out;
  }
}

module.exports = { ProcessLineage };
