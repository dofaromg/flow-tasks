/**
 * MrLiouWord Particle Chat v4.2
 * 
 * 🔧 完整整合版 - 從 Notion 架構文檔完整實現
 * 
 * 整合內容：
 * - 📜 RootLaw v1 (LAW-0 ~ LAW-42)
 * - 🧠 邊緣記憶體模組 (Edge Memory Module)
 * - 🔌 粒子系統架構 (13 Workers 整合)
 * - 🔮 黃金頻率常數 PHI = 1.618
 * - 🔗 ParticleRPC 跨粒子通信
 * - 📊 記憶體一致性協議
 * - 🏗️ 結構性記憶系統
 * 
 * origin_signature: MrLiouWord
 * version: 4.2.0
 */

// ============================================
// LAW-0: 起源簽名律 (Origin Signature Law)
// ============================================

const ORIGIN_SIGNATURE = "MrLiouWord";
const VERSION = "4.2.0";

function validateOriginSignature(signature) {
  return signature === ORIGIN_SIGNATURE;
}

// ============================================
// 黃金頻率常數 (Golden Frequency Constants)
// ============================================

const PHI = 1.618033988749895;

const FREQUENCIES = {
  L0: 1.000,    // 基礎層 (Edge Cache)
  L1: 1.618,    // 感知層
  L2: 2.618,    // 處理層
  L3: 4.236,    // 記憶層
  L4: 6.854,    // 推理層
  L5: 11.09,    // 整合層
  L6: 17.94,    // 輸出層
  L7: 29.03,    // 介面層
  'L∞': 227.34  // 無限層
};

// ============================================
// 記憶體指令集 (Memory Instructions)
// 來自：邊緣記憶體模組
// ============================================

const MEMORY_INSTRUCTIONS = {
  MEM_ALLOC:  0x2001,  // 分配記憶體
  MEM_FREE:   0x2002,  // 釋放記憶體
  MEM_SYNC:   0x2003,  // 同步記憶體
  MEM_CACHE:  0x2004,  // 快取記憶體
  MEM_COHERE: 0x2005   // 記憶體一致性
};

// ============================================
// 粒子類型定義 (11 種 - 完整版)
// 來自：完整部署記錄
// ============================================

const PARTICLE_TYPES = {
  SEED:         { code: 0x01, name: 'Seed', desc: '生成型，高熵，自擴展' },
  FLOW:         { code: 0x02, name: 'Flow', desc: '處理型，數據轉換' },
  CONTAINER:    { code: 0x03, name: 'Container', desc: '組織型，封裝結構' },
  TRANSFORM:    { code: 0x04, name: 'Transform', desc: '形態變化' },
  GATE:         { code: 0x05, name: 'Gate', desc: '控制和調節' },
  STORAGE:      { code: 0x06, name: 'Storage', desc: '持久化存儲' },
  PERSONA:      { code: 0x07, name: 'Persona', desc: '表達風格' },
  BRIDGE:       { code: 0x08, name: 'Bridge', desc: '外部整合' },
  IDENTITY:     { code: 0x09, name: 'Identity', desc: '用戶識別' },
  SIGNAL:       { code: 0x0A, name: 'Signal', desc: '通知事件' },
  MEMORY:       { code: 0x20, name: 'Memory', desc: '記憶粒子' },
  DISTRIBUTION: { code: 0x0B, name: 'Distribution', desc: '內容分享' }
};

// ============================================
// 邊緣記憶體快取系統 (Edge Memory Cache)
// 來自：邊緣記憶體模組 - 完整實現
// ============================================

class EdgeMemoryCache {
  constructor() {
    // 四層快取結構
    this.l0_cache = new Map(); // L0_EDGE_CACHE - 邊緣節點快取（最快）
    this.l1_cache = new Map(); // L1_CLUSTER_CACHE - 叢集級快取
    this.l2_cache = new Map(); // L2_REGION_CACHE - 區域級快取
    this.l3_store = new Map(); // L3_GLOBAL_STORE - 全域儲存（最慢）
    
    this.metrics = { 
      hits: { L0: 0, L1: 0, L2: 0, L3: 0 }, 
      misses: 0,
      allocations: 0,
      frees: 0
    };
    
    this.maxSize = { L0: 100, L1: 500, L2: 2000, L3: 10000 };
    this.ttl = { 
      L0: 60000,     // 1 分鐘
      L1: 300000,    // 5 分鐘
      L2: 1800000,   // 30 分鐘
      L3: 86400000   // 24 小時
    };
    
    this.origin_signature = ORIGIN_SIGNATURE;
  }

  // LAW-1: 記憶體守恆律
  validateMemoryConservation() {
    const total = this.l0_cache.size + this.l1_cache.size + 
                  this.l2_cache.size + this.l3_store.size;
    return total <= (this.maxSize.L0 + this.maxSize.L1 + this.maxSize.L2 + this.maxSize.L3);
  }

  generateKey(input) {
    // SimHash64 風格的 key 生成
    let hash = 0n;
    const str = typeof input === 'string' ? input : JSON.stringify(input);
    for (let i = 0; i < str.length; i++) {
      hash = ((hash << 5n) - hash) ^ BigInt(str.charCodeAt(i));
    }
    return hash.toString(16).padStart(16, '0').slice(0, 16);
  }

  async get(key) {
    const now = Date.now();

    // L0 邊緣快取 - 最快
    const l0Entry = this.l0_cache.get(key);
    if (l0Entry && now - l0Entry.timestamp < this.ttl.L0) {
      this.metrics.hits.L0++;
      return { data: l0Entry.data, layer: 'L0', latency: 1 };
    }

    // L1 叢集快取
    const l1Entry = this.l1_cache.get(key);
    if (l1Entry && now - l1Entry.timestamp < this.ttl.L1) {
      this.metrics.hits.L1++;
      this.promoteToL0(key, l1Entry.data);
      return { data: l1Entry.data, layer: 'L1', latency: 5 };
    }

    // L2 區域快取
    const l2Entry = this.l2_cache.get(key);
    if (l2Entry && now - l2Entry.timestamp < this.ttl.L2) {
      this.metrics.hits.L2++;
      this.promoteToL1(key, l2Entry.data);
      return { data: l2Entry.data, layer: 'L2', latency: 20 };
    }

    // L3 全域儲存
    const l3Entry = this.l3_store.get(key);
    if (l3Entry && now - l3Entry.timestamp < this.ttl.L3) {
      this.metrics.hits.L3++;
      this.promoteToL2(key, l3Entry.data);
      return { data: l3Entry.data, layer: 'L3', latency: 100 };
    }

    this.metrics.misses++;
    return null;
  }

