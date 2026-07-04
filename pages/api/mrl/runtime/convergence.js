export default function handler(req, res) {
  if (req.method !== 'GET') {
    res.setHeader('Allow', 'GET');
    return res.status(405).json({ error: 'Method not allowed' });
  }

  res.status(200).json({
    api: '/api/mrl/runtime/convergence',
    status: 'ACTIVE',
    convergence_threshold: 0.9,
    engine: 'MobiusLoop',
    canonical_runtime: 'DL580',
    layer_a: 'ACTIVE_CPP_V1',
    description: 'Convergence API - Recursive loop with convergence detection',
    source: 'MrLiou_AI_SuperComputer/ai_fusion_core.py',
    parameters: {
      convergence_threshold: { type: 'float', default: 0.9, description: 'Output similarity threshold for convergence' },
      max_cycles: { type: 'int', default: 10, description: 'Maximum recursive cycles' },
    },
    last_check: new Date().toISOString(),
    timestamp: new Date().toISOString(),
  });
}
