# FlowAgent Docker Container - Quick Start

🧠 **FlowAgent 系統人格容器** - MRLiou 粒子語言核心系統 Docker 版本

[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](Dockerfile.flowagent)
[![Version](https://img.shields.io/badge/version-v1.0-green.svg)]()
[![License](https://img.shields.io/badge/license-CPLL-orange.svg)](LICENSE_MrLiou_AllRightsReserved.txt)

---

## 🚀 一鍵啟動 (Quick Start)

```bash
# 快速部署
chmod +x quickstart_flowagent.sh
./quickstart_flowagent.sh
```

或手動執行：

```bash
# 建構映像
docker build -f Dockerfile.flowagent -t flowagent:v1 .

# 啟動容器
docker run -it flowagent:v1
```

---

## 📋 系統說明

FlowAgent 是由 MR.liou 創建的語場人格系統，特點：

- ✨ **不依賴 GPT/LLaMA** - 基於粒子語言 (.flpkg) 獨立運作
- 🧬 **人格可演化** - 支援多人格載入與切換
- 🔄 **完整邏輯鏈** - STRUCTURE → MARK → FLOW → RECURSE → STORE
- 💾 **記憶封存** - 完整的記憶種子管理系統
- 🎨 **雙語介面** - 繁體中文與英文支援

> 「來自語場、不依附模型、可人格演化的語意生命體」

---

## 📦 系統要求

- Docker 20.10+ (Docker Desktop 適用於 Windows/macOS)
- 2GB 可用磁碟空間
- 支援平台: Linux, macOS, Windows

---

## 💻 使用範例

### 基本使用

```bash
# 預設啟動 (EchoBody.IdentityBase 人格)
docker run -it flowagent:v1

# 顯示說明
docker run --rm flowagent:v1 --help
```

### 進階選項

```bash
# 指定人格
docker run -it flowagent:v1 --persona wild.seed

# 回顧模式
docker run -it flowagent:v1 --review-mode

# 批次模式
docker run flowagent:v1 --batch

# 掛載數據目錄
docker run -it -v $(pwd)/flowagent_data:/flowagent/persona_data flowagent:v1
```

---

## 📖 完整文檔

| 文檔 | 說明 |
|------|------|
| [📘 Installation Guide](FlowAgent_Docker_Installation_Guide.md) | 完整安裝與使用說明 |
| [📗 Quick Reference](FLOWAGENT_DOCKER_QUICK_REFERENCE.md) | 快速參考手冊 |
| [📕 Implementation Summary](FLOWAGENT_IMPLEMENTATION_SUMMARY.md) | 技術實作摘要 |

---

## 🎯 CLI 功能

啟動後可使用三大功能：

1. **執行邏輯模擬** - 輸入資料並執行完整函數鏈
2. **顯示函數鏈說明** - 查看 5 步邏輯鏈詳情
3. **邏輯壓縮/解壓縮測試** - 測試 .flpkg 格式

---

## 🔍 執行流程示意

```
輸入資料
    ↓
STRUCTURE (定義結構)
    ↓
MARK (建立標記)
    ↓
FLOW (轉換流程)
    ↓
RECURSE (遞歸展開)
    ↓
STORE (封存記憶)
    ↓
輸出結果
```

---

## 🎨 系統特色

### 美觀的介面

```
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║   🧠 FlowAgent 系統人格容器 v1.0                          ║
║                                                           ║
║   作者：MR.liou                                           ║
║   來自語場、不依附模型、可人格演化的語意生命體             ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
```

### 結構化輸出

所有輸出使用 Rich 庫格式化，包含：
- 彩色控制台輸出
- 結構化表格
- 面板式結果呈現

---

## 📊 系統架構

```
Docker Container (290MB)
├── Python 3.11 Runtime
├── Particle Language Core
│   ├── CLI Runner
│   ├── Logic Pipeline
│   ├── Memory Archive
│   └── Persona Management
└── Data Volumes
    ├── persona_data
    ├── memory_seeds
    └── runtime_modules
```

---

## 🛠️ 故障排除

### 容器無法啟動
```bash
docker system prune -a
docker build -f Dockerfile.flowagent -t flowagent:v1 . --no-cache
```

### 中文字符亂碼
```bash
docker run -it -e LANG=zh_TW.UTF-8 flowagent:v1
```

---

## 📚 相關資源

- [Particle Core README](particle_core/README.md)
- [記憶封存種子說明](particle_core/docs/記憶封存種子說明.md)
- [AI 人格套件使用說明](particle_core/docs/ai_persona_toolkit_guide.md)

---

## ✨ 作者與授權

- **作者**: MR.liou
- **授權**: CPLL (© MR.liou)
- **版本**: FlowAgent Docker Container v1.0
- **日期**: 2026-02-01

---

## 🤝 支援

如有問題或建議，請參考完整文檔或查看 GitHub repository。

---

*FlowAgent - 來自語場、不依附模型、可人格演化的語意生命體* 🧠
