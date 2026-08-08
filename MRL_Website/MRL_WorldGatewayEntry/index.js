/**
 * MRL_WorldGatewayEntry - World Gateway Entry Module
 *
 * Defines the MRL World Gateway entry point.
 * EntryGateway = external read interface.
 * External services = adapter / mirror / ingress only.
 * Data served via /api/mrl/world-gateway.
 */

module.exports = {
  route: '/api/mrl/world-gateway',
  gateway: 'MRL World Gateway',
  entry_gateway: 'EntryGateway',
  mode: 'external_read_interface',
  external_services_role: 'adapter / mirror / ingress only',
  canonical_runtime: 'DL580',
  api_source: 'pages/api/mrl/world-gateway.js',
  connectors: [
    'github_connector',
    'notion_connector',
    'google_drive_connector',
    'vercel_connector',
    'gitlab_connector',
    'dropbox_connector',
    'huggingface_connector',
    'icloud_connector',
  ],
};
