const fs = require('fs');
const path = require('path');
const { MRL_hash } = require('../MRL_Core/MRL_MetaIR');

class MRLModuleRegistry {
  constructor(root = process.cwd()) {
    this.root = root;
    this.modules = [
      { id:'MRL_Module_Parser', capability:'MRL_PARSE_SOURCE', status:'implemented', description:'Parse source into AST/MetaIR/ParticleIR' },
      { id:'MRL_Module_ContextGraph', capability:'MRL_BUILD_CONTEXT_GRAPH', status:'implemented', description:'Build relation graph from particles' },
      { id:'MRL_Module_RuntimeGraph', capability:'MRL_BUILD_RUNTIME_GRAPH', status:'implemented', description:'Build execution DAG' },
      { id:'MRL_Module_AttentionKernel', capability:'MRL_ROUTE_ATTENTION', status:'implemented', description:'Route runtime by attention priority' },
      { id:'MRL_Module_DocumentAnalyzer', capability:'MRL_ANALYZE_DOCUMENT', status:'implemented', description:'Analyze text/markdown/code structure' },
      { id:'MRL_Module_Deduplicate', capability:'MRL_DEDUPLICATE_LINES', status:'implemented', description:'Real line deduplication utility' },
      { id:'MRL_Module_RoundTripVerifier', capability:'MRL_VERIFY_ROUNDTRIP', status:'implemented', description:'Verify IR presence and origin signature' },
      { id:'MRL_Module_TraceStore', capability:'MRL_WRITE_TRACE', status:'implemented', description:'Persist runtime trace to storage' },
      { id:'MRL_Module_ModelInference', capability:'MRL_MODEL_INFERENCE', status:'external_adapter_pending', description:'Local/remote model adapter not bundled in this no-dependency core' }
    ];
  }
  list() { return this.modules; }
  persist() {
    const dir = path.join(this.root, 'MRL_Storage', 'MRL_Reports');
    fs.mkdirSync(dir, { recursive:true });
    const report = { mrl_type:'MRL_Module_Registry_Report', origin_signature:'MrLiouWord', modules:this.modules, created_at:new Date().toISOString() };
    report.mrl_hash = MRL_hash(report);
    fs.writeFileSync(path.join(dir, 'MRL_Module_Registry_Report.json'), JSON.stringify(report,null,2));
    return report;
  }
}
module.exports = { MRLModuleRegistry };
