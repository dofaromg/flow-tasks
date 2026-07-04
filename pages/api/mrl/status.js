import { getRuntimeSnapshot } from '../../../lib/mrl-runtime';

export default function handler(req, res) {
  if (req.method !== 'GET') {
    res.setHeader('Allow', 'GET');
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const snapshot = getRuntimeSnapshot();
  if (!snapshot) {
    return res.status(503).json({
      error: 'MRL runtime snapshot not available. Run: python3 mrl_runtime_snapshot.py',
    });
  }

  const registry = snapshot.particle_registry || {};
  const runtime = snapshot.ai_stack_runtime || {};
  const memory = snapshot.memory || {};
  const convergence = snapshot.convergence || {};

  res.status(200).json({
    platform: 'MRL Official Platform',
    version: 'MRL_Product_Motherbody_Engineering_v1',
    canonical_runtime: snapshot.canonical_runtime,
    layer_a: {
      signal_source: 'MRL_LayerA_PIDScope',
      status: 'ACTIVE',
      variant: snapshot.layer_a,
      pid_scope: 'MRL_LayerA_PIDScope',
    },
    persistent_loop: {
      node: 'MRL_PersistentLoop',
      role: 'ORCHESTRATION_COLLECTOR',
      status: 'ACTIVE',
    },
    base_world: {
      role: 'runtime_state_ledger',
      status: 'ACTIVE',
      memory: memory.memory_status || null,
    },
    entry_gateway: {
      role: 'external_read_interface',
      status: 'ACTIVE',
    },
    particle_registry: registry.stats || null,
    ai_stack_runtime: runtime.metrics || null,
    convergence_api: convergence.mobius_loop
      ? { converged: convergence.mobius_loop.converged, total_cycles: convergence.mobius_loop.total_cycles }
      : null,
    external_services: 'adapter / mirror / ingress only',
    source: 'mrl_runtime_snapshot',
    snapshot_generated_at: snapshot.generated_at,
    timestamp: new Date().toISOString(),
  });
}
