/**
 * NeuronComputeCore - WebGPU-based Neural Computation Core
 * 基於 WebGPU 的神經元計算核心
 * 
 * This module provides GPU-accelerated neural network computations
 * using the WebGPU API for high-performance tensor operations.
 */

import { Tensor, WebGPUConfig, LayerConfig, ComputeResult, ComputeError } from '../types';

export class NeuronComputeCore {
  private device: GPUDevice | null = null;
  private adapter: GPUAdapter | null = null;
  private initialized = false;
  private config: WebGPUConfig;
  private simulatedWeightsCache: Map<string, Float32Array> = new Map();

  constructor(config: WebGPUConfig = {}) {
    this.config = config;
  }

  /**
   * Initialize WebGPU device and adapter
   * 初始化 WebGPU 設備和適配器
   */
  async initialize(): Promise<void> {
    try {
      if (this.initialized) {
        return;
      }

      // Check WebGPU support
      if (typeof navigator === 'undefined' || !navigator.gpu) {
        throw new Error('WebGPU is not supported in this environment');
      }

      // Use provided adapter or request a new one
      this.adapter = this.config.adapter || await navigator.gpu.requestAdapter();
      if (!this.adapter) {
        throw new Error('Failed to get GPU adapter');
      }

      // Use provided device or request a new one
      this.device = this.config.device || await this.adapter.requestDevice();
      if (!this.device) {
        throw new Error('Failed to get GPU device');
      }

      this.initialized = true;
      console.log('NeuronComputeCore initialized successfully');
    } catch (error) {
      throw new Error(`Failed to initialize NeuronComputeCore: ${error}`);
    }
  }

  /**
   * Check if the core is initialized
   * 檢查核心是否已初始化
   */
  isInitialized(): boolean {
    return this.initialized && this.device !== null;
  }

  /**
   * Perform a simple neural network forward pass
   * 執行簡單的神經網絡前向傳播
   */
  async compute(input: Tensor, layerConfig: LayerConfig): Promise<ComputeResult> {
    const startTime = Date.now();

    if (!this.isInitialized()) {
      throw new Error('NeuronComputeCore not initialized. Call initialize() first.');
    }

    try {
      // For now, implement a simple pass-through with basic transformation
      // In a real implementation, this would use WebGPU compute shaders
      const outputData = this.simulateComputation(input, layerConfig);
      
      const output: Tensor = {
        data: outputData,
        shape: [layerConfig.outputSize],
        dtype: 'float32'
      };

      const executionTime = Date.now() - startTime;

      return {
        output,
        metadata: {
          executionTime,
          endpointUsed: 'webgpu',
          memoryUsed: outputData.byteLength
        }
      };
    } catch (error) {
      const baseMessage = error instanceof Error ? error.message : String(error);
      const wrappedError = new Error(
        `Computation failed: ${baseMessage}`
      ) as Error & ComputeError;
      wrappedError.code = 'COMPUTE_ERROR';
      wrappedError.timestamp = new Date();
      throw wrappedError;
    }
  }

  /**
   * Simulate neural computation (placeholder for actual WebGPU shader code)
   * 模擬神經計算（實際 WebGPU 著色器代碼的佔位符）
   */
  private simulateComputation(input: Tensor, config: LayerConfig): Float32Array {
    const { inputSize, outputSize, activationFunction = 'relu' } = config;
    
    // Cache weights per config to ensure deterministic results for the same config
    const cacheKey = `${inputSize}x${outputSize}`;
    let weights = this.simulatedWeightsCache.get(cacheKey);
    if (!weights) {
      weights = new Float32Array(inputSize * outputSize);
      for (let i = 0; i < weights.length; i++) {
        weights[i] = Math.random() * 0.1; // Generated once per config
      }
      this.simulatedWeightsCache.set(cacheKey, weights);
    }

    // Simple linear transformation simulation
    const output = new Float32Array(outputSize);
    for (let i = 0; i < outputSize; i++) {
      let sum = 0;
      for (let j = 0; j < Math.min(inputSize, input.data.length); j++) {
        sum += input.data[j] * weights[i * inputSize + j];
      }
      
      // Apply activation function
      output[i] = this.applyActivation(sum, activationFunction);
    }
    
    return output;
  }

  /**
   * Apply activation function to a value
   * 對值應用激活函數
   */
  private applyActivation(value: number, activation: string): number {
    switch (activation) {
      case 'relu':
        return Math.max(0, value);
      case 'sigmoid':
        return 1 / (1 + Math.exp(-value));
      case 'tanh':
        return Math.tanh(value);
      case 'softmax':
        // Softmax requires all values, simplified here
        return Math.exp(value);
      default:
        return value;
    }
  }

  /**
   * Get device information
   * 獲取設備信息
   */
  getDeviceInfo(): { adapter: string; device: string; supported: boolean } {
    const supported = typeof navigator !== 'undefined' && !!(navigator as any).gpu;

    return {
      adapter: this.adapter ? 'Available' : 'Not available',
      device: this.device ? 'Available' : 'Not available',
      supported
    };
  }

  /**
   * Release GPU resources
   * 釋放 GPU 資源
   */
  async destroy(): Promise<void> {
    if (this.device) {
      this.device.destroy();
      this.device = null;
    }
    this.adapter = null;
    this.initialized = false;
    this.simulatedWeightsCache.clear();
    console.log('NeuronComputeCore destroyed');
  }
}

export default NeuronComputeCore;
