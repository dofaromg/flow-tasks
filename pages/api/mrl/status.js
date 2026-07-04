export default function handler(req, res) {
  if (req.method !== 'GET') {
    res.setHeader('Allow', 'GET');
    return res.status(405).json({ error: 'Method not allowed' });
  }

  res.status(200).json({
    platform: 'MRL Official Platform',
    version: 'MRL_Product_Motherbody_Engineering_v1',
    canonical_runtime: 'DL580',
    layer_a: {
      signal_source: 'MRL_LayerA_PIDScope',
      status: 'ACTIVE',
      variant: 'ACTIVE_CPP_V1',
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
    },
    entry_gateway: {
      role: 'external_read_interface',
      status: 'ACTIVE',
    },
    convergence_api: 'available',
    external_services: 'adapter / mirror / ingress only',
    timestamp: new Date().toISOString(),
  });
}
