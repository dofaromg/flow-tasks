const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

function MRL_nodeId(seed) {
  return 'MRL_NODE_' + crypto.createHash('sha256').update(String(seed || Date.now())).digest('hex').slice(0, 16);
}

class MRLRuntimeNodeManager {
  constructor(root) {
    this.root = root;
    this.nodeDir = path.join(root, 'MRL_Storage', 'MRL_RuntimeNodes');
    fs.mkdirSync(this.nodeDir, { recursive: true });
  }

  createNode(spec = {}) {
    const now = new Date().toISOString();
    const node = {
      mrl_type: 'MRL_RuntimeNode',
      origin_signature: 'MrLiouWord',
      node_id: spec.node_id || MRL_nodeId(JSON.stringify(spec) + now),
      runtime: spec.runtime || 'node',
      role: spec.role || 'MRL_Generic_RuntimeNode',
      status: 'registered',
      keep_alive: Boolean(spec.keep_alive),
      isolation: spec.isolation || 'local_process_or_external_box',
      capabilities: Array.isArray(spec.capabilities) ? spec.capabilities : ['parse', 'execute', 'verify'],
      endpoint: spec.endpoint || null,
      ssh_target: spec.ssh_target || null,
      metadata: spec.metadata || {},
      created_at: now,
      updated_at: now
    };
    this._write(node.node_id, node);
    return node;
  }

  listNodes() {
    return fs.readdirSync(this.nodeDir).filter(f => f.endsWith('.json')).map(f => JSON.parse(fs.readFileSync(path.join(this.nodeDir, f), 'utf8')));
  }

  getNode(id) {
    const file = path.join(this.nodeDir, `${id}.json`);
    return fs.existsSync(file) ? JSON.parse(fs.readFileSync(file, 'utf8')) : null;
  }

  updateNode(id, patch = {}) {
    const node = this.getNode(id);
    if (!node) return null;
    const next = { ...node, ...patch, node_id: id, updated_at: new Date().toISOString() };
    this._write(id, next);
    return next;
  }

  heartbeat(id, status = 'alive') {
    const node = this.getNode(id);
    if (!node) return null;
    return this.updateNode(id, { status, last_heartbeat_at: new Date().toISOString() });
  }

  _write(id, obj) {
    fs.writeFileSync(path.join(this.nodeDir, `${id}.json`), JSON.stringify(obj, null, 2));
  }
}

module.exports = { MRLRuntimeNodeManager };
