export default function handler(req, res) {
  if (req.method !== 'GET') {
    res.setHeader('Allow', 'GET');
    return res.status(405).json({ error: 'Method not allowed' });
  }

  res.status(200).json({
    persistent_loop: {
      node: 'MRL_PersistentLoop',
      role: 'ORCHESTRATION_COLLECTOR',
      status: 'ACTIVE',
      canonical_runtime: 'DL580',
      source: 'MrLiou_AI_SuperComputer/flowcore_loop.py',
    },
    base_world: {
      name: 'BaseWorld DB',
      role: 'runtime_state_ledger',
      status: 'ACTIVE',
      description: 'Runtime state ledger for all MRL operations',
    },
    entry_gateway: {
      name: 'EntryGateway',
      role: 'external_read_interface',
      status: 'ACTIVE',
      description: 'Read-only external interface for MRL runtime data',
    },
    layer_a: {
      signal_source: 'MRL_LayerA_PIDScope',
      variant: 'ACTIVE_CPP_V1',
      status: 'ACTIVE',
    },
    timestamp: new Date().toISOString(),
  });
}
