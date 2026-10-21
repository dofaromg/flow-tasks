# 🔒 MRLiou 私人開發與觀測指南
# MRLiou Private Development & Observation Guide

> **品牌所有權 / Brand Ownership**: All Rights Reserved © 2025 **Mr.liou**
> 
> 本專案為 **MRLiou** 品牌私人開發與觀測專用
> 
> **目前狀態**: 🔐 私人開發中，不對外公開

---

## 🎯 專案性質說明

### ✅ 這是什麼？

這是 **MRLiou 粒子語言核心系統 (Particle Language Core System)** 的私人開發與觀測環境。

- 👤 **開發者**: MRLiou (z814241@gmail.com)
- 🏢 **品牌**: MRLiou / Mr.liou
- 🔒 **性質**: 私人開發、觀測、研究
- 📵 **狀態**: **不對外公開**

### ❌ 這不是什麼？

- ❌ 不是公開服務
- ❌ 不需要部署到雲端
- ❌ 不需要對外展示
- ❌ 不需要生產環境配置

---

## 🚀 快速開始（私人開發）

### 選項 1: 本地開發環境（推薦）

```bash
# 1. 克隆倉庫（私人）
git clone https://github.com/dofaromg/flow-tasks.git
cd flow-tasks

# 2. 設置環境變數（可選）
cp .env.example .env.private
# 編輯 .env.private 根據需要

# 3. 啟動開發環境
docker-compose -f docker-compose.dev.yml up -d

# 4. 訪問本地環境
# http://localhost:3000 (Next.js)
# http://localhost:4321 (Astro)
```

### 選項 2: Python 粒子核心開發

```bash
# 1. 設置 Python 環境
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 2. 安裝依賴
pip install -r requirements.txt
pip install -r particle_core/requirements.txt

# 3. 運行粒子核心
cd particle_core
python demo.py demo

# 4. CLI 運行
python src/cli_runner.py
```

---

## 📊 私人觀測與監控

### 本地觀測工具

#### 1. Docker 容器監控
```bash
# 查看運行狀態
docker ps

# 查看資源使用
docker stats

# 查看日誌
docker logs -f <container_name>
```

#### 2. 系統性能監控
```bash
# CPU 和內存使用
top
htop  # 如果安裝

# 磁盤使用
df -h

# 網絡連接
netstat -tulpn
```

#### 3. 應用日誌觀測
```bash
# Next.js 開發日誌
npm run dev

# Python 粒子核心日誌
cd particle_core
python demo.py demo 2>&1 | tee logs/demo_$(date +%Y%m%d).log
```

### 創建觀測儀表板（本地）

創建 `observe-dashboard.sh`：
```bash
#!/bin/bash
# MRLiou 私人觀測儀表板

echo "═══════════════════════════════════════════════"
echo "  🔒 MRLiou 私人開發觀測儀表板"
echo "  © $(date +%Y) Mr.liou - All Rights Reserved"
echo "═══════════════════════════════════════════════"
echo ""

echo "📊 Docker 容器狀態:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo ""

echo "💾 磁盤使用:"
df -h | grep -E "Filesystem|/$"
echo ""

echo "🧠 內存使用:"
free -h
echo ""

echo "🔥 最近日誌 (最後 5 行):"
if [ -d "logs" ]; then
    tail -n 5 logs/*.log 2>/dev/null || echo "無日誌文件"
fi
echo ""

echo "✅ 觀測完成 - $(date)"
```

使用：
```bash
chmod +x observe-dashboard.sh
./observe-dashboard.sh
```

---

## 🔐 隱私與安全設定

### 1. Git 隱私配置

確保私人文件不被提交：

```bash
# 添加到 .gitignore
echo "" >> .gitignore
echo "# MRLiou 私人開發文件" >> .gitignore
echo ".env.private" >> .gitignore
echo "logs/*.log" >> .gitignore
echo "private_notes/" >> .gitignore
echo "observations/" >> .gitignore
echo "*.private.*" >> .gitignore
```

### 2. 環境變數隔離

創建 `.env.private`（不提交到 Git）：
```bash
# MRLiou 私人開發環境變數
# © Mr.liou - Private Development Only

# 標記為私人
ENVIRONMENT=private_development
OWNER=MRLiou

# 關閉公開功能
PUBLIC_ACCESS=false
ANALYTICS_ENABLED=false
EXTERNAL_SHARING=false

# 本地開發配置
DEV_MODE=true
DEBUG=true
LOG_LEVEL=verbose
```

