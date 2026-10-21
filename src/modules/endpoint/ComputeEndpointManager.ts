/**
 * ComputeEndpointManager - Manages compute endpoints for distributed computation
 * 計算端點管理器 - 管理分佈式計算的計算端點
 * 
 * This module manages multiple compute endpoints (WebGPU, WebGL, CPU, WASM)
 * and provides load balancing and failover capabilities.
 */

import { ComputeEndpoint } from '../types';

export class ComputeEndpointManager {
  private endpoints: Map<string, ComputeEndpoint> = new Map();
  private initialized = false;

  constructor() {
    // Initialize with empty endpoint registry
  }

  /**
   * Initialize the endpoint manager
   * 初始化端點管理器
   */
  async initialize(): Promise<void> {
    try {
      if (this.initialized) {
        return;
      }

      // Detect and register available compute endpoints
      await this.detectEndpoints();

      this.initialized = true;
      console.log(`ComputeEndpointManager initialized with ${this.endpoints.size} endpoints`);
    } catch (error) {
      throw new Error(`Failed to initialize ComputeEndpointManager: ${error}`);
    }
  }

  /**
   * Detect available compute endpoints
   * 檢測可用的計算端點
   */
  private async detectEndpoints(): Promise<void> {
    // Check for WebGPU support
    if (typeof navigator !== 'undefined' && (navigator as any).gpu) {
      const webgpuEndpoint: ComputeEndpoint = {
        id: 'webgpu-primary',
        name: 'WebGPU Primary',
        type: 'webgpu',
        status: 'active',
        capabilities: ['neural-compute', 'parallel-processing', 'tensor-ops']
      };
      this.endpoints.set(webgpuEndpoint.id, webgpuEndpoint);
    }

    // Check for WebGL support (fallback)
    if (typeof WebGLRenderingContext !== 'undefined') {
      const webglEndpoint: ComputeEndpoint = {
        id: 'webgl-fallback',
        name: 'WebGL Fallback',
        type: 'webgl',
        status: 'active',
        capabilities: ['rendering', 'basic-compute']
      };
      this.endpoints.set(webglEndpoint.id, webglEndpoint);
    }

    // CPU endpoint (always available)
    const cpuEndpoint: ComputeEndpoint = {
      id: 'cpu-default',
      name: 'CPU Default',
      type: 'cpu',
      status: 'active',
      capabilities: ['universal-compute']
    };
    this.endpoints.set(cpuEndpoint.id, cpuEndpoint);

    // Check for WebAssembly support
    if (typeof WebAssembly !== 'undefined') {
      const wasmEndpoint: ComputeEndpoint = {
        id: 'wasm-optimized',
        name: 'WASM Optimized',
        type: 'wasm',
        status: 'active',
        capabilities: ['optimized-compute', 'portable']
      };
      this.endpoints.set(wasmEndpoint.id, wasmEndpoint);
    }
  }

  /**
   * Check if the manager is initialized
   * 檢查管理器是否已初始化
   */
  isInitialized(): boolean {
    return this.initialized;
  }

  /**
   * Register a new compute endpoint
   * 註冊新的計算端點
   */
  registerEndpoint(endpoint: ComputeEndpoint): void {
    if (this.endpoints.has(endpoint.id)) {
      throw new Error(`Endpoint with id '${endpoint.id}' already exists`);
    }
    this.endpoints.set(endpoint.id, endpoint);
    console.log(`Registered endpoint: ${endpoint.name} (${endpoint.id})`);
  }

  /**
   * Unregister a compute endpoint
   * 取消註冊計算端點
   */
  unregisterEndpoint(endpointId: string): boolean {
    const removed = this.endpoints.delete(endpointId);
    if (removed) {
      console.log(`Unregistered endpoint: ${endpointId}`);
    }
    return removed;
  }

  /**
   * Get an endpoint by ID
   * 通過 ID 獲取端點
   */
  getEndpoint(endpointId: string): ComputeEndpoint | undefined {
    return this.endpoints.get(endpointId);
  }

