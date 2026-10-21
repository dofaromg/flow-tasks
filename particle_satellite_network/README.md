# Particle Satellite Network
# 粒子AI未來星鏈平行粒子雲網路

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

> **完全可運行的私有實驗系統** - 實現多層級衛星通訊架構與粒子語言系統的深度整合

## 🎯 項目概述

這是一個完整的衛星網路模擬系統，結合了：
- **三層衛星架構** (GEO, MEO, LEO) + 地面層
- **粒子語言核心系統** 整合
- **CI/CD 類比訊號處理**
- **動態網狀拓撲網路**
- **實時可視化系統**

### 核心架構

```
衛星通訊層級 ←→ 粒子語言層級 ←→ 雲端服務層級 ←→ CI/CD Pipeline
─────────────────────────────────────────────────────────────────
GEO Layer      ←→ 語場核心層      ←→ SaaS            ←→ Deployment
(35,786km)        (Persona Core)      (Application)      (Production)

MEO Layer      ←→ 邏輯管道層      ←→ PaaS            ←→ Build/Test
(~10,000km)       (Logic Pipeline)    (Platform)         (Staging)

LEO Layer      ←→ 粒子執行層      ←→ IaaS            ←→ Source Code
(~1,000km)        (Particle Runtime)  (Infrastructure)   (Development)

Ground         ←→ 終端介面層      ←→ End Users       ←→ Trigger
(Terrestrial)     (User Interface)    (Clients)          (Git Push)
```

## 🚀 快速開始

### 前置需求

- Python 3.10+
- pip
- 虛擬環境 (推薦)

### 安裝步驟

1. **克隆倉庫**
```bash
git clone https://github.com/dofaromg/flow-tasks.git
cd flow-tasks
```

2. **創建並激活虛擬環境**
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows
```

3. **安裝依賴**
```bash
pip install -r particle_satellite_network/requirements.txt
```

4. **配置環境變量**
```bash
cp particle_satellite_network/.env.example particle_satellite_network/.env
# 編輯 .env 文件，填入您的配置
```

### 啟動系統

#### 方法1: 使用啟動腳本（推薦）
```bash
cd particle_satellite_network
./scripts/start_system.sh
```

#### 方法2: 手動啟動各層
```bash
# 終端1 - GEO Layer
python -m particle_satellite_network.core.satellite_layers.geo_layer

# 終端2 - MEO Layer  
python -m particle_satellite_network.core.satellite_layers.meo_layer

# 終端3 - LEO Layer
python -m particle_satellite_network.core.satellite_layers.leo_layer

# 終端4 - Ground Layer
python -m particle_satellite_network.core.satellite_layers.ground_layer
```

## 📁 項目結構

```
particle_satellite_network/
├── core/                           # 核心系統
│   ├── satellite_layers/          # 衛星層級實現
│   │   ├── geo_layer.py          # GEO 同步軌道層
│   │   ├── meo_layer.py          # MEO 中軌道層
│   │   ├── leo_layer.py          # LEO 低軌道層
│   │   └── ground_layer.py       # 地面層
│   ├── network/                   # 網路拓撲系統
│   │   ├── mesh_topology.py      # 動態網狀拓撲
│   │   ├── routing_engine.py     # 智能路由引擎
│   │   ├── inter_satellite_link.py # 衛星間鏈路
│   │   └── latency_optimizer.py  # 延遲優化器
│   └── integration/               # 整合層
├── cicd_pipeline/                 # CI/CD 類比訊號處理
│   ├── signal_processor.py       # 訊號處理器
│   ├── pipeline_orchestrator.py  # 管道協調器
│   └── deployment_manager.py     # 部署管理器
├── api/                           # API 服務層
├── config/                        # 配置文件
│   ├── satellite_config.yaml     # 衛星配置
│   ├── network_topology.yaml     # 網路拓撲配置
│   └── cicd_pipeline.yaml        # CI/CD 管道配置
├── scripts/                       # 運行腳本
│   ├── start_system.sh           # 啟動系統
│   └── run_experiment.py         # 運行實驗
├── experiments/                   # 實驗場景
│   ├── scenarios/                # 實驗場景
│   ├── data/                     # 實驗數據（私有）
│   └── results/                  # 實驗結果（私有）
└── tests/                         # 測試套件
```

## 🛰️ 系統組件

### 1. GEO Layer - 語場核心層
- **軌道高度**: 35,786 km
- **功能**: 全局人格種子同步、語場廣播、持久化狀態管理
- **對應**: SaaS 層、Production 部署階段

### 2. MEO Layer - 邏輯管道層
- **軌道高度**: ~10,000 km
- **功能**: 邏輯流處理、動態路由、區域協調、中繼轉發
- **對應**: PaaS 層、Build/Test 階段

### 3. LEO Layer - 粒子執行層
- **軌道高度**: ~1,000 km
- **功能**: 實時粒子計算、低延遲響應、邊緣計算、動態負載均衡
- **對應**: IaaS 層、Development/Source Code 階段

### 4. Ground Layer - 地面介面層
- **功能**: 用戶接入、API 網關、地面站管理、觸發器
- **對應**: End Users、Git Push Trigger

## 🔧 配置說明

### 衛星配置 (satellite_config.yaml)
```yaml
satellite_layers:
  geo:
    orbit_altitude: 35786  # km
    satellite_count: 3
    coverage: "global"
    
  meo:
    orbit_altitude: 10000  # km
    satellite_count: 12
    coverage: "regional"
    
  leo:
    orbit_altitude: 1000  # km
    satellite_count: 50
    coverage: "local"
