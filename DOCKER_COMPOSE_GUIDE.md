# 🐳 Docker Compose 快速部署指南

> 最簡單的本地/自託管部署方式！

## 🚀 快速開始

### 前置需求

- Docker 和 Docker Compose 已安裝
  ```bash
  docker --version
  docker-compose --version
  ```

### 3 步驟部署

#### 1. 克隆倉庫
```bash
git clone https://github.com/dofaromg/flow-tasks.git
cd flow-tasks
```

#### 2. 配置環境變數（可選）
```bash
# 複製環境變數範例
cp .env.docker-example .env

# 編輯 .env 文件（如需要）
nano .env
```

#### 3. 啟動服務
```bash
# 啟動所有服務
docker-compose up -d

# 查看日誌
docker-compose logs -f

# 查看運行狀態
docker-compose ps
```

#### 4. 訪問應用
```bash
# Next.js 前端
open http://localhost:3000

# MongoDB（如需要）
mongo mongodb://admin:changeme123@localhost:27017
```

---

## 📦 包含的服務

### Next.js Frontend
- **端口**: 3000
- **URL**: http://localhost:3000
- **描述**: 前端 Web 應用

### MongoDB Database
- **端口**: 27017
- **用戶名**: admin
- **密碼**: changeme123（請修改！）
- **描述**: 資料庫服務

---

## 🔧 常用命令

### 啟動服務
```bash
# 後台啟動
docker-compose up -d

# 前台啟動（可看日誌）
docker-compose up
```

### 停止服務
```bash
# 停止但保留容器
docker-compose stop

# 停止並刪除容器
docker-compose down

# 停止並刪除容器和數據卷
docker-compose down -v
```

### 查看狀態
```bash
# 查看運行狀態
docker-compose ps

# 查看日誌
docker-compose logs

# 實時查看特定服務日誌
docker-compose logs -f nextjs-frontend
```

### 重新構建
```bash
# 重新構建所有服務
docker-compose build

# 重新構建並啟動
docker-compose up -d --build

# 只重新構建特定服務
docker-compose build nextjs-frontend
```

### 進入容器
```bash
# 進入 Next.js 容器
docker-compose exec nextjs-frontend sh

# 進入 MongoDB 容器
docker-compose exec mongodb mongosh
```

---

## ⚙️ 環境變數配置

### .env 文件示例

```bash
# GrowthBook 功能旗標（可選）
NEXT_PUBLIC_GROWTHBOOK_API_HOST=https://cdn.growthbook.io
NEXT_PUBLIC_GROWTHBOOK_CLIENT_KEY=sdk-abc123xyz

# MongoDB 配置
MONGO_INITDB_ROOT_USERNAME=admin
MONGO_INITDB_ROOT_PASSWORD=your_secure_password_here

# Node 環境
NODE_ENV=production
```

### 重要提醒
⚠️ **生產環境請務必修改默認密碼！**

---

## 🔒 安全建議

### 1. 修改 MongoDB 密碼
```bash
# 在 .env 文件中設置強密碼
MONGO_INITDB_ROOT_PASSWORD=VeryStrongPassword123!
```

### 2. 使用 Docker Secrets（生產環境）
```yaml
secrets:
  mongo_password:
    file: ./secrets/mongo_password.txt

services:
  mongodb:
    secrets:
      - mongo_password
    environment:
      MONGO_INITDB_ROOT_PASSWORD_FILE: /run/secrets/mongo_password
```

### 3. 限制端口暴露
如果不需要外部訪問 MongoDB：
```yaml
# 只綁定到 localhost
ports:
  - "127.0.0.1:27017:27017"
```

---

## 📊 數據持久化

### 數據卷位置
```bash
# 查看數據卷
docker volume ls

# 查看 MongoDB 數據卷詳情
docker volume inspect flow-tasks_mongodb-data

# 備份數據卷
docker run --rm -v flow-tasks_mongodb-data:/data -v $(pwd):/backup \
  busybox tar czf /backup/mongodb-backup.tar.gz /data
```

### 恢復數據
```bash
# 從備份恢復
docker run --rm -v flow-tasks_mongodb-data:/data -v $(pwd):/backup \
  busybox tar xzf /backup/mongodb-backup.tar.gz -C /
```

---

## 🌐 反向代理（使用 Nginx）

### Nginx 配置示例

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

### 使用 Docker 反向代理

添加到 `docker-compose.yml`：
```yaml
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - nextjs-frontend
    networks:
      - flowagent-network
```

