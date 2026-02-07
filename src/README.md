# WebGPU Neural Network & Attention Mechanism Architecture

WebGPU 神經網絡與注意力機制架構

## 概述 / Overview

This project integrates a **WebGPU-accelerated neural network architecture** with an **intelligent attention-based routing mechanism** for the **Particle Language System (PLS)**. The architecture provides high-performance, distributed computation capabilities across multiple compute endpoints.

本項目整合了**基於 WebGPU 加速的神經網絡架構**與**基於注意力機制的智能路由系統**，為**粒子語言系統 (PLS)** 提供高性能的分佈式計算能力。

## 架構組件 / Architecture Components

### 1. NeuronComputeCore (神經元計算核心)

WebGPU-based neural computation engine that leverages GPU acceleration for high-performance tensor operations.

基於 WebGPU 的神經計算引擎，利用 GPU 加速實現高性能張量運算。

**Features:**
- GPU-accelerated neural network computations
- Support for multiple activation functions (ReLU, Sigmoid, Tanh, Softmax)
- Automatic fallback to CPU when WebGPU is unavailable
- Efficient tensor data management

**Key Methods:**
```typescript
const core = new NeuronComputeCore();
await core.initialize();
const result = await core.compute(inputTensor, layerConfig);
```

### 2. AttentionRoutingLayer (注意力路由層)

Implements multi-head attention mechanism for intelligent computation routing and feature extraction.

實現多頭注意力機制，用於智能計算路由和特徵提取。

**Features:**
- Multi-head scaled dot-product attention
- Causal masking support for autoregressive models
- Self-attention and cross-attention capabilities
- Xavier/Glorot weight initialization

**Key Methods:**
```typescript
const layer = new AttentionRoutingLayer({ numHeads: 4, headDim: 64 });
await layer.initialize();
const result = await layer.computeAttention(query, key, value);
```

### 3. ComputeEndpointManager (計算端點管理器)

Manages multiple compute endpoints (WebGPU, WebGL, CPU, WASM) with automatic detection and load balancing.

管理多個計算端點（WebGPU、WebGL、CPU、WASM），提供自動檢測和負載均衡。

**Features:**
- Automatic endpoint detection and registration
- Capability-based endpoint selection
- Health monitoring and status management
- Support for custom endpoints

**Key Methods:**
```typescript
const manager = new ComputeEndpointManager();
await manager.initialize();
const endpoint = manager.selectBestEndpoint(['neural-compute']);
```

### 4. PLSRoutingEngine (粒子語言系統路由引擎)

Intelligent routing engine that combines attention mechanisms with endpoint management for optimal computation distribution.

智能路由引擎，結合注意力機制和端點管理，實現最優計算分配。

**Features:**
- Attention-based routing decisions
- Multi-endpoint orchestration
- Performance tracking and statistics
- Routing history and analytics

**Key Methods:**
```typescript
const engine = new PLSRoutingEngine();
await engine.initialize();
const decision = await engine.route(inputTensor);
const result = await engine.execute(inputTensor, decision);
```

## 目錄結構 / Directory Structure

```
src/
├── modules/
│   ├── neuron/                    # Neural computation module
│   │   ├── NeuronComputeCore.ts
│   │   └── index.ts
│   ├── attention/                 # Attention mechanism module
│   │   ├── AttentionRoutingLayer.ts
│   │   └── index.ts
│   ├── endpoint/                  # Endpoint management module
│   │   ├── ComputeEndpointManager.ts
│   │   └── index.ts
│   ├── routing/                   # Routing engine module
│   │   ├── PLSRoutingEngine.ts
│   │   └── index.ts
│   └── types/                     # Shared TypeScript types
│       └── index.ts
├── tests/                         # Unit and integration tests
│   ├── NeuronComputeCore.test.ts
│   ├── AttentionRoutingLayer.test.ts
│   ├── ComputeEndpointManager.test.ts
│   ├── PLSRoutingEngine.test.ts
│   └── integration.test.ts
└── index.ts                       # Main module exports
```

## 安裝與使用 / Installation & Usage

### Prerequisites / 先決條件

- Node.js >= 18.x
- npm >= 9.x
- TypeScript >= 5.x
- WebGPU-capable browser (Chrome 113+, Edge 113+) for GPU acceleration

### Installation / 安裝

```bash
# Install dependencies
npm install

# Build the project
npm run build

# Run tests
npm test

# Run tests with coverage
npm run test:coverage

# Run linter
npm run lint
```

### Basic Usage / 基本用法

#### Complete Pipeline Example