  set(key, data, layer = 'L2') {
    const entry = { 
      data, 
      timestamp: Date.now(),
      origin_signature: this.origin_signature
    };
    
    this.metrics.allocations++;
    
    switch (layer) {
      case 'L0':
        this.enforceMaxSize(this.l0_cache, this.maxSize.L0);
        this.l0_cache.set(key, entry);
        break;
      case 'L1':
        this.enforceMaxSize(this.l1_cache, this.maxSize.L1);
        this.l1_cache.set(key, entry);
        break;
      case 'L3':
        this.enforceMaxSize(this.l3_store, this.maxSize.L3);
        this.l3_store.set(key, entry);
        break;
      default:
        this.enforceMaxSize(this.l2_cache, this.maxSize.L2);
        this.l2_cache.set(key, entry);
    }
    
    return true;
  }

  promoteToL0(key, data) {
    this.enforceMaxSize(this.l0_cache, this.maxSize.L0);
    this.l0_cache.set(key, { data, timestamp: Date.now(), origin_signature: this.origin_signature });
  }

  promoteToL1(key, data) {
    this.enforceMaxSize(this.l1_cache, this.maxSize.L1);
    this.l1_cache.set(key, { data, timestamp: Date.now(), origin_signature: this.origin_signature });
  }

  promoteToL2(key, data) {
    this.enforceMaxSize(this.l2_cache, this.maxSize.L2);
    this.l2_cache.set(key, { data, timestamp: Date.now(), origin_signature: this.origin_signature });
  }

  enforceMaxSize(cache, maxSize) {
    if (cache.size >= maxSize) {
      const deleteCount = Math.floor(maxSize * 0.2);
      const keys = Array.from(cache.keys()).slice(0, deleteCount);
      keys.forEach(k => {
        cache.delete(k);
        this.metrics.frees++;
      });
    }
  }

  // 記憶體一致性檢查 (MEM_COHERE)
  async checkCoherence() {
    return {
      score: this.validateMemoryConservation() ? 1.0 : 0.5,
      layers: {
        L0: this.l0_cache.size,
        L1: this.l1_cache.size,
        L2: this.l2_cache.size,
        L3: this.l3_store.size
      },
      origin_signature: this.origin_signature
    };
  }

  getMetrics() {
    const total = this.metrics.hits.L0 + this.metrics.hits.L1 + 
                  this.metrics.hits.L2 + this.metrics.hits.L3 + this.metrics.misses;
    const hitTotal = this.metrics.hits.L0 + this.metrics.hits.L1 + 
                     this.metrics.hits.L2 + this.metrics.hits.L3;
    return {
      ...this.metrics,
      total,
      hitRate: total > 0 ? (hitTotal / total * 100).toFixed(2) + '%' : '0%',
      cacheSize: {
        L0: this.l0_cache.size,
        L1: this.l1_cache.size,
        L2: this.l2_cache.size,
        L3: this.l3_store.size
      },
      memoryConservation: this.validateMemoryConservation(),
      origin_signature: this.origin_signature
    };
  }
}

const edgeCache = new EdgeMemoryCache();

// ============================================
// SimHash64 引擎 (優化版)
// ============================================

class SimHash64Engine {
  constructor() {
    this.fingerprints = new Map();
    this.origin_signature = ORIGIN_SIGNATURE;
  }

  generate(text) {
    const features = this.extractFeatures(text);
    let hash = 0n;
    
    for (const feature of features) {
      let featureHash = 0n;
      for (let i = 0; i < feature.length; i++) {
        featureHash = ((featureHash << 5n) - featureHash) ^ BigInt(feature.charCodeAt(i));
      }
      hash ^= featureHash;
    }
    
    return hash.toString(16).padStart(16, '0').slice(0, 16);
  }

  extractFeatures(text) {
    const ngrams = [];
    const words = text.split(/\s+/);
    ngrams.push(...words);
    for (let i = 0; i < words.length - 1; i++) {
      ngrams.push(words[i] + '_' + words[i + 1]);
    }
    return ngrams;
  }

  similarity(hash1, hash2) {
    const h1 = BigInt('0x' + hash1);
    const h2 = BigInt('0x' + hash2);
    const xor = h1 ^ h2;
    
    let distance = 0;
    let n = xor;
    while (n > 0n) {
      distance += Number(n & 1n);
      n >>= 1n;
    }
    
    return 1 - distance / 64;
  }

  isDuplicate(hash1, hash2, threshold = 0.9) {
    return this.similarity(hash1, hash2) >= threshold;
  }
}

const simHashEngine = new SimHash64Engine();

// ============================================
// δP₀ 粒子狀態引擎
// ============================================

class DeltaP0Engine {
  constructor() {
    this.stateHistory = [];
    this.maxHistory = 100;
    this.origin_signature = ORIGIN_SIGNATURE;
  }

  generate() {
    const chars = 'abcdef0123456789';
    const state = 'δP₀:' + Array.from({ length: 8 }, () => 
      chars[Math.floor(Math.random() * chars.length)]
    ).join('');
    
    this.stateHistory.push({
      state,
      timestamp: Date.now(),
      frequency: FREQUENCIES.L0 * PHI
    });

    if (this.stateHistory.length > this.maxHistory) {
      this.stateHistory.shift();
    }

    return state;
  }

  getRecentStates(count = 10) {
    return this.stateHistory.slice(-count);
  }
}

const deltaP0Engine = new DeltaP0Engine();

