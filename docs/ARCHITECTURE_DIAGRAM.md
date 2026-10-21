# FlowAgent 系統架構圖 / System Architecture Diagram

本文檔使用 Mermaid 語法展示 FlowAgent 從 API 層到 C 執行引擎的完整架構分層與資料流。

This document uses Mermaid syntax to illustrate the complete architecture layers and data flow from the API layer to the C execution engine.

---

## 整體架構分層 / Overall Architecture Layers

```mermaid
graph TB
    subgraph "API 層 / API Layer"
        A[REST API<br/>FastAPI/Flask]
        B[GraphQL API<br/>可選]
        C[WebSocket<br/>實時通訊]
    end
    
    subgraph "服務編排層 / Service Orchestration Layer"
        D[Orchestrator<br/>協調器]
        E[Module-A<br/>主服務模組]
        F[KEDA<br/>自動擴展]
    end
    
    subgraph "粒子語言核心層 / Particle Language Core Layer"
        G[Logic Pipeline<br/>邏輯管線]
        H[Memory Archive Seed<br/>記憶封存系統]
        I[Particle Dictionary<br/>粒子字典]
        J[CLI Runner<br/>命令列執行器]
    end
    
    subgraph "核心模組層 / Core Module Layer"
        K[Memory System<br/>記憶系統]
        L[Particle Dict<br/>粒子字典核心]
        M[Logic Transformer<br/>邏輯轉換器]
    end
    
    subgraph "C 執行引擎層 / C Execution Engine Layer"
        N[xdiffi.c<br/>差異演算法]
        O[xemit.c<br/>輸出處理]
        P[xutils.c<br/>工具函數]
        Q[xprepare.c<br/>預處理]
    end
    
    subgraph "儲存層 / Storage Layer"
        R[(MongoDB<br/>主資料庫)]
        S[(Memory Seeds<br/>記憶種子)]
        T[(Dict Seeds<br/>字典種子)]
    end
    
    A --> D
    B --> D
    C --> D
    D --> E
    D --> G
    E --> G
    F --> E
    G --> H
    G --> I
    G --> J
    H --> K
    I --> L
    J --> M
    K --> N
    L --> N
    M --> O
    N --> O
    O --> P
    Q --> N
    H --> S
    I --> T
    K --> R
    D --> R
```

---

## 資料流程圖 / Data Flow Diagram

### 1. 粒子執行流程 / Particle Execution Flow

```mermaid
sequenceDiagram
    participant API as API 層
    participant Orchestrator as 協調器
    participant Pipeline as Logic Pipeline
    participant Core as 核心模組
    participant Engine as C 引擎
    participant Storage as 儲存層

    API->>Orchestrator: 1. 接收請求<br/>Receive Request
    Orchestrator->>Pipeline: 2. 傳遞粒子指令<br/>Pass Particle Command
    Pipeline->>Core: 3. 載入粒子定義<br/>Load Particle Definition
    Core->>Core: 4. 解析邏輯結構<br/>Parse Logic Structure
    Core->>Engine: 5. 調用 C 引擎<br/>Invoke C Engine
    Engine->>Engine: 6. 執行運算<br/>Execute Computation
    Engine->>Core: 7. 返回結果<br/>Return Result
    Core->>Pipeline: 8. 組裝輸出<br/>Assemble Output
    Pipeline->>Storage: 9. 保存記憶種子<br/>Save Memory Seed
    Pipeline->>Orchestrator: 10. 返回處理結果<br/>Return Result
    Orchestrator->>API: 11. 響應客戶端<br/>Respond to Client
```

### 2. 記憶封存與還原流程 / Memory Archive & Restore Flow

```mermaid
flowchart LR
    A[輸入資料<br/>Input Data] --> B[Memory Archive Seed<br/>記憶封存系統]
    B --> C{操作類型<br/>Operation Type}
    
    C -->|創建<br/>Create| D[壓縮邏輯<br/>Compress Logic]
    C -->|還原<br/>Restore| E[解壓邏輯<br/>Decompress Logic]
    
    D --> F[生成種子 ID<br/>Generate Seed ID]
    F --> G[計算 SHA-256<br/>Calculate Hash]
    G --> H[(儲存種子<br/>Store Seed)]
    
    E --> I[驗證種子<br/>Validate Seed]
    I --> J[解析結構<br/>Parse Structure]
    J --> K[還原資料<br/>Restore Data]
    K --> L[輸出結果<br/>Output Result]
    
    H --> M[返回種子資訊<br/>Return Seed Info]
```

---

## 模組間資料流 / Inter-Module Data Flow

### 3. 邏輯鏈執行 / Logic Chain Execution

