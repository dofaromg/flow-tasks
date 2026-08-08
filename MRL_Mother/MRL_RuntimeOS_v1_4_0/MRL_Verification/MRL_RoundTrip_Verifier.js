const { MRL_hash } = require('../MRL_Core/MRL_MetaIR');
class MRLRoundTripVerifier {
  verify(source, bundle, runtimeGraph = null, contextGraph = null) {
    const checks = [];
    checks.push({ name: 'MRL_AST_EXISTS', pass: !!bundle.ast });
    checks.push({ name: 'MRL_METAIR_EXISTS', pass: !!bundle.metaIR?.mrl_hash });
    checks.push({ name: 'MRL_PARTICLEIR_EXISTS', pass: Array.isArray(bundle.particleIR?.particles) });
    checks.push({ name: 'MRL_ORIGIN_SIGNATURE', pass: bundle.metaIR?.origin_signature === 'MrLiouWord' && bundle.particleIR?.origin_signature === 'MrLiouWord' });
    checks.push({ name: 'MRL_CONTEXT_GRAPH_EXISTS', pass: contextGraph ? Array.isArray(contextGraph.nodes) : true });
    checks.push({ name: 'MRL_RUNTIME_GRAPH_EXISTS', pass: runtimeGraph ? Array.isArray(runtimeGraph.nodes) : true });
    const sourceHash = MRL_hash({ source });
    const artifactHash = MRL_hash({ bundle, runtimeGraph, contextGraph });
    const pass = checks.every(c => c.pass);
    return { mrl_type: 'MRL_RoundTrip_VerificationReport', version:'v1.2.0', origin_signature: 'MrLiouWord', pass, checks, sourceHash, artifactHash, created_at: new Date().toISOString() };
  }
}
module.exports = { MRLRoundTripVerifier };