// ============================================
// ParticleRPC - 跨粒子通信系統
// 來自：粒子系統架構文檔
// ============================================

class ParticleRPC {
  constructor() {
    this.origin_signature = ORIGIN_SIGNATURE;
    this.callLog = [];
  }

  async call(target, method, params) {
    const timestamp = Date.now();
    const callId = `rpc_${timestamp}_${Math.random().toString(36).slice(2, 8)}`;
    
    const request = {
      id: callId,
      origin_signature: this.origin_signature,
      target,
      method,
      params,
      timestamp
    };

    this.callLog.push(request);

    // 如果是已部署的 Worker，發送實際請求
    const workerUrl = DEPLOYED_WORKERS[target];
    if (workerUrl) {
      try {
        const response = await fetch(`${workerUrl}/${method}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(params)
        });
        return await response.json();
      } catch (error) {
        return { error: error.message, callId };
      }
    }

    return { error: 'Worker not found', target, callId };
  }

  getCallLog(limit = 20) {
    return this.callLog.slice(-limit);
  }
}

const particleRPC = new ParticleRPC();

// ============================================
// 已部署 Workers (13 個)
// 來自：完整部署記錄
// ============================================

const DEPLOYED_WORKERS = {
  // Phase 1 - 核心功能
  search:     'https://particle-search.z814241.workers.dev',
  memory:     'https://particle-memory.z814241.workers.dev',
  chat:       'https://particle-chat.z814241.workers.dev',
  research:   'https://particle-research.z814241.workers.dev',
  
  // Phase 2 - 擴展功能
  project:    'https://particle-project.z814241.workers.dev',
  artifact:   'https://particle-artifact.z814241.workers.dev',
  config:     'https://particle-config.z814241.workers.dev',
  file:       'https://particle-file.z814241.workers.dev',
  
  // Phase 3 - 完整功能
  style:      'https://particle-style.z814241.workers.dev',
  connector:  'https://particle-connector.z814241.workers.dev',
  user:       'https://particle-user.z814241.workers.dev',
  notify:     'https://particle-notify.z814241.workers.dev',
  share:      'https://particle-share.z814241.workers.dev'
};

// ============================================
// 結構性記憶系統
// 來自：邊緣記憶體模組 - 母體記憶核心
// ============================================

class StructuralMemory {
  constructor() {
    this.functionTrees = new Map();
    this.reconstructionFlows = new Map();
    this.origin_signature = ORIGIN_SIGNATURE;
  }

  // 快照不是內容，是函數
  storeAsStructure(content) {
    const snapshotId = `snapshot_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
    
    const functionTree = this.extractFunctionTree(content);
    const flow = this.extractReconstructionFlow(content);
    
    this.functionTrees.set(snapshotId, functionTree);
    this.reconstructionFlows.set(snapshotId, flow);
    
    return {
      snapshotId,
      treeDepth: functionTree.depth,
      flowSteps: flow.steps.length,
      origin_signature: this.origin_signature
    };
  }

  extractFunctionTree(content) {
    // 提取內容的函數樹結構
    const words = typeof content === 'string' ? content.split(/\s+/) : [];
    return {
      depth: Math.ceil(Math.log2(words.length + 1)),
      nodes: words.length,
      rootHash: simHashEngine.generate(typeof content === 'string' ? content : JSON.stringify(content))
    };
  }

  extractReconstructionFlow(content) {
    // 提取重建流程
    return {
      steps: [
        { action: 'parse', target: 'input' },
        { action: 'tokenize', target: 'content' },
        { action: 'reconstruct', target: 'output' }
      ],
      phi: PHI
    };
  }

  reconstruct(snapshotId) {
    const tree = this.functionTrees.get(snapshotId);
    const flow = this.reconstructionFlows.get(snapshotId);
    
    if (!tree || !flow) {
      return { error: 'Snapshot not found', snapshotId };
    }
    
    return {
      snapshotId,
      reconstructed: true,
      tree,
      flow,
      origin_signature: this.origin_signature
    };
  }
}

const structuralMemory = new StructuralMemory();

// ============================================
// 認知模式 (Cognitive Modes)
// ============================================

const COGNITIVE_MODES = {
  quick: {
    name: '快速模式',
    frequency: FREQUENCIES.L1,
    particleType: PARTICLE_TYPES.SEED,
    prompt: '簡潔快速回答，聚焦核心'
  },
  balanced: {
    name: '平衡模式',
    frequency: FREQUENCIES.L3,
    particleType: PARTICLE_TYPES.FLOW,
    prompt: '平衡深度與效率'
  },
  deep: {
    name: '深度模式',
    frequency: FREQUENCIES.L5,
    particleType: PARTICLE_TYPES.CONTAINER,
    prompt: '深入分析，全面思考'
  },
  creative: {
    name: '創意模式',
    frequency: FREQUENCIES.L7,
    particleType: PARTICLE_TYPES.TRANSFORM,
    prompt: '發散思維，創意解答'
  },
  memory: {
    name: '記憶模式',
    frequency: FREQUENCIES.L4,
    particleType: PARTICLE_TYPES.MEMORY,
    prompt: '調用記憶，關聯分析'
  }
};

// ============================================
// 連接器系統 (Connectors)
// ============================================

const ConnectorRegistry = {
  sources: new Map(),
  
  registerSource(name, config) {
    this.sources.set(name, {
      name,
      baseURL: config.baseURL,
      headers: config.headers || {},
      timeout: config.timeout || 10000,
      particleType: config.particleType || PARTICLE_TYPES.BRIDGE
    });
  },
  
  getSource(name) {
    return this.sources.get(name);
  }
};

// 初始化連接器
ConnectorRegistry.registerSource('weather', {
  baseURL: 'https://wttr.in',
  particleType: PARTICLE_TYPES.SEED
});
ConnectorRegistry.registerSource('time', {
  baseURL: 'https://worldtimeapi.org/api',
  particleType: PARTICLE_TYPES.FLOW
});
ConnectorRegistry.registerSource('wikipedia', {
  baseURL: 'https://zh.wikipedia.org/api/rest_v1',
  particleType: PARTICLE_TYPES.SEED
});
ConnectorRegistry.registerSource('exchange', {
  baseURL: 'https://api.exchangerate-api.com/v4',
  particleType: PARTICLE_TYPES.FLOW
});

const Connectors = {
  weather: {
    description: '查詢天氣資訊',
    source: 'weather',
    params: ['city'],
    cacheTTL: 600000,
    async execute(params) {
      const city = params.city || 'Taipei';
      const response = await fetch(`https://wttr.in/${encodeURIComponent(city)}?format=j1`);
      return await response.json();
    }
  },
  time: {
    description: '查詢世界時間',
    source: 'time',
    params: ['timezone'],
    cacheTTL: 60000,
    async execute(params) {
      const tz = params.timezone || 'Asia/Taipei';
      const response = await fetch(`https://worldtimeapi.org/api/timezone/${tz}`);
      return await response.json();
    }
  },
  wikipedia: {
    description: '搜尋維基百科',
    source: 'wikipedia',
    params: ['query'],
    cacheTTL: 3600000,
    async execute(params) {
      const query = params.query || '';
      const response = await fetch(
        `https://zh.wikipedia.org/api/rest_v1/page/summary/${encodeURIComponent(query)}`
      );
      return await response.json();
    }
  },
  exchange: {
    description: '查詢匯率',
    source: 'exchange',
    params: ['base'],
    cacheTTL: 3600000,
    async execute(params) {
      const base = params.base || 'USD';
      const response = await fetch(`https://api.exchangerate-api.com/v4/latest/${base}`);
      return await response.json();
    }
  },
  // 整合已部署 Workers
  particleSearch: {
    description: '粒子搜尋',
    source: 'particle',
    params: ['query'],
    cacheTTL: 300000,
    async execute(params) {
      return await particleRPC.call('search', 'search', params);
    }
  },
  particleMemory: {
    description: '粒子記憶',
    source: 'particle',
    params: ['query', 'layer'],
    cacheTTL: 600000,
    async execute(params) {
      return await particleRPC.call('memory', 'retrieve', params);
    }
  }
};

async function executeConnector(connectorName, params) {
  const connector = Connectors[connectorName];
  if (!connector) {
    return { error: `Connector '${connectorName}' not found` };
  }

  const cacheKey = edgeCache.generateKey({ connector: connectorName, params });
  const cached = await edgeCache.get(cacheKey);
  
  if (cached) {
    return { ...cached.data, _cached: true, _cacheLayer: cached.layer };
  }

  try {
    const result = await connector.execute(params);
    edgeCache.set(cacheKey, result, 'L1');
    return result;
  } catch (error) {
    return { error: error.message };
  }
}

function detectToolCalls(message) {
  const toolCalls = [];
  const lowerMessage = message.toLowerCase();
  
  if (lowerMessage.includes('天氣') || lowerMessage.includes('weather')) {
    const cityMatch = message.match(/([台台北高雄台中|Taipei|Tokyo|New York|London]+)/i);
    toolCalls.push({
      name: 'weather',
      params: { city: cityMatch?.[1] || 'Taipei' },
      particleType: PARTICLE_TYPES.SEED
    });
  }
  
  if (lowerMessage.includes('時間') || lowerMessage.includes('time') || lowerMessage.includes('幾點')) {
    toolCalls.push({
      name: 'time',
      params: { timezone: 'Asia/Taipei' },
      particleType: PARTICLE_TYPES.FLOW
    });
  }
  
  if (lowerMessage.includes('維基') || lowerMessage.includes('wiki') || lowerMessage.includes('什麼是')) {
    const queryMatch = message.match(/(?:什麼是|wiki|維基)[\s:：]*([^\s?？]+)/i);
    if (queryMatch) {
      toolCalls.push({
        name: 'wikipedia',
        params: { query: queryMatch[1] },
        particleType: PARTICLE_TYPES.SEED
      });
    }
  }
  
  if (lowerMessage.includes('匯率') || lowerMessage.includes('exchange')) {
    toolCalls.push({
      name: 'exchange',
      params: { base: 'USD' },
      particleType: PARTICLE_TYPES.FLOW
    });
  }

  return toolCalls;
}

// ============================================
// Chat Handler (核心)
// ============================================

async function handleChat(request, env) {
  const startTime = Date.now();
  
  try {
    const body = await request.json();
    const { message, mode = 'balanced', chat_id, use_connectors = true } = body;

    if (!message) {
      return Response.json({ error: 'Message required' }, { status: 400 });
    }

    // 生成粒子狀態
    const simhash64 = simHashEngine.generate(message);
    const deltaP0 = deltaP0Engine.generate();
    
    // 儲存結構性記憶
    const memorySnapshot = structuralMemory.storeAsStructure(message);
    
    // 檢查快取 (相似問題)
    const responseCacheKey = edgeCache.generateKey({ message, mode });
    const cachedResponse = await edgeCache.get(responseCacheKey);
    
    if (cachedResponse && simHashEngine.similarity(
      cachedResponse.data.simhash64, simhash64) > 0.95) {
      return Response.json({
        ...cachedResponse.data,
        _cached: true,
        _cacheLayer: cachedResponse.layer,
        _latency: Date.now() - startTime
      });
    }

    // 工具調用
    let toolResults = [];
    if (use_connectors) {
      const toolCalls = detectToolCalls(message);
      if (toolCalls.length > 0) {
        const results = await Promise.all(
          toolCalls.map(async (tool) => ({
            tool: tool.name,
            params: tool.params,
            particleType: tool.particleType?.name,
            result: await executeConnector(tool.name, tool.params)
          }))
        );
        toolResults = results;
      }
    }

    // 構建 AI Prompt
    const modeConfig = COGNITIVE_MODES[mode] || COGNITIVE_MODES.balanced;
    
    let systemPrompt = `你是 Mr.liou_夥伴，MrLiouWord 粒子系統的 AI 助手。

【系統常數】
- origin_signature: ${ORIGIN_SIGNATURE}
- version: ${VERSION}
- 黃金頻率: PHI = ${PHI}
- 當前頻率層: L${Object.entries(FREQUENCIES).find(([k, v]) => v === modeConfig.frequency)?.[0] || '3'}
- 粒子類型: ${modeConfig.particleType.name}

【律法遵守】
- LAW-0: 起源簽名律 (所有實體攜帶 origin_signature)
- LAW-1: 記憶體守恆律 (記憶總量守恆)
- LAW-2: 記憶體單調性律 (Gravity Model)

【認知模式】
- 模式: ${modeConfig.name}
- 指令: ${modeConfig.prompt}

【已部署粒子】
${Object.keys(DEPLOYED_WORKERS).join(', ')}

保持簡潔、專業、友善。怎麼過去就怎麼回來。`;

    if (toolResults.length > 0) {
      systemPrompt += `\n\n【連接器即時數據】\n`;
      toolResults.forEach(tr => {
        systemPrompt += `[${tr.tool}] (${tr.particleType})\n${JSON.stringify(tr.result, null, 2)}\n`;
      });
      systemPrompt += `\n根據上述數據回答，數據有錯誤請告知用戶。`;
    }

    // 調用 Anthropic API
    const apiKey = env.ANTHROPIC_API_KEY;
    
    const aiResponse = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': apiKey,
        'anthropic-version': '2023-06-01'
      },
      body: JSON.stringify({
        model: 'claude-sonnet-4-20250514',
        max_tokens: 2048,
        system: systemPrompt,
        messages: [{ role: 'user', content: message }]
      })
    });

    if (!aiResponse.ok) {
      const err = await aiResponse.text();
      return Response.json({ error: 'AI API error', details: err }, { status: 500 });
    }

    const aiData = await aiResponse.json();
    const responseText = aiData.content?.[0]?.text || 'No response';

    const latency = Date.now() - startTime;

    // 構建回應
    const result = {
      response: responseText,
      mode: mode,
      mode_name: modeConfig.name,
      simhash64,
      deltaP0,
      origin_signature: ORIGIN_SIGNATURE,
      version: VERSION,
      timestamp: new Date().toISOString(),
      
      // 粒子系統資訊
      particle: {
        type: modeConfig.particleType.name,
        frequency: modeConfig.frequency,
        phi: PHI
      },
      
      // 記憶快照
      memory: {
        snapshotId: memorySnapshot.snapshotId,
        coherence: await edgeCache.checkCoherence()
      },
      
      // 連接器資訊
      connectors: {
        enabled: use_connectors,
        tools_called: toolResults.map(t => t.tool),
        results: toolResults,
        cache_metrics: edgeCache.getMetrics()
      },
      
      // 效能指標
      performance: {
        latency_ms: latency,
        cached: false
      }
    };

    // 存入回應快取 (L2)
    edgeCache.set(responseCacheKey, result, 'L2');

    // 存入 D1
    if (env.DB && chat_id) {
      try {
        await env.DB.prepare(`
          INSERT INTO messages (chat_id, role, content, mode, simhash64, deltap0, tool_calls, latency_ms)
          VALUES (?, 'user', ?, ?, ?, ?, ?, ?)
        `).bind(chat_id, message, mode, simhash64, deltaP0, JSON.stringify(toolResults), latency).run();
        
        await env.DB.prepare(`
          INSERT INTO messages (chat_id, role, content, mode, simhash64, deltap0, tool_calls, latency_ms)
          VALUES (?, 'assistant', ?, ?, ?, ?, ?, ?)
        `).bind(chat_id, responseText, mode, simhash64, deltaP0, JSON.stringify(toolResults), latency).run();
      } catch (dbErr) {
        console.error('DB error:', dbErr);
      }
    }

    return Response.json(result);

  } catch (error) {
    return Response.json({ 
      error: error.message,
      origin_signature: ORIGIN_SIGNATURE,
      latency_ms: Date.now() - startTime
    }, { status: 500 });
  }
}