```typescript
import { PLSRoutingEngine, Tensor } from './src';

// Initialize the routing engine
const engine = new PLSRoutingEngine();
await engine.initialize();

// Prepare input data
const input: Tensor = {
  data: new Float32Array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]),
  shape: [8],
  dtype: 'float32'
};

// Route the computation
const decision = await engine.route(input);
console.log(`Selected endpoint: ${decision.endpoint.name}`);
console.log(`Priority: ${decision.priority}, Confidence: ${decision.confidence}`);

// Execute the computation
const result = await engine.execute(input, decision);
console.log('Computation result:', result.output.data);
console.log('Execution time:', result.metadata?.executionTime, 'ms');

// Get routing statistics
const stats = engine.getStatistics();
console.log('Routing statistics:', stats);

// Cleanup
await engine.destroy();
```

#### Individual Component Usage

**NeuronComputeCore:**
```typescript
import { NeuronComputeCore, Tensor, LayerConfig } from './src';

const core = new NeuronComputeCore();
await core.initialize();

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

const result = await core.compute(input, config);
```

**AttentionRoutingLayer:**
```typescript
import { AttentionRoutingLayer } from './src';

const layer = new AttentionRoutingLayer({
  numHeads: 4,
  headDim: 64,
  dropoutRate: 0.1,
  useCausalMask: false
});

await layer.initialize();
const result = await layer.route(inputTensor);
```

**ComputeEndpointManager:**
```typescript
import { ComputeEndpointManager } from './src';

const manager = new ComputeEndpointManager();
await manager.initialize();

// Get all available endpoints
const endpoints = manager.getAllEndpoints();

// Select best endpoint for task
const best = manager.selectBestEndpoint(['neural-compute', 'parallel-processing']);

// Check endpoint health
const healthStatus = await manager.healthCheck();
```

## API 文檔 / API Documentation

### Core Types

```typescript
interface Tensor {
  data: Float32Array;
  shape: number[];
  dtype?: 'float32' | 'float16' | 'int32';
}

interface ComputeResult {
  output: Tensor;
  metadata?: {
    executionTime?: number;
    endpointUsed?: string;
    memoryUsed?: number;
  };
}

interface RoutingDecision {
  endpoint: ComputeEndpoint;
  priority: number;
  estimatedLatency?: number;
  confidence?: number;
}
```

For complete API documentation, see the TypeScript type definitions in `src/modules/types/index.ts`.

## 測試 / Testing

### Running Tests

```bash
# Run all tests
npm test

# Run tests in watch mode
npm run test:watch

# Generate coverage report
npm run test:coverage
```

### Test Coverage

The project includes comprehensive unit tests and integration tests:
- NeuronComputeCore: Initialization, computation, activation functions
- AttentionRoutingLayer: Attention mechanisms, weight management
- ComputeEndpointManager: Endpoint detection, selection, health checks
- PLSRoutingEngine: Routing decisions, execution, statistics
- Integration: Complete pipeline, multi-component interactions

## CI/CD 配置 / CI/CD Configuration

The project includes automated CI/CD workflows:

### GitHub Actions Workflows

- **Lint**: Code quality checks with ESLint
- **Build**: TypeScript compilation and Next.js build
- **Test**: Automated test execution with Jest
- **Coverage**: Test coverage reporting

See `.github/workflows/` for workflow configurations.

## 性能優化 / Performance Optimization

### WebGPU Acceleration
- Leverages GPU compute shaders for parallel tensor operations
- Automatic fallback to CPU when GPU unavailable
- Efficient memory management with typed arrays

### Attention Mechanism
- Multi-head attention for parallel processing
- Scaled dot-product attention for numerical stability
- Optional causal masking for autoregressive models

### Endpoint Selection
- Intelligent routing based on capabilities and performance
- Load balancing across multiple compute endpoints
- Health monitoring and automatic failover

## 瀏覽器兼容性 / Browser Compatibility

| Feature | Chrome | Edge | Firefox | Safari |
|---------|--------|------|---------|--------|
| WebGPU  | 113+   | 113+ | Experimental | Experimental |
| WebGL   | ✓      | ✓    | ✓       | ✓      |
| WASM    | ✓      | ✓    | ✓       | ✓      |

**Note**: WebGPU is still in development. The system automatically falls back to CPU computation when WebGPU is unavailable.

## 貢獻 / Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Ensure all tests pass: `npm test`
5. Run linter: `npm run lint`
6. Submit a pull request

## 許可證 / License

This project follows the flow-tasks repository license. See LICENSE for details.

## 聯繫 / Contact

- Author: MRLiou
- Email: z814241@gmail.com
- Repository: https://github.com/dofaromg/flow-tasks

## 更新日誌 / Changelog

### Version 1.0.0 (2026-02-07)

- ✅ Initial implementation of WebGPU Neural Network & Attention Mechanism Architecture
- ✅ Four core components: NeuronComputeCore, AttentionRoutingLayer, ComputeEndpointManager, PLSRoutingEngine
- ✅ Modular architecture with independent components
- ✅ Comprehensive unit tests and integration tests
- ✅ TypeScript type definitions and documentation
- ✅ CI/CD workflow configuration
- ✅ Bilingual documentation (English/Chinese)

---

**Built with ❤️ for the Particle Language System**
