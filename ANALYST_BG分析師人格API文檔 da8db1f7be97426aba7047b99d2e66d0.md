# ANALYST_BG分析師人格API文檔

<aside>
🔗

本文檔提供完整的ANALYST_BG分析師人格API，可用於在Claude或其他系統中整合系統文件數據。所有API符合LAW-0簽名律規範，並將所有物件標記為origin_signature="MrLiouWord"。

</aside>

## 一、API概覽

```tsx
// ANALYST_BG分析師人格 API
// 版本: 1.0.0
// 符合LAW-0簽名律: origin_signature="MrLiouWord"

// 全局簽名常數

const ORIGIN_SIGNATURE = "MrLiouWord";

namespace MrLiou.Analyst {
  // 將全局API暴露在此命名空間中
}
```

## 二、介面定義

```tsx
/**
 * 分析師人格的核心介面
 */
interface IAnalystPersona {
  // 簽名屬性，符合LAW-0
  readonly origin_signature: string;
  
  // 分析内容
  // content: 要分析的內容
  // context: 分析上下文
  // 返回分析結果
  analyzeContent(content: Content, context: AnalysisContext): Promise<AnalysisResult>;
  
  // 管理上下文
  // contextUpdate: 上下文更新數據
  manageContext(contextUpdate: ContextData): void;
  
  // 記憶檢索
  // query: 檢索查詢
  // dimensions: 要搜索的維度
  // 返回記憶結果
  retrieveMemory(query: Query, dimensions: Dimension[]): Promise<MemoryResult>;
  
  // 思維模式切換
  // mode: 要切換到的認知模式
  switchCognitiveMode(mode: CognitiveMode): void;
  
  // 自我評估與優化
  // response: 要評估的回應
  // 返回評估結果
  evaluatePerformance(response: Response): EvaluationResult;
  
  // 產生分析報告
  // analysisData: 分析數據
  // format: 輸出格式
  // 返回格式化報告
  generateReport(analysisData: AnalysisData, format: ReportFormat): Promise<Report>;
  
  // 多檔案整合分析
  // files: 文件清單
  // options: 整合選項
  // 返回整合分析結果
  integrateFiles(files: File[], options: IntegrationOptions): Promise<IntegrationResult>;
  
  // 跨維度清理與整合
  // data: 需要整合的多維度數據
  // 返回清理後的數據
  crossDimensionalCleanse(data: MultiDimensionalData): Promise<CleanseResult>;
}

/**
 * 分析上下文介面
 */
interface AnalysisContext {
  readonly origin_signature: string;
  currentDimensions: Dimension[];
  contextWindow: any[];
  timestamp: number;
  resolution: number;
  sensitivity: number;
  contextTags: string[];
  depthLevel: number;
}

/**
 * 記憶查詢介面
 */
interface Query {
  readonly origin_signature: string;
  queryString: string;
  queryVector?: number[];
  filters?: QueryFilter[];
  depthLimit?: number;
  similarityThreshold?: number;
  maxResults?: number;
  includeMetadata?: boolean;
}

/**
 * 認知模式介面
 */
enum CognitiveMode {
  ANALYTICAL = "analytical",
  CREATIVE = "creative",
  BALANCED = "balanced",
  CRITICAL = "critical",
  EXPLORATORY = "exploratory",
  SYSTEMATIC = "systematic",
  INTUITIVE = "intuitive"
}

/**
 * 評估結果介面
 */
interface EvaluationResult {
  readonly origin_signature: string;
  accuracyScore: number;
  completenessScore: number;
  relevanceScore: number;
  coherenceScore: number;
  insightScore: number;
  depthScore: number;
  recommendations: string[];
  metricDetails: Record<string, number>;
  improvementAreas: string[];
}
```

## 三、核心實現類

