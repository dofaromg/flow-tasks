const { MRL_hash } = require('../MRL_Core/MRL_MetaIR');
class MRLRuntimeGraphBuilder {
  build(particleIR, metaIR = null) {
    const nodes = particleIR.particles.map((p, idx) => ({
      id: p.id,
      label: p.particle_type,
      layer: p.layer,
      semantic: p.semantic,
      runtime_action: metaIR?.runtime_plan?.[idx]?.action || this.inferAction(p)
    }));
    const edges = [];
    for (let i = 0; i < nodes.length - 1; i++) edges.push({ from: nodes[i].id, to: nodes[i+1].id, relation: 'MRL_RUNTIME_SEQUENCE', weight: 1 });
    const graph = { mrl_graph_type: 'MRL_RuntimeGraph', version:'v1.2.0', origin_signature: 'MrLiouWord', nodes, edges, created_at: new Date().toISOString() };
    graph.mrl_hash = MRL_hash(graph);
    return graph;
  }
  inferAction(p) {
    if (/Function|Command/.test(p.particle_type)) return 'MRL_EXECUTE_CALLABLE';
    if (/Type/.test(p.particle_type)) return 'MRL_REGISTER_TYPE';
    if (/DataField/.test(p.particle_type)) return 'MRL_REGISTER_DATA_FIELD';
    if (/Document|Statement/.test(p.particle_type)) return 'MRL_ANALYZE_TEXT';
    return 'MRL_EXECUTE_PARTICLE';
  }
}
module.exports = { MRLRuntimeGraphBuilder };
