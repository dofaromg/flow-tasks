import { queryProductRegistry, queryModelRegistry } from '../../../lib/mrl-db';

const STATIC_PRODUCT = {
  product: 'MRL Product Motherbody',
  version: 'MRL_Product_Motherbody_Engineering_v1',
  canonical_runtime: 'DL580',
  status: 'ACTIVE',
  layer_a: 'ACTIVE_CPP_V1',
  pid_scope: 'MRL_LayerA_PIDScope',
  architecture: 'Particle Language Core + Knowledge Distillation + Fusion Engine',
  components: {
    particle_core: 'particle_core/src/',
    ai_supercomputer: 'MrLiou_AI_SuperComputer/',
    flowos: 'flowos/',
    neural_network: 'src/modules/',
    fusion_engine: 'MrLiou_AI_SuperComputer/runtime/fusion_engine.py',
    particle_registry: 'MrLiou_AI_SuperComputer/runtime/particle_registry.py',
  },
  capabilities: [
    'Particle Language Core - Logic Seed Computation',
    'Knowledge Distillation - Teacher-Student Transfer',
    'Particle Fusion Engine - Dynamic LoRA Composition',
    'WebGPU Neural Network - Attention Routing',
    'AI Stack Runtime - Sequential/Parallel/Recursive Execution',
    'Convergence API - Mobius Loop Processing',
  ],
  entry_points: {
    official_website: '/mrl',
    world_gateway: '/api/mrl/world-gateway',
    runtime_status: '/api/mrl/status',
    convergence: '/api/mrl/runtime/convergence',
    persistent_loop: '/api/mrl/runtime/persistentloop',
  },
};

export default async function handler(req, res) {
  if (req.method !== 'GET') {
    res.setHeader('Allow', 'GET');
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const [dbProduct, dbModel] = await Promise.all([
    queryProductRegistry(),
    queryModelRegistry(),
  ]);

  const data = dbProduct
    ? { ...STATIC_PRODUCT, ...dbProduct, _id: undefined, source: 'BaseWorld_DB' }
    : { ...STATIC_PRODUCT, source: 'static' };

  if (dbModel) {
    data.mrl_model = {
      name: dbModel.name,
      version: dbModel.version,
      base_model: dbModel.base_model,
      capabilities: dbModel.capabilities,
      fusion_engine: dbModel.fusion_engine,
      distillation: dbModel.distillation,
      source: dbModel.source,
    };
  }

  res.status(200).json({ ...data, timestamp: new Date().toISOString() });
}
