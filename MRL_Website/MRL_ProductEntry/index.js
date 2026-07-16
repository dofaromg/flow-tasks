/**
 * MRL_ProductEntry - Product Entry Module
 *
 * Defines the MRL product entry point structure.
 * Data served via /api/mrl/product, rendered in /mrl page.
 */

module.exports = {
  route: '/api/mrl/product',
  product: 'MRL Product Motherbody',
  version: 'MRL_Product_Motherbody_Engineering_v1',
  canonical_runtime: 'DL580',
  layer_a: 'ACTIVE_CPP_V1',
  pid_scope: 'MRL_LayerA_PIDScope',
  api_source: 'pages/api/mrl/product.js',
  components: {
    particle_core: 'particle_core/src/',
    ai_supercomputer: 'MrLiou_AI_SuperComputer/',
    flowos: 'flowos/',
    neural_network: 'src/modules/',
  },
};