---

## 🔍 故障排除

### 服務無法啟動

**檢查日誌：**
```bash
docker-compose logs nextjs-frontend
```

**常見問題：**
1. **端口被佔用**
   ```bash
   # 檢查端口佔用
   lsof -i :3000
   lsof -i :27017
   
   # 修改 docker-compose.yml 中的端口
   ports:
     - "3001:3000"  # 改用 3001
   ```

2. **映像構建失敗**
   ```bash
   # 清理並重建
   docker-compose down
   docker-compose build --no-cache
   docker-compose up -d
   ```

3. **無法連接 MongoDB**
   ```bash
   # 檢查 MongoDB 是否運行
   docker-compose ps mongodb
   
   # 查看 MongoDB 日誌
   docker-compose logs mongodb
   ```

### 性能問題

**分配更多資源（Docker Desktop）：**
- Settings → Resources
- 增加 CPU 和內存

**使用生產模式：**
```bash
NODE_ENV=production docker-compose up -d
```

---

## 📈 監控和日誌

### 查看資源使用
```bash
# 查看容器資源使用
docker stats

# 只查看特定容器
docker stats flow-tasks_nextjs-frontend_1
```

### 日誌管理
```bash
# 查看最後 100 行日誌
docker-compose logs --tail=100 nextjs-frontend

# 查看特定時間的日誌
docker-compose logs --since 30m nextjs-frontend

# 導出日誌到文件
docker-compose logs > logs.txt
```

---

## 🚀 進階配置

### 添加更多服務

#### Astro Frontend（如有）
```yaml
astro-frontend:
  build:
    context: .
    dockerfile: apps/astro-frontend/Dockerfile
  ports:
    - "4321:4321"
  restart: unless-stopped
  networks:
    - flowagent-network
```

#### Redis 快取
```yaml
redis:
  image: redis:alpine
  ports:
    - "6379:6379"
  volumes:
    - redis-data:/data
  restart: unless-stopped
  networks:
    - flowagent-network
```

### 開發模式

創建 `docker-compose.dev.yml`：
```yaml
version: '3.8'

services:
  nextjs-frontend:
    build:
      context: .
      dockerfile: apps/nextjs-frontend/Dockerfile
      target: development  # 開發階段
    volumes:
      - .:/app
      - /app/node_modules
    environment:
      - NODE_ENV=development
    command: npm run dev
```

使用：
```bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

---

## 🌍 部署到服務器

### 1. 準備服務器
```bash
# SSH 連接到服務器
ssh user@your-server.com

# 安裝 Docker
curl -fsSL https://get.docker.com | sh

# 安裝 Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 2. 部署應用
```bash
# 克隆倉庫
git clone https://github.com/dofaromg/flow-tasks.git
cd flow-tasks

# 配置環境變數
cp .env.docker-example .env
nano .env  # 修改配置

# 啟動服務
docker-compose up -d
```

### 3. 設置自動啟動
```bash
# 創建 systemd 服務
sudo nano /etc/systemd/system/flowagent.service
```

內容：
```ini
[Unit]
Description=FlowAgent Docker Compose
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/path/to/flow-tasks
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down

[Install]
WantedBy=multi-user.target
```

啟用服務：
```bash
sudo systemctl enable flowagent
sudo systemctl start flowagent
```

---

## 📚 相關資源

- [Docker 官方文檔](https://docs.docker.com)
- [Docker Compose 文檔](https://docs.docker.com/compose/)
- [部署替代方案](DEPLOYMENT_ALTERNATIVES.md)
- [GKE 部署指南](DEPLOYMENT.md)

---

## ✅ 完成檢查清單

- [ ] Docker 和 Docker Compose 已安裝
- [ ] 克隆倉庫完成
- [ ] 環境變數已配置
- [ ] 服務啟動成功
- [ ] 可以訪問 http://localhost:3000
- [ ] MongoDB 運行正常
- [ ] 已修改默認密碼（生產環境）

---

## 🆘 需要幫助？

- [GitHub Issues](https://github.com/dofaromg/flow-tasks/issues)
- [Docker 社群](https://forums.docker.com)
- [Stack Overflow](https://stackoverflow.com/questions/tagged/docker-compose)

---

**💡 提示**: 這是最簡單的部署方式！適合本地開發和小型部署。如需企業級部署，請參考 [GKE 部署指南](DEPLOYMENT.md)。
