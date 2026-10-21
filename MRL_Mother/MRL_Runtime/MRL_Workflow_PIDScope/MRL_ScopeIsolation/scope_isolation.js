"use strict";
// MRL_ScopeIsolation — workflow/runtime scope contamination detection
// origin_signature=MrLiouWord
// 規則：
//   1. 一個 runtime 只能屬於單一 workflow_scope（多 scope = 污染）
//   2. structure field 節點 scope 必須與 ownership scope 一致（scope_mismatch = 污染）
//   3. MRL_ExternalScope 不得擁有 runtime（external = adapter only）

class ScopeIsolation {
  constructor(db, structureField, pidScopeCore) {
    this.db = db;
    this.sf = structureField;
    this.core = pidScopeCore;
  }

  check() {
    const findings = [];
    const ownerScope = new Map(); // runtime_id -> workflow_scope (from ownership rows)
    const externalOwners = new Set(); // runtime_ids whose ownership/structure-field scope is external

    for (const r of this.core.all()) {
      if (r.restart_update) continue; // restart 補登不視為新 scope 宣告
      if (ownerScope.has(r.runtime_id) && ownerScope.get(r.runtime_id) !== r.workflow_scope) {
        findings.push({ type: "multi_scope", runtime_id: r.runtime_id,
          scopes: [ownerScope.get(r.runtime_id), r.workflow_scope] });
      }
      ownerScope.set(r.runtime_id, r.workflow_scope);
      // 規則 3 以 ownership 為準：external scope 即使未登錄 structure field 也不得擁有 runtime
      if (r.workflow_scope === "MRL_ExternalScope") externalOwners.add(r.runtime_id);
    }

    for (const [rid, sfScope] of this.sf.nodes) {
      const own = ownerScope.get(rid);
      if (own && own !== sfScope) {
        findings.push({ type: "scope_mismatch", runtime_id: rid, owner: own, structureField: sfScope, graph: sfScope });
      }
      if (sfScope === "MRL_ExternalScope") externalOwners.add(rid);
    }

    for (const rid of externalOwners) {
      findings.push({ type: "external_ownership", runtime_id: rid });
    }

    this.db.insert("runtime_scope_isolation", { ts: Date.now(), findings_count: findings.length, findings });
    return findings;
  }
}

module.exports = { ScopeIsolation };
