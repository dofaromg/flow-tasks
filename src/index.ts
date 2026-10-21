/**
 * WebGPU Neural Network & Attention Mechanism Architecture
 * WebGPU 神經網絡與注意力機制架構
 * 
 * Main exports for all modules
 * 所有模塊的主要導出
 */

// Core modules
export { NeuronComputeCore } from './modules/neuron';
export { AttentionRoutingLayer } from './modules/attention';
export { ComputeEndpointManager } from './modules/endpoint';
export { PLSRoutingEngine } from './modules/routing';

// Types
export type {
  Tensor,
  WebGPUConfig,
  LayerConfig,
  AttentionConfig,
  ComputeEndpoint,
  RoutingDecision,
  ComputeResult,
  ComputeError
} from './modules/types';
