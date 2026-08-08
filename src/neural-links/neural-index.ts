// origin_signature: MrLiouWord

export interface NeuralNode {
  id: string;
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
  nodes: NeuralNode[];
  synapses: Synapse[];
}

export class BranchNeuralSystem {
  private network: NeuralNetwork;
  
  constructor() {
    this.network = {
      origin_signature: "MrLiouWord",
      nodes: [],
      synapses: []
    };
  }
  
  // 註冊新的神經元節點
  registerNode(node: NeuralNode): void {
    this.network.nodes.push(node);
  }
  
  // 建立突觸連結
  createSynapse(synapse: Synapse): void {
    this.network.synapses.push(synapse);
  }
  
  // 追溯神經路徑 (BFS)
  tracePath(from: string, to: string): Synapse[] {
    const visited = new Set<string>();
    const queue: Array<{node: string, path: Synapse[]}> = [{node: from, path: []}];
    
    while (queue.length > 0) {
      const current = queue.shift();
      if (!current) continue;
      
      if (current.node === to) {
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
    const synapses = this.network.synapses.filter(s => s.from === branchId);
    if (synapses.length === 0) return 0;
    return synapses.reduce((sum, s) => sum + s.weight, 0) / synapses.length;
  }
  
  // 獲取所有子節點
  getChildren(branchId: string): NeuralNode[] {
    const childIds = this.network.synapses
      .filter(s => s.from === branchId)
      .map(s => s.to);
    return this.network.nodes.filter(n => childIds.includes(n.id));
  }
  
  // 獲取節點深度
  getDepth(branchId: string): number {
    const node = this.network.nodes.find(n => n.id === branchId);
    if (!node || !node.parent) return 0;
    return 1 + this.getDepth(node.parent);
  }
  
  // 輸出為 Mermaid
  toMermaid(): string {
    let mermaid = "graph TD\n";
    
    // 生成節點
    this.network.nodes.forEach(node => {
      const label = `${node.id}<br/>${node.layer}`;
      const prInfo = node.merged_pr ? ` #${node.merged_pr}` : '';
      mermaid += `  ${this.sanitizeId(node.id)}[${label}${prInfo}]:::${node.type}\n`;
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
    this.network = network;
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
