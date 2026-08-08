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

  res.status(200).json({
    gateway: 'MRL World Gateway',
    status: 'ACTIVE',
    entry_gateway: 'EntryGateway',
    mode: 'external_read_interface',
    canonical_runtime: snapshot.canonical_runtime,
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
    particle_network: {
      total_particles: registry.stats?.total_particles || 0,
      providers: registry.stats?.providers || {},
      tags: registry.stats?.tags || {},
    },
    source: 'mrl_runtime_snapshot',
    snapshot_generated_at: snapshot.generated_at,
    timestamp: new Date().toISOString(),
  });
}
