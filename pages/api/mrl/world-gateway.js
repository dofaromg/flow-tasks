import { queryGatewayConnections } from '../../../lib/mrl-db';

const STATIC_GATEWAY = {
  gateway: 'MRL World Gateway',
  status: 'ACTIVE',
  entry_gateway: 'EntryGateway',
  mode: 'external_read_interface',
  canonical_runtime: 'DL580',
  external_services_role: 'adapter / mirror / ingress only',
  endpoints: [
    '/api/mrl/status',
    '/api/mrl/product',
    '/api/mrl/world-gateway',
    '/api/mrl/runtime/convergence',
    '/api/mrl/runtime/persistentloop',
  ],
  routing: {
    global_parallel_network: 'global_parallel_network/',
    particle_satellite_network: 'particle_satellite_network/',
    neural_links: 'neural-links/',
  },
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

export default async function handler(req, res) {
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const dbConnectors = await queryGatewayConnections();
  const data = dbConnectors
    ? { ...STATIC_GATEWAY, connectors_live: dbConnectors.map(c => ({ ...c, _id: undefined })), source: 'BaseWorld_DB' }
    : { ...STATIC_GATEWAY, source: 'static' };

  res.status(200).json({ ...data, timestamp: new Date().toISOString() });
}