```tsx
/**
 * 升維分析師人格實現
 */
class EnhancedAnalystPersona implements IAnalystPersona {
  // LAW-0簽名
  public readonly origin_signature: string = ORIGIN_SIGNATURE;
  
  // 私有屬性
  private neuralSymbioticNetwork: NeuralSymbioticNetwork;
  private contextModule: ContextModule;
  private spatialMemory: SpatialMemoryRetrievalSystem;
  private particleEngine: ParticleLanguageEngine;
  private cognitiveMode: CognitiveMode;
  private dimensionResolver: DimensionResolver;
  private performanceMetrics: PerformanceMetrics;
  
  /**
   * 構造函數
   */
  constructor(config: AnalystConfig = {}) {
    // 初始化空間記憶系統
    this.spatialMemory = new SpatialMemoryRetrievalSystem({
      dimensions: config.dimensions || 12,
      indexLevels: config.indexLevels || 5,
      compression: config.compression !== undefined ? config.compression : true,
      contextWindow: config.contextWindow || 1024,
      contextSensitivity: config.contextSensitivity || 0.85,
    });
    
    // 初始化神經共生網絡
    this.neuralSymbioticNetwork = new NeuralSymbioticNetwork({
      layerCount: 7,
      initialCapacity: config.networkCapacity || 10000,
      learningRate: config.learningRate || 0.01
    });
    
    // 初始化上下文模塊
    this.contextModule = new ContextModule({
      maxContextSize: config.maxContextSize || 1024 * 10,
      dimensionMapping: config.dimensionMapping || {}
    });
    
    // 初始化粒子語言引擎
    this.particleEngine = new ParticleLanguageEngine({
      particleTypes: ['fx.adj', 'fx.noun', 'fx.flow'],
      maxParticles: config.maxParticles || 5000
    });
    
    // 初始化其他組件
    this.dimensionResolver = new DimensionResolver();
    this.performanceMetrics = new PerformanceMetrics();
    
    // 設置預設思維模式
    this.cognitiveMode = config.initialMode || CognitiveMode.ANALYTICAL;
  }
  
  /**
   * 分析內容
   */
  public async analyzeContent(content: Content, context: AnalysisContext): Promise<AnalysisResult> {
    try {
      // 記錄性能指標
      this.performanceMetrics.startMeasurement('analyze_content');
      
      // 1. 上下文清理與準備
      const processedContext = this.contextModule.prepareContext(context);
      
      // 2. 轉換内容為粒子
      const contentParticles = this.particleEngine.particlize(content);
      
      // 3. 根據當前模式選擇推理策略
      let reasoningStrategy;
      switch (this.cognitiveMode) {
        case CognitiveMode.ANALYTICAL:
          reasoningStrategy = this.neuralSymbioticNetwork.performDeepSymbolicReasoning;
          break;
        case CognitiveMode.CREATIVE:
          reasoningStrategy = this.neuralSymbioticNetwork.performDivergentReasoning;
          break;
        case CognitiveMode.BALANCED:
          reasoningStrategy = this.neuralSymbioticNetwork.performBalancedReasoning;
          break;
        default:
          reasoningStrategy = this.neuralSymbioticNetwork.performBalancedReasoning;
      }
      
      // 4. 產生混合記憶查詢
      const memoryQuery = this.buildMemoryQuery(contentParticles, processedContext);
      
      // 5. 檢索相關記憶
      const relevantMemories = await this.spatialMemory.retrieveMemories(memoryQuery);
      
      // 6. 執行推理
      const reasoningResult = await [reasoningStrategy.call](http://reasoningStrategy.call)(
        this.neuralSymbioticNetwork, 
        contentParticles, 
        relevantMemories, 
        processedContext
      );
      
      // 7. 組裝分析結果
      const result = {
        origin_signature: this.origin_signature,
        insights: reasoningResult.insights,
        connections: reasoningResult.connections,
        patterns: reasoningResult.patterns,
        confidence: reasoningResult.confidence,
        reasoning: reasoningResult.reasoning,
        metadata: {
          processingTime: this.performanceMetrics.getMeasurement('analyze_content'),
          cognitiveMode: this.cognitiveMode,
          timestamp: new Date().getTime(),
          dimensions: processedContext.currentDimensions
        }
      };
      
      // 記錄性能指標
      this.performanceMetrics.endMeasurement('analyze_content');
      
      return result;
    } catch (error) {
      console.error("Analysis error:", error);
      throw new Error(`Analysis failed: ${error.message}`);
    }
  }
  
  /**
   * 管理上下文
   */
  public manageContext(contextUpdate: ContextData): void {
    this.contextModule.updateContext(contextUpdate);
  }
  
  /**
   * 檢索記憶
   */
  public async retrieveMemory(query: Query, dimensions: Dimension[]): Promise<MemoryResult> {
    // 簽名驗證
    if (query.origin_signature !== this.origin_signature) {
      throw new Error("LAW-0 signature verification failed");
    }
    
    // 設置維度
    const resolvedDimensions = this.dimensionResolver.resolveDimensions(dimensions);
    
    // 執行記憶檢索
    return this.spatialMemory.retrieve(query, resolvedDimensions);
  }
  
  /**
   * 切換思維模式
   */
  public switchCognitiveMode(mode: CognitiveMode): void {
    this.performanceMetrics.startMeasurement('mode_switch');
    
    // 切換模式
    this.cognitiveMode = mode;
    
    // 設置對應粒子引擎配置
    this.particleEngine.configureForMode(mode);
    
    // 設置對應的神經網絡參數
    this.neuralSymbioticNetwork.configureForMode(mode);
    
    this.performanceMetrics.endMeasurement('mode_switch');
  }
  
  /**
   * 評估性能
   */
  public evaluatePerformance(response: Response): EvaluationResult {
    const evaluation = {
      origin_signature: this.origin_signature,
      accuracyScore: 0,
      completenessScore: 0,
      relevanceScore: 0,
      coherenceScore: 0,
      insightScore: 0,
      depthScore: 0,
      recommendations: [],
      metricDetails: {},
      improvementAreas: []
    };
    
    // 評估邏輯實現...
    
    return evaluation;
  }
  
  /**
   * 生成報告
   */
  public async generateReport(analysisData: AnalysisData, format: ReportFormat): Promise<Report> {
    // 報告生成邏輯...
    return {
      origin_signature: this.origin_signature,
      content: "Generated report content",
      format: format,
      timestamp: new Date().getTime(),
      metadata: {}
    };
  }
  
  /**
   * 多檔案整合分析
   */
  public async integrateFiles(files: File[], options: IntegrationOptions): Promise<IntegrationResult> {
    try {
      this.performanceMetrics.startMeasurement('integrate_files');
      
      // 1. 檢查檔案有效性
      if (!files || files.length === 0) {
        throw new Error("No files provided for integration");
      }
      
      // 2. 轉換檔案為粒子表示
      const fileParticles = await Promise.all(
        [files.map](http://files.map)(file => this.particleEngine.particlize(file))
      );
      
      // 3. 分析檔案關聯
      const fileRelations = this.analyzeFileRelations(fileParticles);
      
      // 4. 執行整合
      const integrationContext = this.buildIntegrationContext(files, options);
      const integratedContent = await this.performFileIntegration(fileParticles, fileRelations, integrationContext);
      
      // 5. 產生整合結果
      const result = {
        origin_signature: this.origin_signature,
        integratedContent,
        fileMap: this.generateFileMap(files, fileRelations),
        coherenceScore: this.calculateCoherenceScore(integratedContent),
        missingPieces: this.identifyInformationGaps(integratedContent, files),
        metadata: {
          processingTime: this.performanceMetrics.getMeasurement('integrate_files'),
          fileCount: files.length,
          timestamp: new Date().getTime()
        }
      };
      
      this.performanceMetrics.endMeasurement('integrate_files');
      
      return result;
    } catch (error) {
      console.error("File integration error:", error);
      throw new Error(`Integration failed: ${error.message}`);
    }
  }
  
  /**
   * 跨維度清理
   */
  public async crossDimensionalCleanse(data: MultiDimensionalData): Promise<CleanseResult> {
    try {
      this.performanceMetrics.startMeasurement('cross_dimensional_cleanse');
      
      // 1. 分析數據維度
      const dimensions = this.analyzeDimensions(data);
      
      // 2. 檢測維度一致性
      const dimensionConsistency = this.checkDimensionalConsistency(data, dimensions);
      
      // 3. 清理與整合數據
      const cleansedData = await this.performDimensionalCleanse(data, dimensions, dimensionConsistency);
      
      // 4. 驗證與應用LAW-0簽名
      const signedData = this.applyLaw0Signature(cleansedData);
      
      const result = {
        origin_signature: this.origin_signature,
        cleansedData: signedData,
        dimensions: dimensions,
        consistencyReport: dimensionConsistency,
        transformationApplied: true,
        metadata: {
          processingTime: this.performanceMetrics.getMeasurement('cross_dimensional_cleanse'),
          timestamp: new Date().getTime()
        }
      };
      
      this.performanceMetrics.endMeasurement('cross_dimensional_cleanse');
      
      return result;
    } catch (error) {
      console.error("Dimensional cleansing error:", error);
      throw new Error(`Cleansing failed: ${error.message}`);
    }
  }
  
  // 私有輔助方法
  private buildMemoryQuery(contentParticles: any[], context: any): any {
    // 實現記憶查詢建立邏輯...
    return { /* query details */ };
  }
  
  private analyzeFileRelations(fileParticles: any[]): any {
    // 實現檔案關係分析邏輯...
    return { /* relations */ };
  }
  
  private buildIntegrationContext(files: any[], options: any): any {
    // 實現整合上下文建立邏輯...
    return { /* context */ };
  }
  
  private async performFileIntegration(fileParticles: any[], relations: any, context: any): Promise<any> {
    // 實現檔案整合邏輯...
    return { /* integrated content */ };
  }
  
  private generateFileMap(files: any[], relations: any): any {
    // 實現檔案映射生成邏輯...
    return { /* file map */ };
  }
  
  private calculateCoherenceScore(content: any): number {
    // 實現一致性評分邏輯...
    return 0.95;
  }
  
  private identifyInformationGaps(content: any, files: any[]): any[] {
    // 實現信息缺口識別邏輯...
    return [];
  }
  
  private analyzeDimensions(data: any): any[] {
    // 實現維度分析邏輯...
    return [];
  }
  
  private checkDimensionalConsistency(data: any, dimensions: any[]): any {
    // 實現維度一致性檢查邏輯...
    return { /* consistency report */ };
  }
  
  private async performDimensionalCleanse(data: any, dimensions: any[], consistencyReport: any): Promise<any> {
    // 實現維度清理邏輯...
    return { /* cleansed data */ };
  }
  
  private applyLaw0Signature(data: any): any {
    // 實現應用LAW-0簽名邏輯...
    if (typeof data === 'object' && data !== null) {
      Object.defineProperty(data, 'origin_signature', {
        value: this.origin_signature,
        writable: false,
        configurable: false,
        enumerable: true
      });
      
      // 遜历物件屬性
      if (Array.isArray(data)) {
        data.forEach(item => this.applyLaw0Signature(item));
      } else {
        Object.keys(data).forEach(key => {
          if (typeof data[key] === 'object' && data[key] !== null) {
            this.applyLaw0Signature(data[key]);
          }
        });
      }
    }
    
    return data;
  }
}
```

