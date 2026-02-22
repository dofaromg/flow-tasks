/**
 * Unit tests for ComputeEndpointManager
 * ComputeEndpointManager 的單元測試
 */

import { ComputeEndpointManager } from '../modules/endpoint';
import { ComputeEndpoint } from '../modules/types';

describe('ComputeEndpointManager', () => {
  let manager: ComputeEndpointManager;

  beforeEach(() => {
    manager = new ComputeEndpointManager();
  });

  afterEach(() => {
    if (manager.isInitialized()) {
      manager.destroy();
    }
  });

  test('should create instance', () => {
    expect(manager).toBeInstanceOf(ComputeEndpointManager);
  });

  test('should not be initialized on creation', () => {
    expect(manager.isInitialized()).toBe(false);
  });

  test('should initialize successfully', async () => {
    await manager.initialize();
    expect(manager.isInitialized()).toBe(true);
  });

  test('should detect and register endpoints on initialization', async () => {
    await manager.initialize();
    
    const endpoints = manager.getAllEndpoints();
    expect(endpoints.length).toBeGreaterThan(0);
    
    // CPU endpoint should always be available
    const cpuEndpoint = manager.getEndpoint('cpu-default');
    expect(cpuEndpoint).toBeDefined();
    expect(cpuEndpoint?.type).toBe('cpu');
  });

  test('should register custom endpoint', async () => {
    await manager.initialize();
    
    const customEndpoint: ComputeEndpoint = {
      id: 'custom-test',
      name: 'Custom Test Endpoint',
      type: 'cpu',
      status: 'active',
      capabilities: ['test-capability']
    };

    manager.registerEndpoint(customEndpoint);
    
    const retrieved = manager.getEndpoint('custom-test');
    expect(retrieved).toEqual(customEndpoint);
  });

  test('should not register duplicate endpoint', async () => {
    await manager.initialize();
    
    const endpoint: ComputeEndpoint = {
      id: 'duplicate-test',
      name: 'Duplicate Test',
      type: 'cpu',
      status: 'active'
    };

    manager.registerEndpoint(endpoint);
    
    expect(() => {
      manager.registerEndpoint(endpoint);
    }).toThrow();
  });

  test('should unregister endpoint', async () => {
    await manager.initialize();
    
    const endpoint: ComputeEndpoint = {
      id: 'temp-endpoint',
      name: 'Temporary Endpoint',
      type: 'cpu',
      status: 'active'
    };

    manager.registerEndpoint(endpoint);
    expect(manager.getEndpoint('temp-endpoint')).toBeDefined();
    
    const removed = manager.unregisterEndpoint('temp-endpoint');
    expect(removed).toBe(true);
    expect(manager.getEndpoint('temp-endpoint')).toBeUndefined();
  });

  test('should get endpoints by type', async () => {
    await manager.initialize();
    
    const cpuEndpoints = manager.getEndpointsByType('cpu');
    expect(cpuEndpoints.length).toBeGreaterThan(0);
    expect(cpuEndpoints.every(e => e.type === 'cpu')).toBe(true);
  });

  test('should get endpoints by capability', async () => {
    await manager.initialize();
    
    const endpoint: ComputeEndpoint = {
      id: 'test-cap',
      name: 'Test Capability',
      type: 'cpu',
      status: 'active',
      capabilities: ['special-capability']
    };

    manager.registerEndpoint(endpoint);
    
    const endpoints = manager.getEndpointsByCapability('special-capability');
    expect(endpoints.length).toBe(1);
    expect(endpoints[0].id).toBe('test-cap');
  });

  test('should get active endpoints only', async () => {
    await manager.initialize();
    
    const inactiveEndpoint: ComputeEndpoint = {
      id: 'inactive-test',
      name: 'Inactive Test',
      type: 'cpu',
      status: 'inactive'
    };

    manager.registerEndpoint(inactiveEndpoint);
    
    const activeEndpoints = manager.getActiveEndpoints();
    expect(activeEndpoints.every(e => e.status === 'active')).toBe(true);
    expect(activeEndpoints.find(e => e.id === 'inactive-test')).toBeUndefined();
  });

  test('should select best endpoint without requirements', async () => {
    await manager.initialize();
    
    const bestEndpoint = manager.selectBestEndpoint();
    expect(bestEndpoint).toBeDefined();
    expect(bestEndpoint?.status).toBe('active');
  });

  test('should select endpoint with required capabilities', async () => {
    await manager.initialize();
    
    const endpoint: ComputeEndpoint = {
      id: 'specialized',
      name: 'Specialized Endpoint',
      type: 'cpu',
      status: 'active',
      capabilities: ['neural-compute', 'tensor-ops']
    };

    manager.registerEndpoint(endpoint);
    
    const selected = manager.selectBestEndpoint(['neural-compute', 'tensor-ops']);
    expect(selected?.id).toBe('specialized');
  });

  test('should update endpoint status', async () => {
    await manager.initialize();
    
    const cpuEndpoint = manager.getEndpoint('cpu-default');
    expect(cpuEndpoint?.status).toBe('active');
    
    const updated = manager.updateEndpointStatus('cpu-default', 'inactive');
    expect(updated).toBe(true);
    
    const updatedEndpoint = manager.getEndpoint('cpu-default');
    expect(updatedEndpoint?.status).toBe('inactive');
  });

  test('should get statistics', async () => {
    await manager.initialize();
    
    const stats = manager.getStatistics();
    expect(stats).toHaveProperty('total');
    expect(stats).toHaveProperty('active');
    expect(stats).toHaveProperty('inactive');
    expect(stats).toHaveProperty('error');
    expect(stats).toHaveProperty('byType');
    expect(stats.total).toBeGreaterThan(0);
    expect(typeof stats.byType).toBe('object');
  });

  test('should perform health check', async () => {
    await manager.initialize();
    
    const healthResults = await manager.healthCheck();
    expect(healthResults).toBeInstanceOf(Map);
    expect(healthResults.size).toBeGreaterThan(0);
  });

  test('should destroy successfully', async () => {
    await manager.initialize();
    expect(manager.isInitialized()).toBe(true);
    
    manager.destroy();
    expect(manager.isInitialized()).toBe(false);
    expect(manager.getAllEndpoints().length).toBe(0);
  });
});
