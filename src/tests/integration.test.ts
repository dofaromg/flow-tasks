/**
 * Integration tests for WebGPU Neural Network & Attention Mechanism Architecture
 * WebGPU 神經網絡與注意力機制架構的集成測試
 */

import {
  NeuronComputeCore,
  AttentionRoutingLayer,
  ComputeEndpointManager,
  PLSRoutingEngine,
  Tensor
} from '../index';

describe('Integration Tests', () => {
  test('should export all main components', () => {
    expect(NeuronComputeCore).toBeDefined();
    expect(AttentionRoutingLayer).toBeDefined();
    expect(ComputeEndpointManager).toBeDefined();
    expect(PLSRoutingEngine).toBeDefined();
  });

  test('should initialize all components independently', async () => {
    const attentionLayer = new AttentionRoutingLayer({
      numHeads: 4,
      headDim: 64
    });
    const endpointManager = new ComputeEndpointManager();

    // Initialize all components
    await attentionLayer.initialize();
    await endpointManager.initialize();

    expect(attentionLayer.isInitialized()).toBe(true);
    expect(endpointManager.isInitialized()).toBe(true);

    // Cleanup
    attentionLayer.destroy();
    endpointManager.destroy();
  });

  test('should create complete routing pipeline', async () => {
    const engine = new PLSRoutingEngine();
    await engine.initialize();

    expect(engine.isInitialized()).toBe(true);

    const components = engine.getComponents();
    expect(components.attentionLayer).toBeDefined();
    expect(components.endpointManager).toBeDefined();
    expect(components.neuronCore).toBeDefined();

    await engine.destroy();
  });

  test('should route and execute computation through pipeline', async () => {
    const engine = new PLSRoutingEngine();
    await engine.initialize();

    const input: Tensor = {
      data: new Float32Array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]),
      shape: [8],
      dtype: 'float32'
    };

    // Route the computation
    const decision = await engine.route(input);
    expect(decision.endpoint).toBeDefined();
    expect(decision.priority).toBeGreaterThan(0);

    // Execute the computation
    const result = await engine.execute(input, decision);
    expect(result.output.data).toBeInstanceOf(Float32Array);
    expect(result.metadata?.executionTime).toBeDefined();

    await engine.destroy();
  });

  test('should handle multiple sequential computations', async () => {
    const engine = new PLSRoutingEngine();
    await engine.initialize();

    const inputs: Tensor[] = [
      { data: new Float32Array([1, 2, 3, 4]), shape: [4], dtype: 'float32' },
      { data: new Float32Array([5, 6, 7, 8]), shape: [4], dtype: 'float32' },
      { data: new Float32Array([9, 10, 11, 12]), shape: [4], dtype: 'float32' }
    ];

    for (const input of inputs) {
      const decision = await engine.route(input);
      const result = await engine.execute(input, decision);
      expect(result.output.data).toBeInstanceOf(Float32Array);
    }

    const history = engine.getRoutingHistory();
    expect(history.length).toBe(3);

    const stats = engine.getStatistics();
    expect(stats.totalRoutings).toBe(3);
    expect(stats.averageConfidence).toBeGreaterThan(0);

    await engine.destroy();
  });

  test('should integrate attention layer with endpoint manager', async () => {
    const attentionLayer = new AttentionRoutingLayer({
      numHeads: 2,
      headDim: 32
    });
    const endpointManager = new ComputeEndpointManager();

    await attentionLayer.initialize();
    await endpointManager.initialize();

    const input: Tensor = {
      data: new Float32Array([1, 2, 3, 4]),
      shape: [4],
      dtype: 'float32'
    };

    // Compute attention
    const attentionResult = await attentionLayer.route(input);
    expect(attentionResult.output.data).toBeInstanceOf(Float32Array);

    // Select endpoint based on attention result
    const endpoint = endpointManager.selectBestEndpoint();
    expect(endpoint).toBeDefined();
    expect(endpoint?.status).toBe('active');

    attentionLayer.destroy();
    endpointManager.destroy();
  });

  test('should handle different tensor shapes', async () => {
    const engine = new PLSRoutingEngine();
    await engine.initialize();

    const tensorShapes = [
      [4],
      [8],
      [16],
      [32]
    ];

    for (const shape of tensorShapes) {
      const input: Tensor = {
        data: new Float32Array(shape[0]).fill(1.0),
        shape: shape,
        dtype: 'float32'
      };

      const decision = await engine.route(input);
      const result = await engine.execute(input, decision);
      
      expect(result.output.data).toBeInstanceOf(Float32Array);
      expect(result.output.data.length).toBeGreaterThan(0);
    }

    await engine.destroy();
  });

  test('should track and report performance metrics', async () => {
    const engine = new PLSRoutingEngine();
    await engine.initialize();

    const input: Tensor = {
      data: new Float32Array([1, 2, 3, 4, 5, 6, 7, 8]),
      shape: [8],
      dtype: 'float32'
    };

    // Perform multiple computations
    const startTime = Date.now();
    const numComputations = 10;

    for (let i = 0; i < numComputations; i++) {
      const decision = await engine.route(input);
      await engine.execute(input, decision);
    }

    const totalTime = Date.now() - startTime;
    const avgTime = totalTime / numComputations;

    const stats = engine.getStatistics();
    expect(stats.totalRoutings).toBe(numComputations);
    expect(avgTime).toBeGreaterThan(0);

    if (process.env.SHOW_PERF_LOGS === 'true') {
      console.log(`Average computation time: ${avgTime.toFixed(2)}ms`);
      console.log(`Total routings: ${stats.totalRoutings}`);
      console.log(`Average confidence: ${stats.averageConfidence.toFixed(3)}`);
    }

    await engine.destroy();
  });

  test('should handle component lifecycle properly', async () => {
    // Create and initialize
    const engine = new PLSRoutingEngine();
    await engine.initialize();
    expect(engine.isInitialized()).toBe(true);

    // Use the engine
    const input: Tensor = {
      data: new Float32Array([1, 2, 3, 4]),
      shape: [4],
      dtype: 'float32'
    };
    await engine.route(input);

    // Destroy
    await engine.destroy();
    expect(engine.isInitialized()).toBe(false);

    // Verify components are cleaned up
    const components = engine.getComponents();
    expect(components.attentionLayer?.isInitialized()).toBe(false);
    expect(components.endpointManager?.isInitialized()).toBe(false);
  });
});
