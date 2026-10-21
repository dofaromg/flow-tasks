/**
 * AttentionRoutingLayer - Neural Attention Mechanism for Routing
 * 神經注意力機制路由層
 * 
 * This module implements attention-based routing for neural computations,
 * enabling dynamic focus on relevant computation paths.
 */

import { Tensor, AttentionConfig, ComputeResult, ComputeError } from '../types';

export class AttentionRoutingLayer {
  private config: AttentionConfig;
  private initialized = false;
  private queryWeights: Float32Array | null = null;
  private keyWeights: Float32Array | null = null;
  private valueWeights: Float32Array | null = null;

  constructor(config: AttentionConfig) {
    this.config = config;
    this.validateConfig();
  }

  /**
   * Validate attention configuration
   * 驗證注意力配置
   */
  private validateConfig(): void {
    const { numHeads, headDim } = this.config;
    if (numHeads <= 0) {
      throw new Error('Number of attention heads must be positive');
    }
    if (headDim <= 0) {
      throw new Error('Head dimension must be positive');
    }
  }

  /**
   * Initialize attention layer with random weights
   * 使用隨機權重初始化注意力層
   */
  async initialize(): Promise<void> {
    try {
      if (this.initialized) {
        return;
      }

      const { numHeads, headDim } = this.config;
      const totalDim = numHeads * headDim;

      // Initialize QKV weight matrices (simplified)
      this.queryWeights = new Float32Array(totalDim * totalDim);
      this.keyWeights = new Float32Array(totalDim * totalDim);
      this.valueWeights = new Float32Array(totalDim * totalDim);

      // Random initialization (Xavier/Glorot uniform)
      const limit = Math.sqrt(6.0 / (totalDim + totalDim));
      this.initializeWeights(this.queryWeights, limit);
      this.initializeWeights(this.keyWeights, limit);
      this.initializeWeights(this.valueWeights, limit);

      this.initialized = true;
      console.log('AttentionRoutingLayer initialized successfully');
    } catch (error) {
      throw new Error(`Failed to initialize AttentionRoutingLayer: ${error}`);
    }
  }

  /**
   * Initialize weights with uniform random values
   * 使用均勻隨機值初始化權重
   */
  private initializeWeights(weights: Float32Array, limit: number): void {
    for (let i = 0; i < weights.length; i++) {
      weights[i] = (Math.random() * 2 - 1) * limit;
    }
  }

  /**
   * Check if the layer is initialized
   * 檢查層是否已初始化
   */
  isInitialized(): boolean {
    return this.initialized;
  }

  /**
   * Compute attention-based routing scores
   * 計算基於注意力的路由分數
   */
  async computeAttention(
    query: Tensor,
    key: Tensor,
    value: Tensor
  ): Promise<ComputeResult> {
    const startTime = Date.now();

    if (!this.isInitialized()) {
      throw new Error('AttentionRoutingLayer not initialized. Call initialize() first.');
    }

    try {
      // Compute attention scores: softmax(QK^T / sqrt(d_k))V
      const attentionScores = this.computeScaledDotProductAttention(query, key, value);

      const output: Tensor = {
        data: attentionScores,
        shape: value.shape,
        dtype: 'float32'
      };

      const executionTime = Date.now() - startTime;

      return {
        output,
        metadata: {
          executionTime,
          endpointUsed: 'attention-layer',
          memoryUsed: attentionScores.byteLength
        }
      };
    } catch (error) {
      const baseMessage =
        error instanceof Error ? error.message : String(error);
      const wrappedError = new Error(
        `Attention computation failed: ${baseMessage}`
      ) as Error & ComputeError;
      wrappedError.code = 'ATTENTION_ERROR';
      wrappedError.timestamp = new Date();
      throw wrappedError;
    }
  }

  /**
   * Compute scaled dot-product attention
   * 計算縮放點積注意力
   */
  private computeScaledDotProductAttention(
    query: Tensor,
    key: Tensor,
    value: Tensor
  ): Float32Array {
    const { headDim, useCausalMask = false } = this.config;
    
    const qLen = query.data.length;
    const kLen = key.data.length;
    const vLen = value.data.length;
    
    // Simplified attention calculation
    const scores = new Float32Array(qLen);
    const scale = 1.0 / Math.sqrt(headDim);

    for (let i = 0; i < qLen; i++) {
      let sum = 0;
      for (let j = 0; j < Math.min(kLen, qLen); j++) {
        // Apply causal mask if needed
        if (useCausalMask && j > i) {
          continue;
        }
        sum += query.data[i] * key.data[j % kLen] * scale;
      }
      scores[i] = sum;
    }

    // Apply softmax
    const softmaxScores = this.softmax(scores);

    // Compute weighted values
    const output = new Float32Array(vLen);
    for (let i = 0; i < vLen; i++) {
      output[i] = softmaxScores[i % softmaxScores.length] * value.data[i];
    }

    return output;
  }

  /**
   * Apply softmax function to an array
   * 對數組應用 softmax 函數
   */
  private softmax(values: Float32Array): Float32Array {
    const length = values.length;

    // Handle empty input gracefully
    if (length === 0) {
      return new Float32Array(0);
    }

    // 1) Find max value without using spread (avoids argument limits)
    let max = values[0];
    for (let i = 1; i < length; i++) {
      const v = values[i];
      if (v > max) {
        max = v;
      }
    }

    // 2) Compute exponentials and their sum
    const result = new Float32Array(length);
    let sum = 0;
    for (let i = 0; i < length; i++) {
      const expValue = Math.exp(values[i] - max);
      result[i] = expValue;
      sum += expValue;
    }

    // 3) Normalize to get probabilities
    if (sum !== 0) {
      for (let i = 0; i < length; i++) {
        result[i] /= sum;
      }
    }

    return result;
  }

  /**
   * Route input through attention mechanism
   * 通過注意力機制路由輸入
   */
  async route(input: Tensor): Promise<ComputeResult> {
    // Use input as Q, K, V for self-attention
    return this.computeAttention(input, input, input);
  }

  /**
   * Get layer configuration
   * 獲取層配置
   */
  getConfig(): AttentionConfig {
    return { ...this.config };
  }

  /**
   * Get attention weights (for inspection/debugging)
   * 獲取注意力權重（用於檢查/調試）
   */
  getWeights(): {
    query: Float32Array | null;
    key: Float32Array | null;
    value: Float32Array | null;
  } {
    return {
      query: this.queryWeights,
      key: this.keyWeights,
      value: this.valueWeights
    };
  }

  /**
   * Release resources
   * 釋放資源
   */
  destroy(): void {
    this.queryWeights = null;
    this.keyWeights = null;
    this.valueWeights = null;
    this.initialized = false;
    console.log('AttentionRoutingLayer destroyed');
  }
}

export default AttentionRoutingLayer;