### 3. 網絡隔離

使用本地網絡，不暴露到公網：

```yaml
# docker-compose.dev.yml
networks:
  mrliou-private-net:
    driver: bridge
    internal: true  # 不連接外部網絡
```

---

## 📝 開發筆記與觀測記錄

### 創建私人筆記結構

```bash
# 創建私人觀測目錄
mkdir -p private_notes/observations
mkdir -p private_notes/experiments
mkdir -p private_notes/ideas

# 創建模板
cat > private_notes/template.md << 'EOF'
# MRLiou 開發筆記
© Mr.liou - $(date +%Y-%m-%d)

## 日期
$(date)

## 觀測主題


## 實驗內容


## 發現與想法


## 下一步


---
品牌: MRLiou
類型: 私人開發觀測
狀態: 不對外公開
EOF
```

### 觀測日誌格式

```markdown
# MRLiou 觀測日誌 - [日期]

## 系統狀態
- [ ] Docker 容器運行正常
- [ ] 粒子核心測試通過
- [ ] 記憶封存功能正常

## 今日觀測
1. ...
2. ...

## 性能指標
- CPU: 
- 內存:
- 響應時間:

## 待辦事項
- [ ] ...
- [ ] ...

---
© Mr.liou | MRLiou 品牌私人開發
```

---

## 🛠️ 開發工具配置

### VS Code 設定（私人開發）

創建 `.vscode/settings.json`：
```json
{
  "editor.formatOnSave": true,
  "files.exclude": {
    "**/.git": true,
    "**/.env.private": true,
    "private_notes/": true
  },
  "search.exclude": {
    "private_notes/": true,
    "observations/": true
  },
  "git.ignoreLimitWarning": true,
  "editor.rulers": [80, 120],
  "files.associations": {
    "*.private.*": "plaintext"
  }
}
```

### Docker Compose 開發模式

創建 `docker-compose.dev.yml`：
```yaml
version: '3.8'

# MRLiou 私人開發環境
# © Mr.liou - Private Development Only

services:
  nextjs-dev:
    build:
      context: .
      dockerfile: apps/nextjs-frontend/Dockerfile
      target: development
    ports:
      - "127.0.0.1:3000:3000"  # 只綁定 localhost
    environment:
      - NODE_ENV=development
      - OWNER=MRLiou
      - PRIVATE_DEV=true
    volumes:
      - ./apps/nextjs-frontend:/app
      - /app/node_modules
    networks:
      - mrliou-private
    restart: unless-stopped

  mongodb-dev:
    image: mongo:6.0
    ports:
      - "127.0.0.1:27017:27017"  # 只綁定 localhost
    environment:
      - MONGO_INITDB_ROOT_USERNAME=mrliou_dev
      - MONGO_INITDB_ROOT_PASSWORD=私人開發密碼請修改
    volumes:
      - mongodb-dev-data:/data/db
    networks:
      - mrliou-private
    restart: unless-stopped

volumes:
  mongodb-dev-data:
    driver: local

networks:
  mrliou-private:
    driver: bridge
    internal: false  # 允許訪問外部（用於拉取包）
```

---

## 📦 MRLiou 粒子語言核心開發

### 粒子核心結構

```
particle_core/
├── src/
│   ├── cli_runner.py          # CLI 模擬器
│   ├── logic_pipeline.py      # 邏輯管線
│   ├── memory_archive_seed.py # 記憶封存
│   └── ...
├── examples/                   # 範例
├── docs/                      # 文檔
└── tests/                     # 測試
```

### 私人開發工作流

```bash
# 1. 創建實驗分支
git checkout -b private/experiment-$(date +%Y%m%d)

# 2. 開發與測試
cd particle_core
python demo.py demo

# 3. 記錄觀測
echo "實驗: ..." >> ../private_notes/observations/$(date +%Y%m%d).md

# 4. 本地提交（不推送）
git add .
git commit -m "MRLiou 私人實驗: $(date +%Y%m%d)"
# 不執行 git push（保持私人）
```

### 測試私人功能