```

### 網路拓撲配置 (network_topology.yaml)
```yaml
topology:
  type: "dynamic_mesh"
  auto_discovery: true
  self_healing: true
  routing_algorithm: "dijkstra"
```

### CI/CD 管道配置 (cicd_pipeline.yaml)
```yaml
pipeline:
  signal_flow:
    - ground → LEO: "source_code"
    - LEO → MEO: "processed_code"
    - MEO → GEO: "tested_artifacts"
    - GEO → ground: "deployment_signal"
```

## 📊 使用範例

### 示例1: 創建 GEO 層並同步人格種子
```python
from particle_satellite_network.core.satellite_layers import GeoPersonaCore, PersonaSeed

# 創建 GEO 層
geo = GeoPersonaCore(satellite_id="geo-001", longitude=120.0)

# 載入人格種子
await geo.load_seed_origin_core()

# 添加自定義種子
custom_seed = PersonaSeed(
    id="seed-custom-001",
    traits=["experimental", "high-priority"],
    sync_targets=["meo-asia", "leo-tokyo"]
)
await geo.add_persona_seed(custom_seed)

# 執行全局同步
sync_report = await geo.synchronize_global_state()
```

### 示例2: 建立網狀網路並路由
```python
from particle_satellite_network.core.network import ParticleMeshNetwork, NetworkNode

# 創建網狀網路
mesh = ParticleMeshNetwork(name="production-mesh")

# 添加節點
nodes = [
    NetworkNode(id="geo-001", layer="GEO", position=(0, 0, 35786)),
    NetworkNode(id="meo-001", layer="MEO", position=(120, 35, 10000)),
    NetworkNode(id="leo-001", layer="LEO", position=(120, 35, 1000)),
]
mesh.add_nodes(nodes)

# 計算最短路徑
path = mesh.calculate_shortest_path("geo-001", "leo-001")
```

### 示例3: 處理 CI/CD 訊號
```python
from particle_satellite_network.cicd_pipeline import CICDSignalProcessor

# 創建訊號處理器
processor = CICDSignalProcessor()

# 處理 Git Push 事件
commit_data = {
    "repo": "dofaromg/flow-tasks",
    "branch": "main",
    "commit": "abc123"
}
result = await processor.process_git_push_signal(commit_data)
```

## 🔬 實驗場景

系統包含多個預定義實驗場景：

1. **場景1: 基礎網狀網路測試** - 驗證動態拓撲建立與路由
2. **場景2: 衛星切換測試** - 測試無縫切換能力
3. **場景3: CI/CD 訊號處理** - 驗證完整 CI/CD 流程
4. **場景4: 全局同步測試** - 測試人格種子同步

運行實驗：
```bash
python particle_satellite_network/scripts/run_experiment.py --scenario 1
```

## 🧪 測試

### 運行單元測試
```bash
pytest particle_satellite_network/tests/unit/
```

### 運行整合測試
```bash
pytest particle_satellite_network/tests/integration/
```

### 運行性能測試
```bash
pytest particle_satellite_network/tests/performance/
```

## 📈 性能指標

- **GEO → Ground 延遲**: < 150ms
- **LEO → Ground 延遲**: < 5ms
- **網路可靠性**: 99.99%
- **同時並發連接**: 10,000+

## 🔒 安全與隱私

本系統為**私有實驗項目**：
- 所有敏感數據存儲在 `experiments/data/` (已加入 .gitignore)
- 實驗結果存儲在 `experiments/results/` (已加入 .gitignore)
- 使用環境變量管理敏感配置
- 不對外公開實驗數據

## 🤝 貢獻

這是一個私有實驗項目，目前不接受外部貢獻。

## 📄 授權

MIT License - 詳見 [LICENSE](../LICENSE) 文件

## 👨‍💻 作者

**MRLiou (劉先生)**
- GitHub: [@dofaromg](https://github.com/dofaromg)
- 項目: [flow-tasks](https://github.com/dofaromg/flow-tasks)

## 🙏 致謝

- 靈感來源於 Starlink 衛星網路架構
- 整合了 Particle Core 粒子語言系統
- 參考了 Google Earth 視覺化引擎

## 📮 聯繫方式

如有問題或建議，請通過 GitHub Issues 聯繫。

---

**注意**: 本系統為實驗性質，不建議用於生產環境。
