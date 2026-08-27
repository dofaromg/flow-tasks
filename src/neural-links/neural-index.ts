// origin_signature: MrLiouWord

export const MRL_NAMING_PREFIX = 'MRL_';

export function toMRLNodeId(sourceIdentity: string): string {
  if (typeof sourceIdentity !== 'string' || !sourceIdentity.trim()) {
    throw new Error('MRL naming requires a non-empty source identity');
  }

  const trimmed = sourceIdentity.trim();
  if (/^MRL_/i.test(trimmed)) {
    const suffix = trimmed.slice(MRL_NAMING_PREFIX.length);
    if (!suffix) {
      throw new Error('MRL naming requires content after the MRL_ prefix');
    }
    return `${MRL_NAMING_PREFIX}${suffix}`;
  }

  return `${MRL_NAMING_PREFIX}${trimmed}`;
}

export interface NeuralNode {
  id: string;
  source_branch?: string;
  naming_authority?: 'MRL';
  type: 'trunk' | 'cognitive' | 'feature' | 'hotfix' | 'experimental';
  layer: string;
  frequency_hz?: number;
  status: 'active' | 'merged' | 'closed' | 'archived';
  energy: number; // 0-1
  parent?: string;
  merged_pr?: number;
  created_at?: string;
  merged_at?: string;
}

export interface Synapse {
  from: string;
  to: string;
  type: 'merge' | 'rebase' | 'cherry-pick' | 'influence';
  weight: number; // 0-1
  pr_number?: number;
  timestamp: string;
}

export interface NeuralNetwork {
  origin_signature: string;
  naming_policy?: {
    version: string;
    canonical_prefix: 'MRL_';
    canonical_identity_field: 'id';
    source_identity_field: 'source_branch';
    source_identity_mutated: false;
  };
  nodes: NeuralNode[];
  synapses: Synapse[];
}

export class BranchNeuralSystem {
  private network: NeuralNetwork;
  
  constructor() {
    this.network = {
      origin_signature: "MrLiouWord",
      naming_policy: {
        version: "MRL_AutoExpansion_Naming_v1",
        canonical_prefix: "MRL_",
        canonical_identity_field: "id",
        source_identity_field: "source_branch",
        source_identity_mutated: false
      },
      nodes: [],
      synapses: []
    };
  }
  
  // 註冊新的神經元節點
  registerNode(node: NeuralNode): void {
    const sourceBranch = node.source_branch ?? node.id;
    const canonicalId = toMRLNodeId(sourceBranch);

    if (node.source_branch && toMRLNodeId(node.id) !== canonicalId) {
      throw new Error(`MRL provenance violation: node id "${node.id}" does not match source_branch "${node.source_branch}"`);
    }

    if (this.network.nodes.some(existing => existing.id === canonicalId)) {
      throw new Error(`MRL naming collision: duplicate node id "${canonicalId}"`);
    }

    this.network.nodes.push({
      ...node,
      id: canonicalId,
      source_branch: sourceBranch,
      naming_authority: 'MRL',
      parent: node.parent ? toMRLNodeId(node.parent) : undefined
    });
  }
  
  // 建立突觸連結
  createSynapse(synapse: Synapse): void {
    const from = toMRLNodeId(synapse.from);
    const to = toMRLNodeId(synapse.to);
    const nodeIds = new Set(this.network.nodes.map(node => node.id));

    if (!nodeIds.has(from) || !nodeIds.has(to)) {
      throw new Error(`MRL chain violation: unresolved synapse ${from} -> ${to}`);
    }

    this.network.synapses.push({
      ...synapse,
      from,
      to
    });
  }
  
  // 追溯神經路徑 (BFS)
  tracePath(from: string, to: string): Synapse[] {
    const canonicalFrom = toMRLNodeId(from);
    const canonicalTo = toMRLNodeId(to);
    const visited = new Set<string>();
    const queue: Array<{node: string, path: Synapse[]}> = [{node: canonicalFrom, path: []}];
    
    while (queue.length > 0) {
      const current = queue.shift();
      if (!current) continue;
      
      if (current.node === canonicalTo) {
        return current.path;
      }
      
      if (visited.has(current.node)) continue;
      visited.add(current.node);
      
      const outgoing = this.network.synapses.filter(s => s.from === current.node);
      for (const synapse of outgoing) {
        queue.push({
          node: synapse.to,
          path: [...current.path, synapse]
        });
      }
    }
    
    return [];
  }
  
  // 計算分支影響力
  calculateInfluence(branchId: string): number {
    const canonicalId = toMRLNodeId(branchId);
    const synapses = this.network.synapses.filter(s => s.from === canonicalId);
    if (synapses.length === 0) return 0;
    return synapses.reduce((sum, s) => sum + s.weight, 0) / synapses.length;
  }
  
