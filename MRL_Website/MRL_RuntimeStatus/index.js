/**
 * MRL_RuntimeStatus - Runtime Status Module
 *
 * Aggregates all MRL runtime component status.
 * Data served via /api/mrl/status, /api/mrl/runtime/convergence,
 * /api/mrl/runtime/persistentloop.
 */

module.exports = {
  routes: {
    status: '/api/mrl/status',
    convergence: '/api/mrl/runtime/convergence',
    persistentloop: '/api/mrl/runtime/persistentloop',
  },
  components: {
    layer_a: {
      signal_source: 'MRL_LayerA_PIDScope',
      variant: 'ACTIVE_CPP_V1',
    },
    persistent_loop: {
      node: 'MRL_PersistentLoop',
      role: 'ORCHESTRATION_COLLECTOR',
    },
    base_world: {
      role: 'runtime_state_ledger',
    },
    entry_gateway: {
      role: 'external_read_interface',
    },
    convergence: {
      engine: 'MobiusLoop',
      threshold: 0.9,
      source: 'MrLiou_AI_SuperComputer/ai_fusion_core.py',
    },
  },
  canonical_runtime: 'DL580',
  api_sources: [
    'pages/api/mrl/status.js',
    'pages/api/mrl/runtime/convergence.js',
    'pages/api/mrl/runtime/persistentloop.js',
  ],
};
