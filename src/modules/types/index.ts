/**
 * Shared types for WebGPU Neural Network & Attention Mechanism Architecture
 * 共享的 WebGPU 神經網絡與注意力機制架構類型定義
 */

/**
 * Tensor data structure for neural computations
 * 神經計算的張量數據結構
 */
export interface Tensor {
  data: Float32Array;
  shape: number[];
  dtype?: 'float32' | 'float16' | 'int32';
}

/**
 * WebGPU compute configuration
 * WebGPU 計算配置
 */
export interface WebGPUConfig {
  device?: GPUDevice;
  adapter?: GPUAdapter;
  preferredFormat?: GPUTextureFormat;
}

/**
 * Neural network layer configuration
 * 神經網絡層配置
 */
export interface LayerConfig {
  inputSize: number;
  outputSize: number;
  activationFunction?: 'relu' | 'sigmoid' | 'tanh' | 'softmax';
  useBias?: boolean;
}

/**
 * Attention mechanism configuration
 * 注意力機制配置
 */
export interface AttentionConfig {
  numHeads: number;
  headDim: number;
  dropoutRate?: number;
  useCausalMask?: boolean;
}

/**
 * Compute endpoint information
 * 計算端點信息
 */
export interface ComputeEndpoint {
  id: string;
  name: string;
  type: 'webgpu' | 'webgl' | 'cpu' | 'wasm';
  status: 'active' | 'inactive' | 'error';
  capabilities?: string[];
}

/**
 * Routing decision for particle language system
 * 粒子語言系統的路由決策
 */
export interface RoutingDecision {
  endpoint: ComputeEndpoint;
  priority: number;
  estimatedLatency?: number;
  confidence?: number;
}

/**
 * Computation result
 * 計算結果
 */
export interface ComputeResult {
  output: Tensor;
  metadata?: {
    executionTime?: number;
    endpointUsed?: string;
    memoryUsed?: number;
  };
}

/**
 * Error information
 * 錯誤信息
 */
export interface ComputeError {
  code: string;
  message: string;
  timestamp: Date;
  context?: Record<string, unknown>;
}