```bash
# 運行所有測試
python -m pytest particle_core/tests/

# 測試特定模組
python -m pytest particle_core/tests/test_logic_pipeline.py -v

# 測試覆蓋率
python -m pytest --cov=particle_core --cov-report=html
```

---

## 🗂️ 私人文件組織

### 推薦目錄結構

```
flow-tasks/
├── private_notes/              # 🔒 私人筆記（不提交）
│   ├── observations/          # 觀測記錄
│   ├── experiments/           # 實驗記錄
│   └── ideas/                 # 想法筆記
├── observations/               # 🔒 系統觀測數據（不提交）
│   ├── logs/                  # 日誌
│   ├── metrics/               # 指標
│   └── screenshots/           # 截圖
├── .env.private               # 🔒 私人環境變數（不提交）
├── docker-compose.dev.yml     # 開發環境配置
└── observe-dashboard.sh       # 觀測儀表板腳本
```

### 創建結構

```bash
# 一鍵創建私人開發結構
mkdir -p private_notes/{observations,experiments,ideas}
mkdir -p observations/{logs,metrics,screenshots}
touch .env.private
touch observe-dashboard.sh
chmod +x observe-dashboard.sh

echo "✅ MRLiou 私人開發結構創建完成"
```

---

## 🔍 觀測檢查清單

### 每日觀測項目

```markdown
## MRLiou 每日觀測檢查清單

### 系統健康
- [ ] Docker 容器狀態
- [ ] 磁盤空間充足 (> 10GB)
- [ ] 內存使用正常 (< 80%)
- [ ] CPU 使用正常 (< 70%)

### 功能測試
- [ ] 粒子核心運行正常
- [ ] CLI 工具可用
- [ ] 記憶封存功能測試
- [ ] 數據庫連接正常

### 開發進度
- [ ] 今日開發目標
- [ ] 新功能測試
- [ ] Bug 修復
- [ ] 文檔更新

### 筆記與記錄
- [ ] 觀測日誌已更新
- [ ] 實驗記錄已保存
- [ ] 私人筆記已備份

---
© Mr.liou | MRLiou 品牌 | $(date)
```

---

## 🚫 不需要的功能（已關閉）

### 已關閉/不使用的功能：

- ❌ Vercel 部署（不需要公開）
- ❌ GKE 雲端部署（私人開發）
- ❌ 公開 CI/CD（私人倉庫）
- ❌ 外部監控服務（本地觀測）
- ❌ 公開 API 端點（私人使用）
- ❌ 分析追蹤（不需要）
- ❌ 公開文檔（私人知識）

### 僅保留：

- ✅ 本地開發環境
- ✅ Docker Compose
- ✅ 私人筆記系統
- ✅ 本地觀測工具
- ✅ 粒子核心開發

---

## 📞 私人開發支持

### 聯絡信息

- 👤 **開發者**: MRLiou
- 📧 **Email**: z814241@gmail.com
- 🏢 **品牌**: MRLiou / Mr.liou
- 🔒 **性質**: 私人開發，不對外公開

### 自助資源（私人）

- 📖 私人筆記: `private_notes/`
- 📊 觀測記錄: `observations/`
- 🧪 實驗日誌: `private_notes/experiments/`

---

## 📝 授權聲明

```
All Rights Reserved © 2025 Mr.liou

本專案及所有衍生作品為 Mr.liou 的完整智慧財產權。
未經授權禁止複製、商業使用或分發。

This software system, language specification, and all 
derivative works remain the full intellectual property 
of Mr.liou.

Unauthorized reproduction, commercial usage, or 
distribution is prohibited.

品牌: MRLiou / Mr.liou
性質: 私人開發與觀測
狀態: 不對外公開
```

---

## ✅ 快速命令參考

```bash
# 啟動私人開發環境
docker-compose -f docker-compose.dev.yml up -d

# 查看觀測儀表板
./observe-dashboard.sh

# 運行粒子核心
cd particle_core && python demo.py demo

# 查看日誌
tail -f observations/logs/*.log

# 停止所有服務
docker-compose -f docker-compose.dev.yml down

# 備份私人數據
tar -czf backup-$(date +%Y%m%d).tar.gz private_notes/ observations/
```

---

**🔒 提醒**: 這是 **MRLiou 品牌**的私人開發環境，所有內容不對外公開。

**© 2025 Mr.liou | MRLiou - All Rights Reserved**
