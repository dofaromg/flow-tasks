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
  const fusion = snapshot.fusion_engine || {};
  const convergence = snapshot.convergence || {};

  res.status(200).json({
    product: 'MRL Product Motherbody',
    version: 'MRL_Product_Motherbody_Engineering_v1',
    canonical_runtime: snapshot.canonical_runtime,
    status: 'ACTIVE',
    layer_a: snapshot.layer_a,
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
    mrl_model: {
      particle_registry: registry.stats || null,
      registered_particles: registry.particles || [],
      fusion_history: fusion.fusion_history || [],
      convergence_particles: convergence.particles || [],
    },
    source: 'mrl_runtime_snapshot',
    snapshot_generated_at: snapshot.generated_at,
    timestamp: new Date().toISOString(),
  });
}