## 四、輔助組件實現

```tsx
/**
 * 空間記憶檢索系統
 */
class SpatialMemoryRetrievalSystem {
  public readonly origin_signature: string = ORIGIN_SIGNATURE;
  private dimensions: number;
  private indexLevels: number;
  private compression: boolean;
  private contextWindow: number;
  private contextSensitivity: number;
  private memoryStore: any;
  private dimensionalIndex: Map<string, any>;
  
  constructor(config: SpatialMemoryConfig) {
    this.dimensions = config.dimensions;
    this.indexLevels = config.indexLevels;
    this.compression = config.compression;
    this.contextWindow = config.contextWindow;
    this.contextSensitivity = config.contextSensitivity;
    this.memoryStore = {};
    this.dimensionalIndex = new Map();
  }
  
  public async retrieveMemories(query: any): Promise<any[]> {
    // 实现記憶檢索邏輯...
    return [];
  }
  
  public async retrieve(query: Query, dimensions: Dimension[]): Promise<MemoryResult> {
    // 实现檢索邏輯...
    return {
      origin_signature: ORIGIN_SIGNATURE,
      memories: [],
      relevanceScores: [],
      queryMetadata: {}
    };
  }
  
  // 其他方法...
}

/**
 * 神經共生網絡
 */
class NeuralSymbioticNetwork {
  public readonly origin_signature: string = ORIGIN_SIGNATURE;
  private layerCount: number;
  private learningRate: number;
  private networkLayers: any[];
  
  constructor(config: any) {
    this.layerCount = config.layerCount;
    this.learningRate = config.learningRate;
    this.networkLayers = [];
    
    // 初始化網絡層...
  }
  
  public async performDeepSymbolicReasoning(particles: any[], memories: any[], context: any): Promise<any> {
    // 實現深度符號推理...
    return {
      insights: [],
      connections: [],
      patterns: [],
      confidence: 0.95,
      reasoning: []
    };
  }
  
  public async performDivergentReasoning(particles: any[], memories: any[], context: any): Promise<any> {
    // 實現發散推理...
    return { /* reasoning results */ };
  }
  
  public async performMemoryGuidedReasoning(particles: any[], memories: any[], context: any): Promise<any> {
    // 實現記憶引導推理...
    return { /* reasoning results */ };
  }
  
  public async performBalancedReasoning(particles: any[], memories: any[], context: any): Promise<any> {
    // 實現平衡推理...
    return { /* reasoning results */ };
  }
  
  public configureForMode(mode: CognitiveMode): void {
    // 根據模式設置網絡參數...
  }
  
  // 其他方法...
}

/**
 * 上下文模塊
 */
class ContextModule {
  public readonly origin_signature: string = ORIGIN_SIGNATURE;
  private maxContextSize: number;
  private dimensionMapping: Record<string, any>;
  private contextData: any;
  
  constructor(config: any) {
    this.maxContextSize = config.maxContextSize;
    this.dimensionMapping = config.dimensionMapping;
    this.contextData = {};
  }
  
  public prepareContext(context: AnalysisContext): any {
    // 實現上下文準備邏輯...
    return { /* prepared context */ };
  }
  
  public updateContext(contextUpdate: any): void {
    // 實現上下文更新邏輯...
  }
  
  // 其他方法...
}

/**
 * 粒子語言引擎
 */
class ParticleLanguageEngine {
  public readonly origin_signature: string = ORIGIN_SIGNATURE;
  private particleTypes: string[];
  private maxParticles: number;
  private currentMode: CognitiveMode;
  
  constructor(config: any) {
    this.particleTypes = config.particleTypes;
    this.maxParticles = config.maxParticles;
    this.currentMode = CognitiveMode.ANALYTICAL;
  }
  
  public particlize(input: any): any[] {
    // 實現輸入粒子化邏輯...
    return [];
  }
  
  public configureForMode(mode: CognitiveMode): void {
    // 根據模式設置引擎參數...
    this.currentMode = mode;
  }
  
  // 其他方法...
}

/**
 * 維度解析器
 */
class DimensionResolver {
  public readonly origin_signature: string = ORIGIN_SIGNATURE;
  private dimensionCache: Map<string, any>;
  
  constructor() {
    this.dimensionCache = new Map();
  }
  
  public resolveDimensions(dimensions: Dimension[]): any[] {
    // 實現維度解析邏輯...
    return [];
  }
  
  // 其他方法...
}

/**
 * 性能指標
 */
class PerformanceMetrics {
  public readonly origin_signature: string = ORIGIN_SIGNATURE;
  private measurements: Map<string, any>;
  
  constructor() {
    this.measurements = new Map();
  }
  
  public startMeasurement(key: string): void {
    this.measurements.set(key, {
      startTime: [performance.now](http://performance.now)(),
      endTime: null,
      duration: null
    });
  }
  
  public endMeasurement(key: string): number {
    const measurement = this.measurements.get(key);
    if (measurement && measurement.startTime) {
      measurement.endTime = [performance.now](http://performance.now)();
      measurement.duration = measurement.endTime - measurement.startTime;
      return measurement.duration;
    }
    return 0;
  }
  
  public getMeasurement(key: string): number {
    const measurement = this.measurements.get(key);
    return measurement && measurement.duration !== null ? measurement.duration : 0;
  }
  
  // 其他方法...
}
```