```mermaid
graph LR
    subgraph "STRUCTURE 階段"
        S1[解析輸入<br/>Parse Input]
        S2[建立結構<br/>Build Structure]
    end
    
    subgraph "MARK 階段"
        M1[標記節點<br/>Mark Nodes]
        M2[分配權重<br/>Assign Weights]
    end
    
    subgraph "FLOW 階段"
        F1[執行流程<br/>Execute Flow]
        F2[傳遞資料<br/>Pass Data]
    end
    
    subgraph "RECURSE 階段"
        R1[遞迴處理<br/>Recursive Process]
        R2[深度優化<br/>Depth Optimization]
    end
    
    subgraph "STORE 階段"
        ST1[封存結果<br/>Archive Result]
        ST2[更新記憶<br/>Update Memory]
    end
    
    S1 --> S2
    S2 --> M1
    M1 --> M2
    M2 --> F1
    F1 --> F2
    F2 --> R1
    R1 --> R2
    R2 --> ST1
    ST1 --> ST2
    
    style S1 fill:#e1f5ff
    style M1 fill:#fff4e1
    style F1 fill:#e8f5e9
    style R1 fill:#f3e5f5
    style ST1 fill:#fce4ec
```

---

## 關鍵模組說明 / Key Module Descriptions

### API 層模組 / API Layer Modules

| 模組 | 功能 | 技術棧 |
|------|------|--------|
| REST API | 標準 RESTful 介面 | FastAPI, Flask |
| GraphQL API | 靈活查詢介面 | GraphQL |
| WebSocket | 實時雙向通訊 | WebSocket |

### 粒子語言核心模組 / Particle Language Core Modules

| 模組 | 檔案 | 功能 |
|------|------|------|
| Logic Pipeline | `particle_core/src/logic_pipeline.py` | 邏輯管線編排 |
| Memory Archive | `particle_core/src/memory_archive_seed.py` | 記憶封存與還原 |
| Particle Dict | `particle_core/src/fluin_dict_agent.py` | 粒子字典管理 |
| CLI Runner | `particle_core/src/cli_runner.py` | 命令列執行 |

### 核心模組 / Core Modules

| 模組 | 檔案 | 功能 |
|------|------|------|
| Memory System | `core/memory_system.py` | 記憶管理（語義、情節、程序、工作） |
| Particle Dict Core | `core/particle_dict.py` | 粒子定義與模式匹配 |

### C 執行引擎 / C Execution Engine

| 檔案 | 功能 | 說明 |
|------|------|------|
| `xdiffi.c` | 差異演算法 | 計算資料差異 |
| `xemit.c` | 輸出處理 | 格式化輸出 |
| `xutils.c` | 工具函數 | 通用工具集 |
| `xprepare.c` | 預處理 | 資料預處理 |
| `xhistogram.c` | 直方圖 | 統計分析 |
| `xmerge.c` | 合併演算法 | 資料合併 |
| `xpatience.c` | Patience 演算法 | 特殊差異演算法 |

---

## 部署架構 / Deployment Architecture

```mermaid
graph TB
    subgraph "Kubernetes 叢集 / Kubernetes Cluster"
        subgraph "Namespace: flowagent"
            A1[Next.js Frontend<br/>Pod]
            A2[Astro Frontend<br/>Pod]
            B1[Orchestrator<br/>Deployment]
            B2[Module-A<br/>Deployment]
            C1[MongoDB<br/>StatefulSet]
            D1[Prometheus<br/>Monitoring]
        end
        
        subgraph "Ingress 層"
            E[Ingress Controller<br/>NGINX]
        end
    end
    
    subgraph "外部服務 / External Services"
        F[GitHub Actions<br/>CI/CD]
        G[ArgoCD<br/>GitOps]
        H[Google Container Registry<br/>映像儲存]
    end
    
    E --> A1
    E --> A2
    A1 --> B1
    A2 --> B1
    B1 --> B2
    B2 --> C1
    B1 --> D1
    F --> H
    G --> B1
    G --> B2
    H --> A1
    H --> B1
```

---

## 資料流量與效能指標 / Data Flow & Performance Metrics

### 關鍵路徑延遲 / Critical Path Latency

```mermaid
gantt
    title 請求處理時間分解 / Request Processing Time Breakdown
    dateFormat X
    axisFormat %L ms
    
    section API 層
    接收請求 :0, 2
    
    section 協調層
    路由分配 :2, 5
    
    section 粒子核心
    邏輯解析 :5, 15
    粒子執行 :15, 35
    
    section C 引擎
    底層運算 :35, 45
    
    section 儲存層
    資料保存 :45, 55
    
    section 回應
    組裝返回 :55, 60
```

---

## 延伸閱讀 / Further Reading

- 📖 [系統架構詳細文檔](../ARCHITECTURE.md)
- 🚀 [部署指南](../DEPLOYMENT.md)
- 🔧 [配置說明](./CONFIGURATION.md)
- 📊 [性能優化](../PERFORMANCE_IMPROVEMENTS.md)
- 🧪 [測試指南](../tests/README.md)

---

## 圖例說明 / Legend

- **矩形框**: 處理模組 / Processing modules
- **圓柱體**: 資料儲存 / Data storage
- **箭頭**: 資料流向 / Data flow direction
- **虛線**: 非同步通訊 / Asynchronous communication
- **實線**: 同步通訊 / Synchronous communication

---

**最後更新 / Last Updated**: 2026-02-05  
**維護者 / Maintainer**: FlowAgent Team
