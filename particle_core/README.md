# MRLiou Particle Language Core

MRLiou 粒子語言核心系統 - 邏輯種子運算與函數鏈執行框架

## 功能特色

- **函數鏈執行**: 支援 STRUCTURE → MARK → FLOW → RECURSE → STORE 邏輯鏈
- **邏輯壓縮**: .flpkg 格式的邏輯模組壓縮與還原
- **CLI 模擬器**: 命令列邏輯模擬與執行介面
- **人類可讀**: 邏輯步驟的中文說明與視覺化
- **模組化設計**: 可擴展的邏輯模組與人格生成系統

## 快速開始

```bash
# 執行 CLI 模擬器
python src/cli_runner.py

# 邏輯管線處理
python src/logic_pipeline.py

# 壓縮還原測試
python src/rebuild_fn.py
```

## 需求

- Python 3.10+
- fastapi, uvicorn, rich

## 授權

FlowAgent 專用任務系統內部模組