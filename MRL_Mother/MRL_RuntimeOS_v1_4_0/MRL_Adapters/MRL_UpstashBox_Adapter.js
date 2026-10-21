class MRLUpstashBoxAdapter {
  constructor(config = {}) {
    this.config = config;
  }

  describe() {
    return {
      mrl_type: 'MRL_External_RuntimeNode_Adapter',
      origin_signature: 'MrLiouWord',
      adapter_name: 'MRL_UpstashBox_Adapter',
      status: 'adapter_spec_ready_external_execution_pending',
      purpose: 'Map external isolated agent containers into MRL_RuntimeNode and MRL_RuntimeMesh without replacing the MRL mother runtime.',
      supported_fields: ['runtime', 'agent', 'keepAlive', 'ssh_target', 'endpoint'],
      note: 'This adapter intentionally contains no API key and performs no external call in packaged acceptance.'
    };
  }

  toRuntimeNode(boxRecord = {}) {
    return {
      runtime: boxRecord.runtime || 'node',
      role: boxRecord.role || 'MRL_External_Box_RuntimeNode',
      keep_alive: Boolean(boxRecord.keepAlive || boxRecord.keep_alive),
      isolation: 'external_upstash_box',
      endpoint: boxRecord.endpoint || null,
      ssh_target: boxRecord.ssh_target || boxRecord.ssh || null,
      capabilities: boxRecord.capabilities || ['shell', 'filesystem', 'git', 'execute', 'agent_run'],
      metadata: {
        provider: 'Upstash Box',
        box_id: boxRecord.box_id || boxRecord.id || null,
        agent_harness: boxRecord.agent_harness || null,
        mrl_external_layer: 'MRL_External_Runtime_Infrastructure'
      }
    };
  }
}

module.exports = { MRLUpstashBoxAdapter };
