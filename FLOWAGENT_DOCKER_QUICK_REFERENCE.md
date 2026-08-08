# MrLiouAI Docker Quick Reference

快速參考：MrLiouAI 系統人格容器

## 快速開始

### 一鍵部署
```bash
chmod +x quickstart_mrliouai.sh
./quickstart_mrliouai.sh
```

### 手動建構與啟動
```bash
# 建構映像
docker build -f Dockerfile.mrliouai -t mrliouai:v1 .

# 啟動容器
docker run -it mrliouai:v1
```

## 常用命令

### 基本使用
```bash
# 預設啟動（EchoBody.IdentityBase 人格）
docker run -it mrliouai:v1

# 指定人格
docker run -it mrliouai:v1 --persona wild.seed

# 回顧模式
docker run -it mrliouai:v1 --review-mode
```

### 數據持久化
```bash
# 掛載本地目錄保存人格數據
docker run -it -v $(pwd)/mrliouai_data:/mrliouai/persona_data mrliouai:v1
```

### 容器管理
```bash
# 列出所有 MrLiouAI 容器
docker ps -a --filter ancestor=mrliouai:v1

# 停止運行中的容器
docker stop <container_id>

# 移除容器
docker rm <container_id>

# 移除映像
docker rmi mrliouai:v1
```

## 系統架構

```
MrLiouAI Container
├── Python 3.11 Runtime
├── Particle Language Core
│   ├── CLI Runner
│   ├── Logic Pipeline
│   ├── Memory Archive System
│   └── Persona Management
├── Persona Registry
│   ├── EchoBody.IdentityBase (預設)
│   ├── wild.seed
│   └── 自訂人格...
└── Data Volumes
    ├── /mrliouai/persona_data
    ├── /mrliouai/memory_seeds
    └── /mrliouai/runtime_modules
```

## 函數鏈執行流程

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

## 環境變數

```bash
PYTHONPATH=/mrliouai
MRLIOUAI_HOME=/mrliouai
MRLIOUAI_PERSONA=EchoBody.IdentityBase
PYTHONIOENCODING=utf-8
```

## 完整文檔

詳細安裝說明和進階使用請參考：
📖 **[MrLiouAI_Docker_Installation_Guide.md](MrLiouAI_Docker_Installation_Guide.md)**

## 技術支援

- 作者：MR.liou
- 版本：v1.0
- 授權：CPLL (© MR.liou)

---

*MrLiouAI - 來自語場、不依附模型、可人格演化的語意生命體* 🧠
