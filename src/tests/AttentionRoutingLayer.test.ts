/**
 * Unit tests for AttentionRoutingLayer
 * AttentionRoutingLayer 的單元測試
 */

import { AttentionRoutingLayer } from '../modules/attention';
import { Tensor, AttentionConfig } from '../modules/types';

describe('AttentionRoutingLayer', () => {
  let layer: AttentionRoutingLayer;
  const config: AttentionConfig = {
    numHeads: 4,
    headDim: 64,
    dropoutRate: 0.1
  };

  beforeEach(() => {
    layer = new AttentionRoutingLayer(config);
  });

  afterEach(() => {
    if (layer.isInitialized()) {
      layer.destroy();
    }
  });

  test('should create instance with valid config', () => {
    expect(layer).toBeInstanceOf(AttentionRoutingLayer);
  });

  test('should throw error with invalid config', () => {
    expect(() => {
      new AttentionRoutingLayer({ numHeads: 0, headDim: 64 });
    }).toThrow();

    expect(() => {
      new AttentionRoutingLayer({ numHeads: 4, headDim: -1 });
    }).toThrow();
  });

  test('should not be initialized on creation', () => {
    expect(layer.isInitialized()).toBe(false);
  });

  test('should initialize successfully', async () => {
    await layer.initialize();
    expect(layer.isInitialized()).toBe(true);
  });

  test('should not reinitialize if already initialized', async () => {
    await layer.initialize();
    expect(layer.isInitialized()).toBe(true);
    
    // Second initialization should not cause error
    await layer.initialize();
    expect(layer.isInitialized()).toBe(true);
  });

  test('should throw error when computing without initialization', async () => {
    const query: Tensor = {
      data: new Float32Array([1, 2, 3, 4]),
      shape: [4],
      dtype: 'float32'
    };
    const key: Tensor = {
      data: new Float32Array([1, 2, 3, 4]),
      shape: [4],
      dtype: 'float32'
    };
    const value: Tensor = {
      data: new Float32Array([5, 6, 7, 8]),
      shape: [4],
      dtype: 'float32'
    };

    await expect(layer.computeAttention(query, key, value)).rejects.toThrow();
  });

  test('should compute attention after initialization', async () => {
    await layer.initialize();

    const query: Tensor = {
      data: new Float32Array([1, 2, 3, 4]),
      shape: [4],
      dtype: 'float32'
    };
    const key: Tensor = {
      data: new Float32Array([1, 2, 3, 4]),
      shape: [4],
      dtype: 'float32'
    };
    const value: Tensor = {
      data: new Float32Array([5, 6, 7, 8]),
      shape: [4],
      dtype: 'float32'
    };

    const result = await layer.computeAttention(query, key, value);
    
    expect(result).toHaveProperty('output');
    expect(result.output.data).toBeInstanceOf(Float32Array);
    expect(result.output.shape).toEqual(value.shape);
    expect(result.metadata).toHaveProperty('executionTime');
    expect(result.metadata?.endpointUsed).toBe('attention-layer');
  });

  test('should route input through self-attention', async () => {
    await layer.initialize();

    const input: Tensor = {
      data: new Float32Array([1, 2, 3, 4, 5, 6, 7, 8]),
      shape: [8],
      dtype: 'float32'
    };

    const result = await layer.route(input);
    
    expect(result).toHaveProperty('output');
    expect(result.output.data).toBeInstanceOf(Float32Array);
    expect(result.output.data.length).toBeGreaterThan(0);
  });

  test('should return config', () => {
    const returnedConfig = layer.getConfig();
    expect(returnedConfig).toEqual(config);
    // Ensure it's a copy, not the original
    expect(returnedConfig).not.toBe(config);
  });

  test('should get weights after initialization', async () => {
    await layer.initialize();
    
    const weights = layer.getWeights();
    expect(weights).toHaveProperty('query');
    expect(weights).toHaveProperty('key');
    expect(weights).toHaveProperty('value');
    expect(weights.query).toBeInstanceOf(Float32Array);
    expect(weights.key).toBeInstanceOf(Float32Array);
    expect(weights.value).toBeInstanceOf(Float32Array);
  });

  test('should support causal masking', async () => {
    const causalLayer = new AttentionRoutingLayer({
      numHeads: 2,
      headDim: 32,
      useCausalMask: true
    });
    
    await causalLayer.initialize();

    const input: Tensor = {
      data: new Float32Array([1, 2, 3, 4]),
      shape: [4],
      dtype: 'float32'
    };

    const result = await causalLayer.route(input);
    expect(result.output.data).toBeInstanceOf(Float32Array);
    
    causalLayer.destroy();
  });

  test('should destroy successfully', () => {
    layer.destroy();
    expect(layer.isInitialized()).toBe(false);
    
    const weights = layer.getWeights();
    expect(weights.query).toBeNull();
    expect(weights.key).toBeNull();
    expect(weights.value).toBeNull();
  });
});