  // 獲取所有子節點
  getChildren(branchId: string): NeuralNode[] {
    const canonicalId = toMRLNodeId(branchId);
    const childIds = this.network.synapses
      .filter(s => s.from === canonicalId)
      .map(s => s.to);
    return this.network.nodes.filter(n => childIds.includes(n.id));
  }
  
  // 獲取節點深度
  getDepth(branchId: string): number {
    const canonicalId = toMRLNodeId(branchId);
    const node = this.network.nodes.find(n => n.id === canonicalId);
    if (!node || !node.parent) return 0;
    return 1 + this.getDepth(node.parent);
  }
  
  // 輸出為 Mermaid
  toMermaid(): string {
    let mermaid = "graph TD\n";
    const mermaidIds = new Map<string, string>();
    
    // 生成節點
    this.network.nodes.forEach(node => {
      const renderedId = this.sanitizeId(node.id);
      const previousId = mermaidIds.get(renderedId);
      if (previousId) {
        throw new Error(`MRL Mermaid collision: "${previousId}" and "${node.id}" both render as "${renderedId}"`);
      }
      mermaidIds.set(renderedId, node.id);
      const label = `${node.id}<br/>${node.layer}`;
      const prInfo = node.merged_pr ? ` #${node.merged_pr}` : '';
      mermaid += `  ${renderedId}[${label}${prInfo}]:::${node.type}\n`;
    });
    
    mermaid += "\n";
    
    // 生成連結
    this.network.synapses.forEach(synapse => {
      const linkType = synapse.type === 'merge' ? '-->|merged|' : '-.->|' + synapse.type + '|';
      mermaid += `  ${this.sanitizeId(synapse.from)} ${linkType} ${this.sanitizeId(synapse.to)}\n`;
    });
    
    mermaid += "\n";
    
    // 樣式定義
    mermaid += "  classDef trunk fill:#ff6b6b,stroke:#333,stroke-width:4px\n";
    mermaid += "  classDef cognitive fill:#4ecdc4,stroke:#333,stroke-width:3px\n";
    mermaid += "  classDef feature fill:#95e1d3,stroke:#333,stroke-width:2px\n";
    mermaid += "  classDef hotfix fill:#f9ca24,stroke:#333,stroke-width:2px\n";
    mermaid += "  classDef experimental fill:#6c5ce7,stroke:#333,stroke-width:2px\n";
    
    return mermaid;
  }
  
  // 清理節點 ID 使其符合 Mermaid 語法
  private sanitizeId(id: string): string {
    return id.replace(/[\/\-\.]/g, '_');
  }
  
  // 載入網絡資料
  loadNetwork(network: NeuralNetwork): void {
    const nodes = network.nodes.map(node => {
      const sourceBranch = node.source_branch ?? node.id;
      const canonicalId = toMRLNodeId(sourceBranch);

      if (node.source_branch && toMRLNodeId(node.id) !== canonicalId) {
        throw new Error(`MRL provenance violation: node id "${node.id}" does not match source_branch "${node.source_branch}"`);
      }

      return {
        ...node,
        id: canonicalId,
        source_branch: sourceBranch,
        naming_authority: 'MRL' as const,
        parent: node.parent ? toMRLNodeId(node.parent) : undefined
      };
    });

    const ids = new Set<string>();
    nodes.forEach(node => {
      if (ids.has(node.id)) {
        throw new Error(`MRL naming collision: duplicate node id "${node.id}"`);
      }
      ids.add(node.id);
    });

    const synapses = network.synapses.map(synapse => ({
      ...synapse,
      from: toMRLNodeId(synapse.from),
      to: toMRLNodeId(synapse.to)
    }));

    synapses.forEach(synapse => {
      if (!ids.has(synapse.from) || !ids.has(synapse.to)) {
        throw new Error(`MRL chain violation: unresolved synapse ${synapse.from} -> ${synapse.to}`);
      }
    });

    this.network = {
      ...network,
      naming_policy: {
        version: "MRL_AutoExpansion_Naming_v1",
        canonical_prefix: "MRL_",
        canonical_identity_field: "id",
        source_identity_field: "source_branch",
        source_identity_mutated: false
      },
      nodes,
      synapses
    };
  }
  
  // 匯出網絡資料
  exportNetwork(): NeuralNetwork {
    return this.network;
  }
  
  // 獲取網絡統計
  getStats(): {
    totalNodes: number;
    totalSynapses: number;
    activeNodes: number;
    mergedNodes: number;
    averageEnergy: number;
  } {
    const totalNodes = this.network.nodes.length;
    const totalSynapses = this.network.synapses.length;
    const activeNodes = this.network.nodes.filter(n => n.status === 'active').length;
    const mergedNodes = this.network.nodes.filter(n => n.status === 'merged').length;
    const averageEnergy = this.network.nodes.reduce((sum, n) => sum + n.energy, 0) / totalNodes;
    
    return {
      totalNodes,
      totalSynapses,
      activeNodes,
      mergedNodes,
      averageEnergy
    };
  }
}