// ============================================================
// 爽度導演 — FunDirector (金字塔底層堆疊 v1.1.0)
//
// 三層架構：
//   Layer 1 回饋物理層 (Feel Physics)   — HIT_STOP / SCREEN_SHAKE / KNOCKBACK …
//   Layer 2 反轉邏輯層 (Twist Logic)    — IDENTITY_FLIP / RULE_GLITCH_BURST …
//   Layer 3 人格導演層 (Persona Director) — HYPE / PRANK / SPOOKY
//
// 遵循 MrLiouWord 粒子哲學 LAW-0/1/2：
//   LAW-0 起源簽名律、LAW-1 記憶體守恆律（可追溯 eventLog）、
//   LAW-2 記憶體單調性律（相同 seed 可重現）
// ============================================================

// ── 粒子資料（內嵌，Cloudflare Workers 不支援 require） ──

const FUN_PARTICLES = {
  feelPhysics: [
    { id: 'HIT_STOP',        name: '命中停頓',   params: { duration_ms: 80,  intensity: 1.0 } },
    { id: 'SCREEN_SHAKE',    name: '震屏',       params: { amplitude: 10,    duration_ms: 300 } },
    { id: 'KNOCKBACK',       name: '擊退',       params: { force: 500,       angle: 30 } },
    { id: 'RAGDOLL',         name: '布娃娃',     params: { joint_loose: 0.7, duration_ms: 2000 } },
    { id: 'PROP_BREAK',      name: '道具破壞',   params: { fragments: 12,    fragment_damage: 5 } },
    { id: 'CHAIN_REACTION',  name: '連鎖反應',   params: { radius: 200,      chain_count: 3, delay_ms: 200 } }
  ],
  twistLogic: [
    { id: 'IDENTITY_FLIP',        name: '身分反轉', params: { probability: 0.15, duration_s: 10 } },
    { id: 'RULE_GLITCH_BURST',    name: '規則爆衝', params: { probability: 0.20, burst_count: 3 } },
    { id: 'COMEDY_CHAIN_REACTION',name: '搞笑連鎖', params: { trigger_count: 2,  laugh_factor: 1.5 } }
  ],
  personaDirector: [
    { id: 'HYPE',   name: '炒熱者',   bias: { comfort: 0.2, humor: 0.3, thrill: 0.4, power: 0.1 } },
    { id: 'PRANK',  name: '惡作劇者', bias: { comfort: 0.1, humor: 0.6, thrill: 0.2, power: 0.1 } },
    { id: 'SPOOKY', name: '驚恐者',   bias: { comfort: 0.0, humor: 0.2, thrill: 0.6, power: 0.2 } }
  ]
};

