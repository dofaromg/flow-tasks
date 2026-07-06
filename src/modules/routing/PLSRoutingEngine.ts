/**
 * PLSRoutingEngine - Particle Language System Routing Engine
 * 粒子語言系統路由引擎
 * 
 * This module implements intelligent routing for the Particle Language System,
 * combining attention mechanisms and endpoint management for optimal computation routing.
 */

import { Tensor, RoutingDecision, ComputeEndpoint, ComputeResult } from '../types';
import { AttentionRoutingLayer } from '../attention';
import { ComputeEndpointManager } from '../endpoint';
import { NeuronComputeCore } from '../neuron';

export class PLSRoutingEngine {
  private attentionLayer: AttentionRoutingLayer | null = null;
  private endpointManager: ComputeEndpointManager | null = null;
  private neuronCore: NeuronComputeCore | null = null;
  private initialized = false;
  private routingHistory: RoutingDecision[] = [];
  private maxHistorySize = 100;

  constructor(
    attentionLayer?: AttentionRoutingLayer,
    endpointManager?: ComputeEndpointManager,
    neuronCore?: NeuronComputeCore
  ) {
    this.attentionLayer = attentionLayer || null;
    this.endpointManager = endpointManager || null;
    this.neuronCore = neuronCore || null;
  }

  /**
   * Initialize the routing engine
   * 初始化路由引擎
   */
  async initialize(): Promise<void> {
    try {
      if (this.initialized) {
        return;
      }

      // Initialize attention layer if not provided
      if (!this.attentionLayer) {
        this.attentionLayer = new AttentionRoutingLayer({
          numHeads: 4,
          headDim: 64,
          dropoutRate: 0.1
        });
      }
      if (!this.attentionLayer.isInitialized()) {
        await this.attentionLayer.initialize();
      }

      // Initialize endpoint manager if not provided
      if (!this.endpointManager) {
        this.endpointManager = new ComputeEndpointManager();
      }
      if (!this.endpointManager.isInitialized()) {
        await this.endpointManager.initialize();
      }

      // Initialize neuron core if not provided (optional)
      if (!this.neuronCore) {
        this.neuronCore = new NeuronComputeCore();
      }
      if (!this.neuronCore.isInitialized()) {
        try {
          await this.neuronCore.initialize();
        } catch (error) {
          console.warn('WebGPU not available, neuron core initialization skipped:', error);
        }
      }

      this.initialized = true;
      console.log('PLSRoutingEngine initialized successfully');
    } catch (error) {
      throw new Error(`Failed to initialize PLSRoutingEngine: ${error}`);
    }
  }

  /**
   * Check if the engine is initialized
   * 檢查引擎是否已初始化
   */
  isInitialized(): boolean {
    return this.initialized;
  }

  /**
   * Route a computation task to the best endpoint
   * 將計算任務路由到最佳端點
   */
  async route(
    input: Tensor,
    requiredCapabilities?: string[]
  ): Promise<RoutingDecision> {
    if (!this.isInitialized()) {
      throw new Error('PLSRoutingEngine not initialized. Call initialize() first.');
    }

    try {
      // Use attention mechanism to compute routing scores
      const attentionResult = await this.attentionLayer!.route(input);
      
      // Get attention scores and use them to influence endpoint selection
      const attentionScores = attentionResult.output.data;
      const avgAttentionScore = this.calculateAverage(attentionScores);

      // Select best endpoint based on requirements and attention scores
      const selectedEndpoint = this.endpointManager!.selectBestEndpoint(requiredCapabilities);
      
      if (!selectedEndpoint) {
        throw new Error('No suitable endpoint found');
      }

      // Calculate routing decision with priority influenced by attention
      const decision: RoutingDecision = {
        endpoint: selectedEndpoint,
        priority: this.calculatePriority(selectedEndpoint, avgAttentionScore),
        estimatedLatency: this.estimateLatency(selectedEndpoint),
        confidence: avgAttentionScore
      };

      // Record decision in history
      this.addToHistory(decision);

      console.log(
        `Routed to endpoint: ${selectedEndpoint.name} (confidence: ${decision.confidence?.toFixed(3)})`
      );

      return decision;
    } catch (error) {
      throw new Error(`Routing failed: ${error}`);
    }
  }

