/**
 * Unit tests for PLSRoutingEngine
 * PLSRoutingEngine 的單元測試
 */

import { PLSRoutingEngine } from '../modules/routing';
import { AttentionRoutingLayer } from '../modules/attention';
import { ComputeEndpointManager } from '../modules/endpoint';
import { NeuronComputeCore } from '../modules/neuron';
import { Tensor } from '../modules/types';

describe('PLSRoutingEngine', () => {
  let engine: PLSRoutingEngine;

  beforeEach(() => {
    engine = new PLSRoutingEngine();
  });

  afterEach(async () => {
    if (engine.isInitialized()) {
      await engine.destroy();
    }
  });

  test('should create instance', () => {
    expect(engine).toBeInstanceOf(PLSRoutingEngine);
  });

  test('should not be initialized on creation', () => {
    expect(engine.isInitialized()).toBe(false);
  });

  test('should initialize successfully', async () => {
    await engine.initialize();
    expect(engine.isInitialized()).toBe(true);
  });

  test('should initialize with provided components', async () => {
    const attentionLayer = new AttentionRoutingLayer({
      numHeads: 2,
      headDim: 32
    });
    const endpointManager = new ComputeEndpointManager();
    const neuronCore = new NeuronComputeCore();

    const customEngine = new PLSRoutingEngine(
      attentionLayer,
      endpointManager,
      neuronCore
    );

    await customEngine.initialize();
    expect(customEngine.isInitialized()).toBe(true);

    const components = customEngine.getComponents();
    expect(components.attentionLayer).toBe(attentionLayer);
    expect(components.endpointManager).toBe(endpointManager);
    expect(components.neuronCore).toBe(neuronCore);

    await customEngine.destroy();
  });

  test('should throw error when routing without initialization', async () => {
    const input: Tensor = {
      data: new Float32Array([1, 2, 3, 4]),
      shape: [4],
      dtype: 'float32'
    };

    await expect(engine.route(input)).rejects.toThrow();
  });

  test('should route successfully after initialization', async () => {
    await engine.initialize();

    const input: Tensor = {
      data: new Float32Array([1, 2, 3, 4]),
      shape: [4],
      dtype: 'float32'
    };

    const decision = await engine.route(input);
    
    expect(decision).toHaveProperty('endpoint');
    expect(decision).toHaveProperty('priority');
    expect(decision).toHaveProperty('estimatedLatency');
    expect(decision).toHaveProperty('confidence');
    expect(decision.endpoint.status).toBe('active');
    expect(decision.priority).toBeGreaterThan(0);
    expect(decision.priority).toBeLessThanOrEqual(1);
  });

  test('should route with required capabilities', async () => {
    await engine.initialize();

    const input: Tensor = {
      data: new Float32Array([1, 2, 3, 4]),
      shape: [4],
      dtype: 'float32'
    };

    const decision = await engine.route(input, ['universal-compute']);
    
    expect(decision).toHaveProperty('endpoint');
    expect(decision.endpoint.capabilities).toContain('universal-compute');
  });

  test('should execute routed computation', async () => {
    await engine.initialize();

    const input: Tensor = {
      data: new Float32Array([1, 2, 3, 4]),
      shape: [4],
      dtype: 'float32'
    };

    const decision = await engine.route(input);
    const result = await engine.execute(input, decision);
    
    expect(result).toHaveProperty('output');
    expect(result.output.data).toBeInstanceOf(Float32Array);
    expect(result.metadata).toHaveProperty('executionTime');
    expect(result.metadata).toHaveProperty('endpointUsed');
  });

  test('should maintain routing history', async () => {
    await engine.initialize();

    const input: Tensor = {
      data: new Float32Array([1, 2, 3, 4]),
      shape: [4],
      dtype: 'float32'
    };

    // Route multiple times
    await engine.route(input);
    await engine.route(input);
    await engine.route(input);

    const history = engine.getRoutingHistory();
    expect(history.length).toBe(3);
    expect(history[0]).toHaveProperty('endpoint');
    expect(history[0]).toHaveProperty('priority');
  });

  test('should limit routing history size', async () => {
    await engine.initialize();

    const input: Tensor = {
      data: new Float32Array([1, 2]),
      shape: [2],
      dtype: 'float32'
    };

    // Route many times to exceed max history
    for (let i = 0; i < 150; i++) {
      await engine.route(input);
    }

    const history = engine.getRoutingHistory();
    expect(history.length).toBeLessThanOrEqual(100); // Max history size
  });

  test('should get routing statistics', async () => {
    await engine.initialize();

    const input: Tensor = {
      data: new Float32Array([1, 2, 3, 4]),
      shape: [4],
      dtype: 'float32'
    };

    await engine.route(input);
    await engine.route(input);

    const stats = engine.getStatistics();
    expect(stats).toHaveProperty('totalRoutings');
    expect(stats).toHaveProperty('endpointUsage');
    expect(stats).toHaveProperty('averageConfidence');
    expect(stats).toHaveProperty('averagePriority');
    expect(stats.totalRoutings).toBe(2);
    expect(typeof stats.endpointUsage).toBe('object');
  });

  test('should clear routing history', async () => {
    await engine.initialize();

    const input: Tensor = {
      data: new Float32Array([1, 2, 3, 4]),
      shape: [4],
      dtype: 'float32'
    };

    await engine.route(input);
    await engine.route(input);
    
    let history = engine.getRoutingHistory();
    expect(history.length).toBe(2);

    engine.clearHistory();
    
    history = engine.getRoutingHistory();
    expect(history.length).toBe(0);
  });

  test('should get components', async () => {
    await engine.initialize();

    const components = engine.getComponents();
    expect(components).toHaveProperty('attentionLayer');
    expect(components).toHaveProperty('endpointManager');
    expect(components).toHaveProperty('neuronCore');
    expect(components.attentionLayer).toBeInstanceOf(AttentionRoutingLayer);
    expect(components.endpointManager).toBeInstanceOf(ComputeEndpointManager);
  });

  test('should handle different endpoint types in execution', async () => {
    await engine.initialize();

    const input: Tensor = {
      data: new Float32Array([1, 2, 3, 4]),
      shape: [4],
      dtype: 'float32'
    };

    // Test with CPU endpoint
    const cpuDecision = await engine.route(input);
    const cpuResult = await engine.execute(input, cpuDecision);
    expect(cpuResult.output.data).toBeInstanceOf(Float32Array);
  });

  test('should destroy successfully', async () => {
    await engine.initialize();
    expect(engine.isInitialized()).toBe(true);

    await engine.destroy();
    expect(engine.isInitialized()).toBe(false);
    expect(engine.getRoutingHistory().length).toBe(0);
  });
});
