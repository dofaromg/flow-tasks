import { getRuntimeSnapshot } from '../../../../lib/mrl-runtime';

export default function handler(req, res) {
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const snapshot = getRuntimeSnapshot();
  if (!snapshot) {
    return res.status(503).json({
      error: 'MRL runtime snapshot not available. Run: python3 mrl_runtime_snapshot.py',
    });
  }

  const conv = snapshot.convergence || {};
  const loop = conv.mobius_loop || {};
  const fusion = conv.fusion_result || {};

  res.status(200).json({
    api: '/api/mrl/runtime/convergence',
    status: 'ACTIVE',
    engine: 'MobiusLoop',
    canonical_runtime: snapshot.canonical_runtime,
    layer_a: snapshot.layer_a,
    mobius_loop: {
      loop_id: loop.loop_id || null,
      converged: loop.converged ?? null,
      total_cycles: loop.total_cycles ?? null,
      convergence_threshold: loop.convergence_threshold ?? null,
      final_output: loop.final_output || null,
      cycle_count: loop.cycle_history?.length || 0,
      cycle_similarities: (loop.cycle_history || []).map(c => ({
        cycle: c.cycle,
        similarity: c.similarity,
        timestamp: c.timestamp,
      })),
    },
    last_fusion: {
      fusion_id: fusion.fusion_id || null,
      mode: fusion.mode || null,
      particle_count: fusion.particle_count ?? null,
      final_result: fusion.final_result || null,
    },
    particles: conv.particles || [],
    source: 'mrl_runtime_snapshot',
    snapshot_generated_at: snapshot.generated_at,
    timestamp: new Date().toISOString(),
  });
}
