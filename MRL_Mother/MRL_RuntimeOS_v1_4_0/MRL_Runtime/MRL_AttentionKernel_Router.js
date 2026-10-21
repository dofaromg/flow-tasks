const { MRL_hash } = require('../MRL_Core/MRL_MetaIR');
class MRLAttentionKernelRouter {
  route(runtimeGraph, command = '') {
    const q = String(command || '').toLowerCase();
    const routes = runtimeGraph.nodes.map((node, idx) => {
      const semantic = String(node.semantic || '').toLowerCase();
      let score = 0.2 + (runtimeGraph.nodes.length - idx) * 0.01;
      for (const word of q.split(/\s+|，|,|。|\||>|\(|\)/).filter(Boolean)) if (semantic.includes(word)) score += 0.25;
      if (/parser|parse|分析|解析|整理|file|文件|檔案/.test(q) && /Statement|Document|DataField|FPP|Fluin|Generic|Function/.test(node.label)) score += 0.25;
      if (/verify|驗證|test/.test(q)) score += 0.2;
      if (/attention|注意力|route/.test(q)) score += 0.2;
      return { node_id: node.id, priority: Number(Math.min(1, score).toFixed(4)), reason: 'MRL_ATTENTION_SCORE_BY_COMMAND_AND_SEMANTIC', runtime_action: node.runtime_action };
    }).sort((a,b)=>b.priority-a.priority);
    const attention = { mrl_type:'MRL_AttentionRoute', version:'v1.2.0', origin_signature:'MrLiouWord', routes, created_at:new Date().toISOString() };
    attention.mrl_hash = MRL_hash(attention);
    return attention;
  }
}
module.exports = { MRLAttentionKernelRouter };