  /**
   * Get all registered endpoints
   * 獲取所有已註冊的端點
   */
  getAllEndpoints(): ComputeEndpoint[] {
    return Array.from(this.endpoints.values());
  }

  /**
   * Get active endpoints
   * 獲取活動端點
   */
  getActiveEndpoints(): ComputeEndpoint[] {
    return Array.from(this.endpoints.values()).filter(
      endpoint => endpoint.status === 'active'
    );
  }

  /**
   * Get endpoints by type
   * 按類型獲取端點
   */
  getEndpointsByType(type: ComputeEndpoint['type']): ComputeEndpoint[] {
    return Array.from(this.endpoints.values()).filter(
      endpoint => endpoint.type === type
    );
  }

  /**
   * Get endpoints by capability
   * 按能力獲取端點
   */
  getEndpointsByCapability(capability: string): ComputeEndpoint[] {
    return Array.from(this.endpoints.values()).filter(
      endpoint => endpoint.capabilities?.includes(capability)
    );
  }

  /**
   * Select best endpoint for a given task
   * 為給定任務選擇最佳端點
   */
  selectBestEndpoint(requiredCapabilities?: string[]): ComputeEndpoint | null {
    const activeEndpoints = this.getActiveEndpoints();
    
    if (activeEndpoints.length === 0) {
      return null;
    }

    // If no capabilities specified, prefer WebGPU > WASM > WebGL > CPU
    if (!requiredCapabilities || requiredCapabilities.length === 0) {
      const preferenceOrder: ComputeEndpoint['type'][] = ['webgpu', 'wasm', 'webgl', 'cpu'];
      for (const type of preferenceOrder) {
        const endpoint = activeEndpoints.find(e => e.type === type);
        if (endpoint) {
          return endpoint;
        }
      }
      return activeEndpoints[0];
    }

    // Find endpoint that supports all required capabilities
    const matchingEndpoints = activeEndpoints.filter(endpoint => {
      const capabilities = endpoint.capabilities || [];
      return requiredCapabilities.every(cap => capabilities.includes(cap));
    });

    return matchingEndpoints.length > 0 ? matchingEndpoints[0] : activeEndpoints[0];
  }

  /**
   * Update endpoint status
   * 更新端點狀態
   */
  updateEndpointStatus(
    endpointId: string,
    status: ComputeEndpoint['status']
  ): boolean {
    const endpoint = this.endpoints.get(endpointId);
    if (!endpoint) {
      return false;
    }
    endpoint.status = status;
    console.log(`Updated endpoint ${endpointId} status to: ${status}`);
    return true;
  }

  /**
   * Get endpoint statistics
   * 獲取端點統計信息
   */
  getStatistics(): {
    total: number;
    active: number;
    inactive: number;
    error: number;
    byType: Record<string, number>;
  } {
    const endpoints = Array.from(this.endpoints.values());
    const stats = {
      total: endpoints.length,
      active: endpoints.filter(e => e.status === 'active').length,
      inactive: endpoints.filter(e => e.status === 'inactive').length,
      error: endpoints.filter(e => e.status === 'error').length,
      byType: {} as Record<string, number>
    };

    endpoints.forEach(endpoint => {
      stats.byType[endpoint.type] = (stats.byType[endpoint.type] || 0) + 1;
    });

    return stats;
  }

  /**
   * Health check for all endpoints
   * 對所有端點進行健康檢查
   */
  async healthCheck(): Promise<Map<string, boolean>> {
    const results = new Map<string, boolean>();
    
    for (const [id, endpoint] of this.endpoints) {
      try {
        // Simple health check - just verify the endpoint exists
        const isHealthy = endpoint.status === 'active';
        results.set(id, isHealthy);
        
        if (!isHealthy && endpoint.status !== 'inactive') {
          this.updateEndpointStatus(id, 'error');
        }
      } catch (error) {
        results.set(id, false);
        this.updateEndpointStatus(id, 'error');
      }
    }

    return results;
  }

  /**
   * Release all resources
   * 釋放所有資源
   */
  destroy(): void {
    this.endpoints.clear();
    this.initialized = false;
    console.log('ComputeEndpointManager destroyed');
  }
}

export default ComputeEndpointManager;
