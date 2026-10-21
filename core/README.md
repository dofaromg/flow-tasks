# FlowAgent Core Module / 核心模組

## 粒子語言系統簡介 / Particle Language System Introduction

FlowAgent 核心模組是 **粒子語言 (Particle Language)** 執行系統的核心實現，提供記憶管理、粒子字典與邏輯執行的基礎設施。粒子語言是一種創新的邏輯表達與執行框架，通過「粒子」（Particle）作為最小的邏輯執行單元，實現從高層 API 到底層 C 引擎的完整執行鏈路。

The FlowAgent core module is the foundational implementation of the **Particle Language** execution system, providing infrastructure for memory management, particle dictionaries, and logic execution. Particle Language is an innovative logical expression and execution framework that uses "particles" as the smallest logical execution units, implementing a complete execution chain from high-level API to low-level C engine.

### 核心特性 / Core Features

- **粒子執行單元 (Particle Execution Unit)**: 最小化的邏輯執行單位
- **記憶系統 (Memory System)**: 長期、短期與工作記憶管理
- **粒子字典 (Particle Dictionary)**: 粒子模式匹配與管理
- **多語言執行引擎 (Multi-language Engine)**: Python、C、Perl、Tcl 協同工作

---

## 專案架構 / Project Architecture

### 主要語言 / Primary Languages

此專案採用多語言架構，各語言分工明確：

This project adopts a multi-language architecture with clear division of responsibilities:

| 語言 / Language | 用途 / Purpose | 主要檔案 / Key Files |
|-----------------|----------------|----------------------|
| **Python** | 核心邏輯、API 層、粒子執行引擎 | `memory_system.py`, `particle_dict.py` |
| **C** | 高性能運算、底層執行引擎 | `xdiffi.c`, `xemit.c`, `xutils.c` |
| **Perl** | Web 介面、Git 整合 | `gitweb.perl` |
| **Tcl** | 腳本生成、構建工具 | `generate-tcl.sh` |

### 目錄結構 / Directory Structure

```
flow-tasks/
├── core/                    # 核心模組 (本目錄)
│   ├── __init__.py         # Python 包初始化
│   ├── memory_system.py    # 記憶系統實現
│   ├── particle_dict.py    # 粒子字典實現
│   └── README.md           # 本文檔
│
├── particle_core/           # 粒子語言完整系統
│   ├── src/                # 源代碼
│   ├── docs/               # 文檔
│   ├── examples/           # 範例
│   └── tests/              # 測試
│
├── *.c                     # C 執行引擎
│   ├── xdiffi.c           # 差異演算法
│   ├── xemit.c            # 輸出處理
│   └── xutils.c           # 工具函數
│
├── apps/                   # 微服務應用
├── cluster/                # Kubernetes 配置
├── docs/                   # 專案文檔
├── scripts/                # 工具腳本
└── tests/                  # 根層級測試
```

### 核心模組說明 / Core Module Description

#### 1. `memory_system.py` - 記憶系統

提供四種記憶類型的管理：
- **語義記憶 (Semantic)**: 知識與概念
- **情節記憶 (Episodic)**: 事件與經歷
- **程序記憶 (Procedural)**: 操作與流程
- **工作記憶 (Working)**: 暫存與處理

```python
from core.memory_system import FlowMemoryCore, MemoryType

memory = FlowMemoryCore()
memory.commit("Hello World", MemoryType.SEMANTIC, tags=["greeting"])
```

#### 2. `particle_dict.py` - 粒子字典

管理粒子定義、模式匹配與粒子鏈：
- 粒子註冊與查詢
- 模式匹配與搜索
- 粒子鏈組裝與執行

```python
from core.particle_dict import ParticleDictionary, Particle

dictionary = ParticleDictionary()
particle = dictionary.get_particle("FX.01")  # 取得「記住」粒子
```

---

## 開發資源與連結 / Development Resources and Links

### 學習資源 / Learning Resources

1. **粒子語言核心系統**
   - 📂 主要實現: [`particle_core/`](../particle_core/)
   - 📖 文檔: [`particle_core/README.md`](../particle_core/README.md)
   - 🔧 範例: [`particle_core/examples/`](../particle_core/examples/)

2. **API 與執行引擎**
   - 📄 API 規格: [`P.MetaEnv.openapi.yaml.txt`](../P.MetaEnv.openapi.yaml.txt)
   - 🚀 執行引擎: C 源碼檔案 (`xdiffi.c`, `xemit.c`, 等)

3. **記憶封存系統**
   - 📘 快速入門: [`記憶封存種子快速入門.md`](../記憶封存種子快速入門.md)
   - 📗 更新說明: [`記憶封存種子系統更新說明.md`](../記憶封存種子系統更新說明.md)

### 關鍵儲存庫連結 / Key Repository Links

- **主儲存庫 / Main Repository**: [https://github.com/dofaromg/flow-tasks](https://github.com/dofaromg/flow-tasks)
- **粒子語言規格 / Particle Language Spec**: [`particle_core/language_spec/`](../particle_core/language_spec/)
- **系統架構文檔 / System Architecture**: [`ARCHITECTURE.md`](../ARCHITECTURE.md)
- **部署指南 / Deployment Guide**: [`DEPLOYMENT.md`](../DEPLOYMENT.md)

### 相關文檔 / Related Documentation

- [系統概覽 / System Overview](../00_System_Overview.md)
- [架構說明 / Architecture](../ARCHITECTURE.md)
- [配置說明 / Configuration](../docs/CONFIGURATION.md)
- [性能優化 / Performance](../PERFORMANCE_IMPROVEMENTS.md)

---

## 快速開始 / Quick Start

### 安裝依賴 / Install Dependencies

```bash
# Python 依賴
pip install -r requirements.txt
pip install -r particle_core/requirements.txt

# 驗證安裝
python -c "from core.memory_system import FlowMemoryCore; print('✓ Core module loaded')"
```

### 基本使用 / Basic Usage

```python
# 導入核心模組
from core.memory_system import FlowMemoryCore, MemoryType
from core.particle_dict import ParticleDictionary

# 初始化系統
memory = FlowMemoryCore()
dictionary = ParticleDictionary()

# 提交記憶
memory.commit(
    content="粒子語言學習",
    memory_type=MemoryType.SEMANTIC,
    tags=["learning", "particle"]
)

# 查詢粒子
particle = dictionary.get_particle("FX.01")
print(f"粒子: {particle.human_view}")  # 輸出: 粒子: 記住
```

### 執行測試 / Run Tests

```bash
# 執行核心測試
cd /home/runner/work/flow-tasks/flow-tasks
python -m pytest tests/ -v

# 執行粒子核心測試
cd particle_core
python demo.py demo
```

---

## 開發指南 / Development Guide

### 編碼規範 / Coding Standards

- **Python**: 遵循 PEP 8，使用類型提示
- **C**: 使用清晰的函數命名，添加註釋
- **文檔**: 支援雙語（中文/英文）

### 貢獻流程 / Contributing

1. Fork 此儲存庫
2. 創建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 開啟 Pull Request

---

## 授權 / License

FlowAgent 專用任務系統內部模組  
粒子語言規格遵循 CPLL 授權條款（© MR.liou）

---

## 聯絡方式 / Contact

如有任何問題或建議，請透過 GitHub Issues 提出。

For questions or suggestions, please submit via GitHub Issues.
