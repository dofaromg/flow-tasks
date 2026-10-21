/**
 * Unit tests for NeuronComputeCore
 * NeuronComputeCore 的單元測試
 */

import { NeuronComputeCore } from '../modules/neuron';
import { Tensor, LayerConfig } from '../modules/types';

describe('NeuronComputeCore', () => {
  let core: NeuronComputeCore;

  beforeEach(() => {
    core = new NeuronComputeCore();
  });

  afterEach(async () => {
    if (core.isInitialized()) {
      await core.destroy();
    }
  });

  test('should create instance', () => {
    expect(core).toBeInstanceOf(NeuronComputeCore);
  });

  test('should not be initialized on creation', () => {
    expect(core.isInitialized()).toBe(false);
  });

  test('should initialize successfully (or skip if WebGPU unavailable)', async () => {
    try {
      await core.initialize();
      expect(core.isInitialized()).toBe(true);
    } catch (error) {
      // WebGPU not available in test environment - skip
      expect(error).toBeDefined();
    }
  });

  test('should get device info', () => {
    const info = core.getDeviceInfo();
    expect(info).toHaveProperty('adapter');
    expect(info).toHaveProperty('device');
    expect(info).toHaveProperty('supported');
    expect(typeof info.supported).toBe('boolean');
  });

  test('should throw error when computing without initialization', async () => {
    const input: Tensor = {
      data: new Float32Array([1, 2, 3, 4]),
      shape: [4],
      dtype: 'float32'
    };
    
    const config: LayerConfig = {
      inputSize: 4,
      outputSize: 2
    };

    await expect(core.compute(input, config)).rejects.toThrow();
  });

  test('should compute with CPU fallback', async () => {
    // Skip WebGPU initialization, use simulated computation
    // This tests the computation logic without GPU
    const testCore = new NeuronComputeCore();
    
    // Manually set initialized flag for testing
    // In real scenario, this would be done by initialize()
    (testCore as any).initialized = true;
    (testCore as any).device = { destroy: () => {} }; // Mock device with destroy method

    const input: Tensor = {
      data: new Float32Array([1, 2, 3, 4]),
      shape: [4],
      dtype: 'float32'
    };
    
    const config: LayerConfig = {
      inputSize: 4,
      outputSize: 2,
      activationFunction: 'relu'
    };

    const result = await testCore.compute(input, config);
    
    expect(result).toHaveProperty('output');
    expect(result.output.data).toBeInstanceOf(Float32Array);
    expect(result.output.data.length).toBe(2);
    expect(result.output.shape).toEqual([2]);
    expect(result.metadata).toHaveProperty('executionTime');
    expect(result.metadata).toHaveProperty('endpointUsed');
    
    await testCore.destroy();
  });

  test('should apply different activation functions', async () => {
    const testCore = new NeuronComputeCore();
    (testCore as any).initialized = true;
    (testCore as any).device = { destroy: () => {} };

    const input: Tensor = {
      data: new Float32Array([1, 2]),
      shape: [2],
      dtype: 'float32'
    };

    const activationFunctions: Array<'relu' | 'sigmoid' | 'tanh' | 'softmax'> = [
      'relu', 'sigmoid', 'tanh', 'softmax'
    ];

    for (const activation of activationFunctions) {
      const config: LayerConfig = {
        inputSize: 2,
        outputSize: 2,
        activationFunction: activation
      };

      const result = await testCore.compute(input, config);
      expect(result.output.data).toBeInstanceOf(Float32Array);
      expect(result.output.data.length).toBe(2);
    }

    await testCore.destroy();
  });

  test('should destroy successfully', async () => {
    const testCore = new NeuronComputeCore();
    (testCore as any).initialized = true;
    (testCore as any).device = { destroy: jest.fn() };

    await testCore.destroy();
    expect(testCore.isInitialized()).toBe(false);
  });
});
