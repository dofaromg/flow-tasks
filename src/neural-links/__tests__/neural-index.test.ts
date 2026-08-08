// origin_signature: MrLiouWord
// Unit tests for neural-index.ts

import { BranchNeuralSystem, NeuralNode, Synapse } from '../neural-index';

describe('BranchNeuralSystem', () => {
  let neural: BranchNeuralSystem;

  beforeEach(() => {
    neural = new BranchNeuralSystem();
  });

  describe('registerNode', () => {
    it('should register a new node', () => {
      const node: NeuralNode = {
        id: 'test-branch',
        type: 'feature',
        layer: 'L5',
        status: 'active',
        energy: 0.8
      };

      neural.registerNode(node);
      const network = neural.exportNetwork();
      
      expect(network.nodes).toHaveLength(1);
      expect(network.nodes[0].id).toBe('test-branch');
    });

    it('should register multiple nodes', () => {
      neural.registerNode({
        id: 'main',
        type: 'trunk',
        layer: 'L7',
        status: 'active',
        energy: 1.0
      });

      neural.registerNode({
        id: 'feature/test',
        type: 'feature',
        layer: 'L5',
        status: 'active',
        energy: 0.7
      });

      const network = neural.exportNetwork();
      expect(network.nodes).toHaveLength(2);
    });
  });

  describe('createSynapse', () => {
    it('should create a synapse between nodes', () => {
      const synapse: Synapse = {
        from: 'main',
        to: 'feature/test',
        type: 'influence',
        weight: 0.5,
        timestamp: '2026-02-08T00:00:00Z'
      };

      neural.createSynapse(synapse);
      const network = neural.exportNetwork();
      
      expect(network.synapses).toHaveLength(1);
      expect(network.synapses[0].from).toBe('main');
      expect(network.synapses[0].to).toBe('feature/test');
    });
  });

  describe('tracePath', () => {
    beforeEach(() => {
      neural.registerNode({ id: 'main', type: 'trunk', layer: 'L7', status: 'active', energy: 1.0 });
      neural.registerNode({ id: 'feature/a', type: 'feature', layer: 'L5', status: 'active', energy: 0.8 });
      neural.registerNode({ id: 'feature/b', type: 'feature', layer: 'L5', status: 'active', energy: 0.7 });

      neural.createSynapse({
        from: 'main',
        to: 'feature/a',
        type: 'influence',
        weight: 0.8,
        timestamp: '2026-02-08T00:00:00Z'
      });

      neural.createSynapse({
        from: 'feature/a',
        to: 'feature/b',
        type: 'influence',
        weight: 0.7,
        timestamp: '2026-02-08T00:00:00Z'
      });
    });

    it('should find direct path', () => {
      const path = neural.tracePath('main', 'feature/a');
      expect(path).toHaveLength(1);
      expect(path[0].from).toBe('main');
      expect(path[0].to).toBe('feature/a');
    });

    it('should find indirect path', () => {
      const path = neural.tracePath('main', 'feature/b');
      expect(path).toHaveLength(2);
      expect(path[0].from).toBe('main');
      expect(path[1].to).toBe('feature/b');
    });

    it('should return empty array when no path exists', () => {
      neural.registerNode({ id: 'isolated', type: 'feature', layer: 'L5', status: 'active', energy: 0.5 });
      const path = neural.tracePath('main', 'isolated');
      expect(path).toHaveLength(0);
    });
  });

  describe('calculateInfluence', () => {
    beforeEach(() => {
      neural.registerNode({ id: 'main', type: 'trunk', layer: 'L7', status: 'active', energy: 1.0 });
      
      neural.createSynapse({
        from: 'main',
        to: 'feature/a',
        type: 'merge',
        weight: 0.95,
        timestamp: '2026-02-08T00:00:00Z'
      });

      neural.createSynapse({
        from: 'main',
        to: 'feature/b',
        type: 'influence',
        weight: 0.5,
        timestamp: '2026-02-08T00:00:00Z'
      });
    });

    it('should calculate influence correctly', () => {
      const influence = neural.calculateInfluence('main');
      expect(influence).toBeCloseTo(0.725, 2); // (0.95 + 0.5) / 2
    });

    it('should return 0 for nodes with no outgoing synapses', () => {
      neural.registerNode({ id: 'isolated', type: 'feature', layer: 'L5', status: 'active', energy: 0.5 });
      const influence = neural.calculateInfluence('isolated');
      expect(influence).toBe(0);
    });
  });

  describe('getChildren', () => {
    beforeEach(() => {
      neural.registerNode({ id: 'main', type: 'trunk', layer: 'L7', status: 'active', energy: 1.0 });
      neural.registerNode({ id: 'feature/a', type: 'feature', layer: 'L5', status: 'active', energy: 0.8 });
      neural.registerNode({ id: 'feature/b', type: 'feature', layer: 'L5', status: 'active', energy: 0.7 });

      neural.createSynapse({
        from: 'main',
        to: 'feature/a',
        type: 'influence',
        weight: 0.8,
        timestamp: '2026-02-08T00:00:00Z'
      });

      neural.createSynapse({
        from: 'main',
        to: 'feature/b',
        type: 'influence',
        weight: 0.7,
        timestamp: '2026-02-08T00:00:00Z'
      });
    });

    it('should get all children of a node', () => {
      const children = neural.getChildren('main');
      expect(children).toHaveLength(2);
      expect(children.map(c => c.id)).toContain('feature/a');
      expect(children.map(c => c.id)).toContain('feature/b');
    });

    it('should return empty array for leaf nodes', () => {
      const children = neural.getChildren('feature/a');
      expect(children).toHaveLength(0);
    });
  });

  describe('getStats', () => {
    beforeEach(() => {
      neural.registerNode({ id: 'main', type: 'trunk', layer: 'L7', status: 'active', energy: 1.0 });
      neural.registerNode({ id: 'feature/a', type: 'feature', layer: 'L5', status: 'active', energy: 0.8 });
      neural.registerNode({ id: 'feature/b', type: 'feature', layer: 'L5', status: 'merged', energy: 0.95 });

      neural.createSynapse({
        from: 'main',
        to: 'feature/a',
        type: 'influence',
        weight: 0.8,
        timestamp: '2026-02-08T00:00:00Z'
      });
    });

    it('should return correct statistics', () => {
      const stats = neural.getStats();
      
      expect(stats.totalNodes).toBe(3);
      expect(stats.totalSynapses).toBe(1);
      expect(stats.activeNodes).toBe(2);
      expect(stats.mergedNodes).toBe(1);
      expect(stats.averageEnergy).toBeCloseTo(0.916, 2); // (1.0 + 0.8 + 0.95) / 3
    });
  });

  describe('toMermaid', () => {
    beforeEach(() => {
      neural.registerNode({ 
        id: 'main', 
        type: 'trunk', 
        layer: 'L7', 
        status: 'active', 
        energy: 1.0,
        frequency_hz: 164.88
      });
      
      neural.registerNode({ 
        id: 'copilot/test', 
        type: 'cognitive', 
        layer: 'L6', 
        status: 'merged', 
        energy: 0.95,
        merged_pr: 388
      });

      neural.createSynapse({
        from: 'main',
        to: 'copilot/test',
        type: 'merge',
        weight: 0.95,
        timestamp: '2026-02-08T00:00:00Z'
      });
    });

    it('should generate valid Mermaid syntax', () => {
      const mermaid = neural.toMermaid();
      
      expect(mermaid).toContain('graph TD');
      expect(mermaid).toContain('main[');
      expect(mermaid).toContain('copilot_test[');
      expect(mermaid).toContain('-->|merged|');
      expect(mermaid).toContain('classDef trunk');
      expect(mermaid).toContain('classDef cognitive');
    });

    it('should sanitize node IDs in references', () => {
      const mermaid = neural.toMermaid();
      // ID should be sanitized (used in references)
      expect(mermaid).toContain('copilot_test[');
      expect(mermaid).toContain('main -->|merged| copilot_test');
      // But label can contain original name
      expect(mermaid).toContain('copilot/test<br/>');
    });

    it('should include PR numbers', () => {
      const mermaid = neural.toMermaid();
      expect(mermaid).toContain('#388');
    });
  });

  describe('loadNetwork and exportNetwork', () => {
    it('should load and export network correctly', () => {
      const testNetwork = {
        origin_signature: 'MrLiouWord',
        nodes: [
          { id: 'main', type: 'trunk' as const, layer: 'L7', status: 'active' as const, energy: 1.0 }
        ],
        synapses: [
          {
            from: 'main',
            to: 'test',
            type: 'merge' as const,
            weight: 0.9,
            timestamp: '2026-02-08T00:00:00Z'
          }
        ]
      };

      neural.loadNetwork(testNetwork);
      const exported = neural.exportNetwork();

      expect(exported.nodes).toHaveLength(1);
      expect(exported.synapses).toHaveLength(1);
      expect(exported.origin_signature).toBe('MrLiouWord');
    });
  });
});
