const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

function MRL_meshHash(obj) {
  return crypto.createHash('sha256').update(JSON.stringify(obj)).digest('hex');
}

class MRLRuntimeMeshController {
  constructor(root, nodeManager, graphBuilder, router, executor, logger) {
    this.root = root;
    this.nodeManager = nodeManager;
    this.graphBuilder = graphBuilder;
    this.router = router;
    this.executor = executor;
    this.logger = logger;
    this.meshDir = path.join(root, 'MRL_Storage', 'MRL_RuntimeMesh');
    fs.mkdirSync(this.meshDir, { recursive: true });
  }

  plan(bundle, contextGraph, command = '') {
    const nodes = this.nodeManager.listNodes();
    const runtimeGraph = this.graphBuilder.build(bundle.particleIR, bundle.metaIR);
    const route = this.router.route(runtimeGraph, command);
    const meshPlan = {
      mrl_type: 'MRL_RuntimeMeshPlan',
      origin_signature: 'MrLiouWord',
      plan_id: 'MRL_MESH_PLAN_' + Date.now(),
      created_at: new Date().toISOString(),
      available_nodes: nodes.map(n => ({ node_id: n.node_id, role: n.role, status: n.status, capabilities: n.capabilities })),
      runtime_graph_hash: MRL_meshHash(runtimeGraph),
      context_graph_hash: MRL_meshHash(contextGraph),
      attention_routes: route.routes.map((r, index) => ({
        index,
        particle_id: r.particle_id,
        assigned_node: this._selectNode(nodes, r)?.node_id || 'MRL_LOCAL_NODE',
        route_score: r.score,
        reason: r.reason || 'MRL_AttentionKernel_Router'
      }))
    };
    this._write(meshPlan.plan_id, meshPlan);
    if (this.logger) this.logger.log('MRL_RUNTIME_MESH_PLAN', { plan_id: meshPlan.plan_id, routes: meshPlan.attention_routes.length });
    return meshPlan;
  }

  execute(plan, runtimeGraph, attentionRoute, bundle, context = {}) {
    const trace = this.executor.execute(runtimeGraph, attentionRoute, bundle, context);
    const result = {
      mrl_type: 'MRL_RuntimeMeshExecution',
      origin_signature: 'MrLiouWord',
      execution_id: 'MRL_MESH_EXEC_' + Date.now(),
      plan_id: plan.plan_id,
      status: 'completed',
      executed_at: new Date().toISOString(),
      local_trace: trace,
      node_assignments: plan.attention_routes
    };
    this._write(result.execution_id, result);
    if (this.logger) this.logger.log('MRL_RUNTIME_MESH_EXECUTION', { execution_id: result.execution_id, plan_id: plan.plan_id });
    return result;
  }

  listPlans() {
    return fs.readdirSync(this.meshDir).filter(f => f.endsWith('.json')).map(f => JSON.parse(fs.readFileSync(path.join(this.meshDir, f), 'utf8')));
  }

  _selectNode(nodes, route) {
    const alive = nodes.filter(n => ['alive','registered'].includes(n.status));
    if (!alive.length) return null;
    const capability = (route && route.capability) || 'execute';
    return alive.find(n => (n.capabilities || []).includes(capability)) || alive[0];
  }

  _write(id, obj) {
    fs.writeFileSync(path.join(this.meshDir, `${id}.json`), JSON.stringify(obj, null, 2));
  }
}

module.exports = { MRLRuntimeMeshController };
