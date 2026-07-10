"use strict";
// MRL_Workflow_Registry — workflow registration, runtime binding, ordered execution trace
// origin_signature=MrLiouWord
// 執行 trace 以單調 seq 排序，供 replay exactness 使用。

class WorkflowRegistry {
  constructor(db) { this.db = db; this._seq = 0; }

  registerWorkflow(workflow_id, scope) {
    const row = { type: "workflow", workflow_id, scope, ts: Date.now() };
    this.db.insert("workflow_registry", row);
    return row;
  }

  bindRuntime(workflow_id, runtime_id) {
    const row = { type: "binding", workflow_id, runtime_id, ts: Date.now() };
    this.db.insert("workflow_registry", row);
    return row;
  }

  bindingsOf(workflow_id) {
    return this.db.find("workflow_registry", (r) => r.type === "binding" && r.workflow_id === workflow_id)
      .map((r) => r.runtime_id);
  }

  _nextSeq() {
    const seqs = this.db.find("workflow_registry", (r) => r.type === "trace").map((r) => r.seq);
    const base = seqs.length ? Math.max.apply(null, seqs) : 0;
    this._seq = Math.max(this._seq, base) + 1;
    return this._seq;
  }

  trace(runtime_id, op, value) {
    const row = { type: "trace", runtime_id, op, value, seq: this._nextSeq(), ts: Date.now() };
    this.db.insert("workflow_registry", row);
    return row;
  }

  traceLog(runtime_id) {
    return this.db.find("workflow_registry", (r) => r.type === "trace" && r.runtime_id === runtime_id)
      .sort((a, b) => a.seq - b.seq);
  }

  _fold(log) {
    const state = [];
    for (const e of log) { if (e.op === "append") state.push(e.value); }
    return state;
  }

  // replay = 對持久化、排序後的 trace log 做確定性重放
  replay(runtime_id) { return this._fold(this.traceLog(runtime_id)); }
}

module.exports = { WorkflowRegistry };
