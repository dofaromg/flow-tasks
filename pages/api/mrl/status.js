import { queryRuntimeState } from '../../../lib/mrl-db';

const STATIC_STATUS = {
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
};

export default async function handler(req, res) {
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const dbState = await queryRuntimeState();
  const data = dbState
    ? { ...STATIC_STATUS, ...dbState, _id: undefined, source: 'BaseWorld_DB' }
    : { ...STATIC_STATUS, source: 'static' };

  res.status(200).json({ ...data, timestamp: new Date().toISOString() });
}