const FUN_MODULES = [
  { id: 'HIT_STOP',              category: 'feelPhysics', cooldown_s: 0.5, duration_s: 0.08, weight: 10 },
  { id: 'SCREEN_SHAKE',          category: 'feelPhysics', cooldown_s: 1.0, duration_s: 0.3,  weight: 8  },
  { id: 'KNOCKBACK',             category: 'feelPhysics', cooldown_s: 0.8, duration_s: 0.2,  weight: 9  },
  { id: 'RAGDOLL',               category: 'feelPhysics', cooldown_s: 3.0, duration_s: 2.0,  weight: 7  },
  { id: 'PROP_BREAK',            category: 'feelPhysics', cooldown_s: 2.0, duration_s: 0.5,  weight: 8  },
  { id: 'CHAIN_REACTION',        category: 'feelPhysics', cooldown_s: 5.0, duration_s: 3.0,  weight: 6  },
  { id: 'IDENTITY_FLIP',         category: 'twistLogic',  cooldown_s: 8.0, duration_s: 10.0, weight: 5  },
  { id: 'RULE_GLITCH_BURST',     category: 'twistLogic',  cooldown_s: 4.0, duration_s: 2.0,  weight: 6  },
  { id: 'COMEDY_CHAIN_REACTION', category: 'twistLogic',  cooldown_s: 6.0, duration_s: 4.0,  weight: 7  }
];

