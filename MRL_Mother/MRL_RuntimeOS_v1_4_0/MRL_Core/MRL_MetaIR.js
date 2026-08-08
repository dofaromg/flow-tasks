const crypto = require('crypto');

function MRL_stable(input) {
  if (input === null || typeof input !== 'object') return input;
  if (Array.isArray(input)) return input.map(MRL_stable);
  const out = {};
  for (const k of Object.keys(input).sort()) out[k] = MRL_stable(input[k]);
  return out;
}

function MRL_hash(input) {
  return crypto.createHash('sha256').update(JSON.stringify(MRL_stable(input))).digest('hex');
}

class MRLMetaIRCompiler {
  constructor() { this.origin_signature = 'MrLiouWord'; }

  compile(sourceIdentity, ast, semanticIntent = {}) {
    const syntaxNodes = ast?.nodes || [];
    const context_relations = [];
    for (let i = 0; i < syntaxNodes.length - 1; i++) {
      context_relations.push({
        relation_id: `MRL_CTX_${i + 1}`,
        from: syntaxNodes[i].name || syntaxNodes[i].value || `node_${i}`,
        to: syntaxNodes[i + 1].name || syntaxNodes[i + 1].value || `node_${i + 1}`,
        relation: 'MRL_SOURCE_SEQUENCE',
        weight: 1
      });
    }
    const runtime_plan = syntaxNodes.map((node, idx) => ({
      step: idx + 1,
      action: MRLMetaIRCompiler.inferAction(node),
      target: node.name || node.value || `MRL_Node_${idx + 1}`,
      node_kind: node.kind || 'unknown'
    }));
    const metaIR = {
      mrl_ir_type: 'MRL_MetaIR',
      version: 'v1.2.0',
      origin_signature: this.origin_signature,
      source_identity: {
        filename: sourceIdentity.filename || 'MRL_Input',
        language: sourceIdentity.language || ast?.language || 'unknown',
        detected: sourceIdentity.detected || sourceIdentity.language || ast?.language || 'unknown',
        source_hash: sourceIdentity.source_hash || null
      },
      syntax_tree: ast,
      semantic_intent: semanticIntent,
      particle_atoms: [],
      context_relations,
      runtime_plan,
      verification_plan: ['MRL_ROUNDTRIP', 'MRL_HASH', 'MRL_PARTICLE_INTEGRITY', 'MRL_CONTEXT_GRAPH', 'MRL_RUNTIME_GRAPH'],
      output_artifact: {
        expected: ['MRL_MetaIR_Record', 'MRL_ParticleIR_Record', 'MRL_RuntimeGraph_Record', 'MRL_Verification_Report']
      },
      created_at: new Date().toISOString()
    };
    metaIR.mrl_hash = MRL_hash(metaIR);
    return metaIR;
  }

  static inferAction(node) {
    const kind = node?.kind || '';
    if (['function','method','call'].includes(kind)) return 'MRL_EXECUTE_CALLABLE';
    if (['class','interface','struct'].includes(kind)) return 'MRL_REGISTER_TYPE';
    if (['particle'].includes(kind)) return 'MRL_REGISTER_PARTICLE';
    if (kind.includes('json') || kind.includes('yaml')) return 'MRL_REGISTER_SCHEMA_FIELD';
    if (kind.includes('heading') || kind.includes('statement')) return 'MRL_ANALYZE_TEXT';
    return 'MRL_ANALYZE_NODE';
  }
}

module.exports = { MRLMetaIRCompiler, MRL_hash, MRL_stable };