  /**
   * Execute a routed computation
   * 執行路由的計算
   */
  async execute(
    input: Tensor,
    decision: RoutingDecision
  ): Promise<ComputeResult> {
    if (!this.isInitialized()) {
      throw new Error('PLSRoutingEngine not initialized. Call initialize() first.');
    }

    const startTime = Date.now();

    try {
      // Execute based on endpoint type
      let result: ComputeResult;

      switch (decision.endpoint.type) {
        case 'webgpu':
          if (this.neuronCore && this.neuronCore.isInitialized()) {
            result = await this.neuronCore.compute(input, {
              inputSize: input.data.length,
              outputSize: input.data.length,
              activationFunction: 'relu'
            });
          } else {
            // Fallback to CPU
            result = this.executeCPU(input);
          }
          break;

        case 'wasm':
        case 'webgl':
        case 'cpu':
        default:
          result = this.executeCPU(input);
          break;
      }

      const executionTime = Date.now() - startTime;
      
      // Update result metadata
      result.metadata = {
        ...result.metadata,
        executionTime,
        endpointUsed: decision.endpoint.id
      };

      return result;
    } catch (error) {
      throw new Error(`Execution failed: ${error}`);
    }
  }

  /**
   * Execute computation on CPU (fallback)
   * 在 CPU 上執行計算（備用）
   */
  private executeCPU(input: Tensor): ComputeResult {
    // Simple pass-through for CPU fallback
    return {
      output: {
        data: new Float32Array(input.data),
        shape: input.shape,
        dtype: input.dtype || 'float32'
      },
      metadata: {
        endpointUsed: 'cpu-fallback'
      }
    };
  }

  /**
   * Calculate priority score for an endpoint
   * 計算端點的優先級分數
   */
  private calculatePriority(endpoint: ComputeEndpoint, attentionScore: number): number {
    // Base priority based on endpoint type
    const typePriority: Record<string, number> = {
      webgpu: 1.0,
      wasm: 0.8,
      webgl: 0.6,
      cpu: 0.4
    };

    const basePriority = typePriority[endpoint.type] || 0.5;
    
    // Combine with attention score
    return (basePriority * 0.6 + attentionScore * 0.4);
  }

  /**
   * Estimate latency for an endpoint (ms)
   * 估計端點的延遲（毫秒）
   */
  private estimateLatency(endpoint: ComputeEndpoint): number {
    const latencyMap: Record<string, number> = {
      webgpu: 5,
      wasm: 10,
      webgl: 15,
      cpu: 20
    };

    return latencyMap[endpoint.type] || 20;
  }

  /**
   * Calculate average of array values
   * 計算數組值的平均值
   */
  private calculateAverage(values: Float32Array): number {
    if (values.length === 0) return 0;

    let sum = 0;
    for (let i = 0; i < values.length; i++) {
      sum += values[i];
    }
    return sum / values.length;
  }

  /**
   * Add routing decision to history
   * 將路由決策添加到歷史記錄
   */
  private addToHistory(decision: RoutingDecision): void {
    this.routingHistory.push(decision);
    
    // Maintain maximum history size
    if (this.routingHistory.length > this.maxHistorySize) {
      this.routingHistory.shift();
    }
  }

  /**
   * Get routing history
   * 獲取路由歷史
   */
  getRoutingHistory(): RoutingDecision[] {
    return [...this.routingHistory];
  }

  /**
   * Get routing statistics
   * 獲取路由統計信息
   */
  getStatistics(): {
    totalRoutings: number;
    endpointUsage: Record<string, number>;
    averageConfidence: number;
    averagePriority: number;
  } {
    const endpointUsage: Record<string, number> = {};
    let totalConfidence = 0;
    let totalPriority = 0;

    this.routingHistory.forEach(decision => {
      const endpointId = decision.endpoint.id;
      endpointUsage[endpointId] = (endpointUsage[endpointId] || 0) + 1;
      totalConfidence += decision.confidence || 0;
      totalPriority += decision.priority;
    });

    return {
      totalRoutings: this.routingHistory.length,
      endpointUsage,
      averageConfidence: this.routingHistory.length > 0 
        ? totalConfidence / this.routingHistory.length 
        : 0,
      averagePriority: this.routingHistory.length > 0 
        ? totalPriority / this.routingHistory.length 
        : 0
    };
  }

  /**
   * Clear routing history
   * 清除路由歷史
   */
  clearHistory(): void {
    this.routingHistory = [];
    console.log('Routing history cleared');
  }

  /**
   * Get all components
   * 獲取所有組件
   */
  getComponents(): {
    attentionLayer: AttentionRoutingLayer | null;
    endpointManager: ComputeEndpointManager | null;
    neuronCore: NeuronComputeCore | null;
  } {
    return {
      attentionLayer: this.attentionLayer,
      endpointManager: this.endpointManager,
      neuronCore: this.neuronCore
    };
  }

  /**
   * Release all resources
   * 釋放所有資源
   */
  async destroy(): Promise<void> {
    this.attentionLayer?.destroy();
    this.endpointManager?.destroy();
    if (this.neuronCore) {
      await this.neuronCore.destroy();
    }
    
    this.routingHistory = [];
    this.initialized = false;
    console.log('PLSRoutingEngine destroyed');
  }
}

export default PLSRoutingEngine;