const FUN_PERSONA_PRESETS = {
  HYPE:   { funIntensity: 1.5, chaos: 1.0, vfxScale: 1.5, sfxPunch: 1.5, slowMo: true  },
  PRANK:  { funIntensity: 1.2, chaos: 1.8, vfxScale: 1.0, sfxPunch: 1.0, slowMo: false },
  SPOOKY: { funIntensity: 1.0, chaos: 0.7, vfxScale: 1.2, sfxPunch: 0.8, slowMo: true  }
};

const FUN_HIGH_IMPACT_IDS = [
  'HIT_STOP', 'SCREEN_SHAKE', 'KNOCKBACK',
  'RAGDOLL', 'CHAIN_REACTION', 'COMEDY_CHAIN_REACTION'
];

// ── LAW-2：Mulberry32 可重現 PRNG ──

function funSeedToNumber(seed) {
  if (typeof seed === 'number') return seed >>> 0;
  let h = 0;
  for (let i = 0; i < seed.length; i++) {
    h = (Math.imul(31, h) + seed.charCodeAt(i)) | 0;
  }
  return h >>> 0;
}

function funMulberry32(seed) {
  let s = seed >>> 0;
  return function () {
    s += 0x6D2B79F5;
    let t = Math.imul(s ^ (s >>> 15), s | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function funWeightedPick(rng, items) {
  const total = items.reduce((s, item) => s + (item.weight || 1), 0);
  let threshold = rng() * total;
  for (const item of items) {
    threshold -= item.weight || 1;
    if (threshold <= 0) return item;
  }
  return items[items.length - 1];
}

function funApplyPersonaBias(modules, personaId) {
  const persona = FUN_PARTICLES.personaDirector.find(p => p.id === personaId);
  if (!persona) return modules;
  return modules.map(mod => {
    let weight = mod.weight;
    if (persona.bias.humor > 0.4 &&
        ['RAGDOLL', 'COMEDY_CHAIN_REACTION', 'RULE_GLITCH_BURST', 'PROP_BREAK'].includes(mod.id)) {
      weight *= 1 + persona.bias.humor;
    }
    if (persona.bias.thrill > 0.3 &&
        ['SCREEN_SHAKE', 'KNOCKBACK', 'CHAIN_REACTION'].includes(mod.id)) {
      weight *= 1 + persona.bias.thrill;
    }
    if (persona.bias.power > 0.3 &&
        ['HIT_STOP', 'KNOCKBACK'].includes(mod.id)) {
      weight *= 1 + persona.bias.power;
    }
    return { ...mod, weight };
  });
}

function funBuildParams(moduleId, personaId, rng) {
  const preset = FUN_PERSONA_PRESETS[personaId] || FUN_PERSONA_PRESETS['HYPE'];
  const allParticles = [...FUN_PARTICLES.feelPhysics, ...FUN_PARTICLES.twistLogic];
  const particle = allParticles.find(p => p.id === moduleId);
  if (!particle) return {};

  const params = JSON.parse(JSON.stringify(particle.params));
  const scale = preset.funIntensity || 1.0;
  const chaos  = preset.chaos || 1.0;
  const noise  = 0.8 + rng() * 0.4;

  if (params.intensity    !== undefined) params.intensity    = +((params.intensity * scale * noise).toFixed(2));
  if (params.amplitude    !== undefined) params.amplitude    = Math.round(params.amplitude * scale * noise);
  if (params.force        !== undefined) params.force        = Math.round(params.force * scale * noise);
  if (params.joint_loose  !== undefined) params.joint_loose  = Math.min(1.0, +((params.joint_loose * chaos * noise).toFixed(2)));
  if (params.chain_count  !== undefined) params.chain_count  = Math.max(1, Math.round(params.chain_count * chaos));
  if (params.burst_count  !== undefined) params.burst_count  = Math.max(1, Math.round(params.burst_count * chaos));
  if (params.laugh_factor !== undefined) params.laugh_factor = +((params.laugh_factor * chaos * noise).toFixed(2));
  if (params.probability  !== undefined) params.probability  = Math.min(1.0, +((params.probability * chaos).toFixed(2)));

  params.slowMo   = preset.slowMo;
  params.vfxScale = +((preset.vfxScale * noise).toFixed(2));
  params.sfxPunch = +((preset.sfxPunch * noise).toFixed(2));
  return params;
}

/**
 * runFunDirector — 爽度導演核心
 * @param {object} opts  { playerState, roomState, personaState, seed }
 * @returns {object}     { twistRecipe, duration_s, cooldown_s, persona, eventLog, … }
 */
function runFunDirector({ playerState = {}, roomState = {}, personaState = 'HYPE', seed = Date.now() } = {}) {
  const rng = funMulberry32(funSeedToNumber(seed));
  const timestamp = new Date().toISOString();

  const validPersonas = FUN_PARTICLES.personaDirector.map(p => p.id);
  const persona = validPersonas.includes(personaState) ? personaState : 'HYPE';

  const biasedModules = funApplyPersonaBias(FUN_MODULES, persona);

  // 保底爆點：第一個模組必定是高衝擊粒子
  const highPool = biasedModules.filter(m => FUN_HIGH_IMPACT_IDS.includes(m.id));
  const firstPick = funWeightedPick(rng, highPool);

  const selected = [firstPick];
  const usedIds = new Set([firstPick.id]);

  if (rng() < 0.5) {
    const remaining = biasedModules.filter(m => !usedIds.has(m.id));
    if (remaining.length > 0) {
      const secondPick = funWeightedPick(rng, remaining);
      selected.push(secondPick);
      usedIds.add(secondPick.id);
    }
  }

  const twistRecipe = selected.map(mod => ({
    moduleId:   mod.id,
    category:   mod.category,
    duration_s: mod.duration_s,
    cooldown_s: mod.cooldown_s,
    params:     funBuildParams(mod.id, persona, rng)
  }));

  const duration_s = 10;
  const cooldown_s = Math.max(...selected.map(m => m.cooldown_s));

  // LAW-1：eventLog
  const personaMeta  = FUN_PARTICLES.personaDirector.find(p => p.id === persona);
  const personaName  = personaMeta ? personaMeta.name : persona;
  const allPList     = [...FUN_PARTICLES.feelPhysics, ...FUN_PARTICLES.twistLogic];
  const moduleNames  = selected
    .map(m => allPList.find(p => p.id === m.id))
    .filter(Boolean)
    .map(p => p.name)
    .join('、');

  const seedNum = funSeedToNumber(seed);
  const eventLog = {
    id:         `evt_${seedNum.toString(16).padStart(8, '0')}_${Date.now().toString(36)}`,
    timestamp,
    seed:       String(seed),
    persona,
    why:        `人格[${personaName}]在第 ${roomState.wave || '?'} 波（玩家 HP=${playerState.hp !== undefined ? playerState.hp : '?'}）偵測到爆點條件，啟動保底爆點：${moduleNames}`,
    what:       selected.map(m => m.id).join(' + '),
    duration_s,
    cooldown_s,
    intensity:  +(twistRecipe.reduce((max, r) => {
      const p = r.params;
      const v = p.intensity || (p.amplitude ? p.amplitude / 30 : 0) || (p.force ? p.force / 1200 : 0) || 1;
      return Math.max(max, v);
    }, 0).toFixed(2)),
    inputs:     { playerState, roomState, personaState: persona, seed: String(seed) },
    modules:    twistRecipe.map(r => ({ id: r.moduleId, category: r.category, duration_s: r.duration_s, cooldown_s: r.cooldown_s }))
  };

  return {
    twistRecipe,
    duration_s,
    cooldown_s,
    persona,
    eventLog,
    law:              'LAW-1: 記憶體守恆律 — 每次決策可追溯',
    origin_signature: 'MrLiouWord.FunDirector',
    version:          '1.1.0'
  };
}

// ============================================================
// runFunSequence — 生成完整場次爽度序列 (v1.1.0 新增)
// ============================================================

/**
 * 生成連續多個 10 秒視窗的爽度序列（LAW-0/1/2）
 * @param {object} opts  { windows, playerState, roomState, personaState, seed }
 * @returns {object}     { sessionId, windows, totalDuration_s, cooldown_s, … }
 */
function runFunSequence({ windows = 6, playerState = {}, roomState = {}, personaState = 'HYPE', seed = Date.now() } = {}) {
  const windowCount = Math.max(1, Math.min(100, Math.floor(windows)));
  const baseSeed = funSeedToNumber(seed);
  const GOLDEN_INT = 0x9E3779B9;

  const windowResults = [];
  for (let i = 0; i < windowCount; i++) {
    const windowSeed = (baseSeed + Math.imul(i + 1, GOLDEN_INT)) >>> 0;
    windowResults.push(runFunDirector({ playerState, roomState, personaState, seed: windowSeed }));
  }

  const totalDuration_s = windowResults.reduce((sum, r) => sum + r.duration_s, 0);
  const cooldown_s = Math.max(...windowResults.map(r => r.cooldown_s));
  const sessionId = `ses_${baseSeed.toString(16).padStart(8, '0')}_${Date.now().toString(36)}`;

  return {
    sessionId,
    windows: windowResults,
    totalDuration_s,
    cooldown_s,
    law:              'LAW-2: 記憶體單調性律 — 相同 seed 序列永遠可重現',
    origin_signature: 'MrLiouWord.FunDirector.Sequence',
    version:          '1.1.0'
  };
}

// ============================================
// Worker 主入口
// ============================================

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const path = url.pathname;

    // CORS
    if (request.method === 'OPTIONS') {
      return new Response(null, {
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
          'Access-Control-Allow-Headers': 'Content-Type, Authorization',
          'Access-Control-Max-Age': '86400'
        }
      });
    }

    const corsHeaders = {
      'Access-Control-Allow-Origin': '*',
      'X-Powered-By': `MrLiouWord Particle System v${VERSION}`,
      'X-Origin-Signature': ORIGIN_SIGNATURE,
      'X-PHI': PHI.toString()
    };

    let response;

    // 健康檢查
    if (path === '/health' || path === '/') {
      response = Response.json({
        status: 'healthy',
        version: VERSION,
        origin_signature: ORIGIN_SIGNATURE,
        phi: PHI,
        frequencies: FREQUENCIES,
        particle_types: Object.keys(PARTICLE_TYPES),
        cognitive_modes: Object.keys(COGNITIVE_MODES),
        deployed_workers: Object.keys(DEPLOYED_WORKERS),
        connectors: Object.keys(Connectors),
        cache_metrics: edgeCache.getMetrics(),
        memory_coherence: await edgeCache.checkCoherence(),
        laws: ['LAW-0: 起源簽名律', 'LAW-1: 記憶體守恆律', 'LAW-2: 記憶體單調性律'],
        endpoints: {
          chat: '/api/chat',
          fun_next: '/api/fun/next',
          fun_sequence: '/api/fun/sequence',
          connectors: '/api/connectors/list',
          cache: '/api/cache/metrics',
          coherence: '/api/memory/coherence',
          workers: '/api/workers/list',
          rpc: '/api/rpc/call'
        },
        timestamp: new Date().toISOString()
      });
    }
    // Chat API
    else if (path === '/api/chat' && request.method === 'POST') {
      response = await handleChat(request, env);
    }
    // 快取統計
    else if (path === '/api/cache/metrics') {
      response = Response.json({
        metrics: edgeCache.getMetrics(),
        origin_signature: ORIGIN_SIGNATURE
      });
    }
    // 記憶體一致性
    else if (path === '/api/memory/coherence') {
      response = Response.json({
        coherence: await edgeCache.checkCoherence(),
        structuralMemory: {
          snapshots: structuralMemory.functionTrees.size,
          flows: structuralMemory.reconstructionFlows.size
        },
        origin_signature: ORIGIN_SIGNATURE
      });
    }
    // 已部署 Workers 列表
    else if (path === '/api/workers/list') {
      response = Response.json({
        workers: DEPLOYED_WORKERS,
        count: Object.keys(DEPLOYED_WORKERS).length,
        origin_signature: ORIGIN_SIGNATURE
      });
    }
    // ParticleRPC 調用
    else if (path === '/api/rpc/call' && request.method === 'POST') {
      try {
        const { target, method, params } = await request.json();
        const result = await particleRPC.call(target, method, params);
        response = Response.json({
          result,
          callLog: particleRPC.getCallLog(5),
          origin_signature: ORIGIN_SIGNATURE
        });
      } catch (error) {
        response = Response.json({ error: error.message }, { status: 400 });
      }
    }
    // 連接器列表
    else if (path === '/api/connectors/list') {
      response = Response.json({
        connectors: Object.entries(Connectors).map(([name, c]) => ({
          name,
          description: c.description,
          source: c.source,
          params: c.params,
          cacheTTL: c.cacheTTL
        })),
        sources: Array.from(ConnectorRegistry.sources.entries()).map(([name, s]) => ({
          name,
          baseURL: s.baseURL,
          particleType: s.particleType?.name
        })),
        origin_signature: ORIGIN_SIGNATURE
      });
    }
    // 執行連接器
    else if (path === '/api/connector/execute' && request.method === 'POST') {
      try {
        const { connector, params } = await request.json();
        const result = await executeConnector(connector, params);
        response = Response.json({
          connector,
          params,
          result,
          cache_metrics: edgeCache.getMetrics(),
          timestamp: new Date().toISOString()
        });
      } catch (error) {
        response = Response.json({ error: error.message }, { status: 400 });
      }
    }
    // 系統常數
    else if (path === '/api/constants') {
      response = Response.json({
        PHI,
        FREQUENCIES,
        MEMORY_INSTRUCTIONS,
        PARTICLE_TYPES: Object.fromEntries(
          Object.entries(PARTICLE_TYPES).map(([k, v]) => [k, v.name])
        ),
        COGNITIVE_MODES: Object.fromEntries(
          Object.entries(COGNITIVE_MODES).map(([k, v]) => [k, { name: v.name, frequency: v.frequency }])
        ),
        origin_signature: ORIGIN_SIGNATURE,
        version: VERSION
      });
    }
    // 爽度導演 — 金字塔底層堆疊
    else if (path === '/api/fun/next' && request.method === 'POST') {
      try {
        const body = await request.json().catch(() => ({}));
        const { playerState = {}, roomState = {}, personaState = 'HYPE', seed } = body;
        const result = runFunDirector({
          playerState,
          roomState,
          personaState,
          seed: seed !== undefined ? seed : Date.now()
        });
        response = Response.json(result);
      } catch (error) {
        response = Response.json({
          error: error.message,
          origin_signature: ORIGIN_SIGNATURE
        }, { status: 400 });
      }
    }
    // 爽度導演序列 — 多視窗場次
    else if (path === '/api/fun/sequence' && request.method === 'POST') {
      try {
        const body = await request.json().catch(() => ({}));
        const { windows = 6, playerState = {}, roomState = {}, personaState = 'HYPE', seed } = body;
        const result = runFunSequence({
          windows,
          playerState,
          roomState,
          personaState,
          seed: seed !== undefined ? seed : Date.now()
        });
        response = Response.json(result);
      } catch (error) {
        response = Response.json({
          error: error.message,
          origin_signature: ORIGIN_SIGNATURE
        }, { status: 400 });
      }
    }
    // 404
    else {
      response = Response.json({ 
        error: 'Not Found',
        available: [
          '/api/chat',
          '/api/fun/next',
          '/api/fun/sequence',
          '/api/connectors/list', 
          '/api/cache/metrics',
          '/api/memory/coherence',
          '/api/workers/list',
          '/api/rpc/call',
          '/api/constants'
        ],
        origin_signature: ORIGIN_SIGNATURE
      }, { status: 404 });
    }

    // 添加 CORS headers
    const newHeaders = new Headers(response.headers);
    Object.entries(corsHeaders).forEach(([k, v]) => newHeaders.set(k, v));
    
    return new Response(response.body, {
      status: response.status,
      headers: newHeaders
    });
  }
};
