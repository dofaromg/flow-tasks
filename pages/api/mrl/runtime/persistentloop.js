import { getRuntimeSnapshot } from '../../../../lib/mrl-runtime';

export default function handler(req, res) {
  if (req.method !== 'GET') {
    res.setHeader('Allow', ['GET']);
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const snapshot = getRuntimeSnapshot();
  if (!snapshot) {
    return res.status(503).json({
      error: 'MRL runtime snapshot not available. Run: python3 mrl_runtime_snapshot.py',
    });
  }

  const memory = snapshot.memory || {};
  const runtime = snapshot.ai_stack_runtime || {};
  const registry = snapshot.particle_registry || {};

  res.status(200).json({
    persistent_loop: {
      node: 'MRL_PersistentLoop',
      role: 'ORCHESTRATION_COLLECTOR',
      status: 'ACTIVE',
      canonical_runtime: snapshot.canonical_runtime,
      source: 'MrLiou_AI_SuperComputer/flowcore_loop.py',
      runtime_metrics: runtime.metrics || null,
    },
    base_world: {
      name: 'BaseWorld DB',
      role: 'runtime_state_ledger',
      status: 'ACTIVE',
      memory: memory.memory_status || null,
    },
    entry_gateway: {
      name: 'EntryGateway',
      role: 'external_read_interface',
      status: 'ACTIVE',
      particle_network: {
        total_particles: registry.stats?.total_particles || 0,
        providers: registry.stats?.providers || {},
      },
    },
    layer_a: {
      signal_source: 'MRL_LayerA_PIDScope',
      variant: snapshot.layer_a,
      status: 'ACTIVE',
    },
    source: 'mrl_runtime_snapshot',
    snapshot_generated_at: snapshot.generated_at,
    timestamp: new Date().toISOString(),
  });
}