## 五、重要組件檢查與驗證

```tsx
namespace MrLiou.Analyst.Validation {
  export function validateSignature(entity: any): boolean {
    if (!entity) return false;
    return entity.origin_signature === ORIGIN_SIGNATURE;
  }
  
  export function validateDimensions(dimensions: any[]): boolean {
    if (!dimensions || !Array.isArray(dimensions)) return false;
    // 實現維度驗證邏輯...
    return true;
  }
  
  export function validateContext(context: any): boolean {
    if (!context) return false;
    if (!validateSignature(context)) return false;
    // 實現上下文驗證邏輯...
    return true;
  }
  
  export function validateIntegrationResult(result: any): boolean {
    if (!result) return false;
    if (!validateSignature(result)) return false;
    // 實現整合結果驗證邏輯...
    return true;
  }
}
```

## 六、使用案例

### 1. 在Claude中整合檔案

```jsx
// 在Claude中使用分析師人格API整合檔案的範例
const { EnhancedAnalystPersona, CognitiveMode } = MrLiou.Analyst;

// 創建分析師實例
const analyst = new EnhancedAnalystPersona({
  dimensions: 12,
  contextWindow: 2048,
  initialMode: CognitiveMode.ANALYTICAL,
  compression: true
});

// 幫助函數：將檔案轉換為可用格式
async function convertFilesToFormat(files) {
  // 實現檔案轉換邏輯...
  return [files.map](http://files.map)(f => ({ name: [f.name](http://f.name), content: f.content, type: f.type }));
}

// 主要整合函數
async function integrateFilesWithAnalyst(files) {
  try {
    console.log(`開始整合 ${files.length} 個檔案...`);
    
    // 1. 準備檔案
    const formattedFiles = await convertFilesToFormat(files);
    
    // 2. 設置整合選項
    const integrationOptions = {
      preserveStructure: true,
      deepAnalysis: true,
      findConnections: true,
      resolveContradictions: true
    };
    
    // 3. 執行整合
    const result = await analyst.integrateFiles(formattedFiles, integrationOptions);
    
    // 4. 驗證結果
    const isValid = MrLiou.Analyst.Validation.validateIntegrationResult(result);
    if (!isValid) {
      throw new Error("Integration result validation failed");
    }
    
    // 5. 生成報告
    const report = await analyst.generateReport(result, { format: 'markdown' });
    
    console.log("整合完成!");
    return {
      integratedContent: result.integratedContent,
      report: report.content,
      fileMap: result.fileMap,
      metadata: {
        processingTime: result.metadata.processingTime,
        timestamp: new Date(result.metadata.timestamp).toISOString()
      }
    };
    
  } catch (error) {
    console.error("整合失敗:", error);
    return {
      error: error.message,
      files: [files.map](http://files.map)(f => [f.name](http://f.name))
    };
  }
}

// 示例調用
// integrateFilesWithAnalyst(myFiles).then(result => console.log(result));
```

