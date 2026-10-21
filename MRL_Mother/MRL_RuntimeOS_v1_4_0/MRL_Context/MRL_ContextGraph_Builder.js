const { MRL_hash } = require('../MRL_Core/MRL_MetaIR');
class MRLContextGraphBuilder {
  build(metaIR, particleIR) {
    const nodes = particleIR.particles.map(p => ({ id:p.id, label:p.semantic, type:p.particle_type, layer:p.layer }));
    const edges = [];
    for (let i=0; i<nodes.length-1; i++) edges.push({ from:nodes[i].id, to:nodes[i+1].id, relation:'MRL_CONTEXT_SEQUENCE', weight:1 });
    for (const r of metaIR.context_relations || []) {
      edges.push({ from:String(r.from), to:String(r.to), relation:r.relation || 'MRL_META_RELATION', weight:r.weight || 0.5 });
    }
    const graph = { mrl_graph_type:'MRL_ContextGraph', version:'v1.2.0', origin_signature:'MrLiouWord', nodes, edges, created_at:new Date().toISOString() };
    graph.mrl_hash = MRL_hash(graph);
    return graph;
  }
}
module.exports = { MRLContextGraphBuilder };
