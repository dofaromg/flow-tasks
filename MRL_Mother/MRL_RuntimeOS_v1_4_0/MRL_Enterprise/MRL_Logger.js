const fs = require('fs');
const path = require('path');
class MRLLogger {
  constructor(root) { this.root = root; this.dir = path.join(root, 'MRL_Storage', 'MRL_Audit'); fs.mkdirSync(this.dir, {recursive:true}); this.level = process.env.MRL_LOG_LEVEL || 'info'; }
  log(event, payload={}) { const rec = { origin_signature:'MrLiouWord', event, level:this.level, ts:new Date().toISOString(), ...payload }; const line = JSON.stringify(rec); fs.appendFileSync(path.join(this.dir,'MRL_Audit_Ledger.jsonl'), line+'\n'); console.log(line); return rec; }
}
module.exports = { MRLLogger };