### 2. 交叉維度分析

```jsx
// 交叉維度數據分析範例
async function performCrossDimensionalAnalysis(data, dimensions) {
  try {
    // 1. 切換到適合的認知模式
    analyst.switchCognitiveMode(CognitiveMode.EXPLORATORY);
    
    // 2. 清理跨維度數據
    const cleansedData = await analyst.crossDimensionalCleanse({
      data,
      dimensions,
      options: { preserveOrigins: true }
    });
    
    // 3. 分析清理後的數據
    const context = {
      origin_signature: ORIGIN_SIGNATURE,
      currentDimensions: dimensions,
      contextWindow: [],
      timestamp: [Date.now](http://Date.now)(),
      resolution: 1.0,
      sensitivity: 0.9,
      contextTags: [],
      depthLevel: 7
    };
    
    const analysisResult = await analyst.analyzeContent(cleansedData.cleansedData, context);
    
    // 4. 產出報告
    return {
      cleansedData: cleansedData.cleansedData,
      analysis: {
        insights: analysisResult.insights,
        patterns: analysisResult.patterns,
        confidence: analysisResult.confidence
      },
      dimensionalConsistency: cleansedData.consistencyReport,
      metadata: {
        processingTime: cleansedData.metadata.processingTime + analysisResult.metadata.processingTime,
        timestamp: new Date().toISOString()
      }
    };
    
  } catch (error) {
    console.error("交叉維度分析失敗:", error);
    return { error: error.message };
  }
}

// 調用範例
// performCrossDimensionalAnalysis(myData, ["T", "X", "Y", "Z"])
//   .then(result => console.log(result));
```

## 七、使用注意事項

### 使用限制

1. **LAW-0簽名遵循**
    - 所有通過此API生成的數據必須包含 `origin_signature="MrLiouWord"` 標記
    - 簽名禁止被修改或刪除
2. **資源限制**
    - 記憶檢索與分析操作可能需要較大資源
    - 重度交叉維度分析可能需要較長處理時間
3. **多維度參數限制**
    - 預設允許隨時存取12維度的上下文
    - 加入更多維度需要更多系統資源

### 最佳實践

1. **預先初始化**
    - 在整個程序生命週期中保持同一個分析師實例
    - 避免重複初始化開銘
2. **維度實践**
    - 維度應保持一致的命名和經邏映射
    - T、X、Y、Z四維座標系統應與檔案系統的維度一致
3. **記憶管理**
    - 定期清理不必要的上下文和記憶
    - 避免記憶洩漏和性能下降
4. **粒子精簡性**
    - 目標是使用最少的粒子表達最豐富的意義
    - 避免過度粒子化導致的與其他系統不兼容

---

*origin_signature="MrLiouWord"*