# Ultimate AI Video System - Deployment Guide
# 小影AI終極版 - 完整部署指南

## 📋 系統概覽

這是一個專為私人家庭伺服器設計的終極AI視頻生成系統，充分利用高性能硬體資源為家庭成員提供專業級AI視頻製作能力。

### 硬體要求

- **GPU**: 6x NVIDIA V100 (32GB each) - 192GB GPU記憶體
- **RAM**: 3TB系統記憶體
- **CPU**: 4x Socket (128+ cores)
- **Storage**: 10TB+ SSD (至少500GB可用空間用於模型)
- **Network**: 10Gbps內網連接

### 軟體要求

- **OS**: Ubuntu 22.04 LTS (推薦)
- **CUDA**: 11.8+
- **cuDNN**: 8.9+
- **Python**: 3.10+
- **NVIDIA Driver**: 525+

## 🚀 快速部署

### 方法一：一鍵部署（推薦）

```bash
# 1. 克隆倉庫
git clone https://github.com/dofaromg/flow-tasks.git
cd flow-tasks

# 2. 運行部署腳本
sudo bash scripts/deploy_ultimate.sh

# 3. 訪問系統
# 打開瀏覽器訪問 http://your-server-ip:8000
```

### 方法二：手動部署

#### 步驟1：安裝系統依賴

```bash
# 更新系統
sudo apt update && sudo apt upgrade -y

# 安裝基礎工具
sudo apt install -y \
    python3.10 python3.10-venv python3-pip \
    git curl wget \
    build-essential \
    ffmpeg libsm6 libxext6

# 驗證NVIDIA驅動和CUDA
nvidia-smi
nvcc --version
```

#### 步驟2：創建Python虛擬環境

```bash
# 創建虛擬環境
python3.10 -m venv venv

# 激活虛擬環境
source venv/bin/activate

# 升級pip
pip install --upgrade pip
```

#### 步驟3：安裝Python依賴

```bash
# 安裝基礎依賴
pip install -r requirements.txt

# 安裝PyTorch (CUDA 11.8)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# 安裝FastAPI和其他依賴
pip install \
    fastapi uvicorn[standard] \
    python-multipart websockets \
    pyyaml psutil \
    numpy pillow opencv-python \
    librosa soundfile scipy
```

#### 步驟4：下載AI模型

```bash
# 創建模型目錄
mkdir -p models/checkpoints

# 下載模型（示例）
# 注意：實際部署需要下載約200GB的模型文件
# 建議使用HuggingFace CLI或ModelScope工具

# HuggingFace示例
huggingface-cli download \
    --repo-id "Organization/Model-Name" \
    --local-dir models/checkpoints/Model-Name

# 主要模型列表：
# - SadTalker v2 (數字人)
# - MuseTalk (數字人)
# - LivePortrait (數字人)
# - GeneFace++ (數字人)
# - F5-TTS v2 (聲音克隆)
# - CosyVoice (聲音克隆)
# - GPT-SoVITS v2 (聲音克隆)
# - XTTS v3 (聲音克隆)
# - Real-ESRGAN (視頻增強)
# - GFPGAN (面部修復)
# - CodeFormer (面部修復)
# - BasicVSR++ (視頻超分)
```

#### 步驟5：配置系統

```bash
# 複製配置模板
cp .env.example .env.ultimate

# 編輯配置文件
nano .env.ultimate

# 設置環境變量
export CUDA_VISIBLE_DEVICES=0,1,2,3,4,5
export MODEL_BASE_PATH=./models
```

#### 步驟6：創建工作區

```bash
# 創建用戶工作區
mkdir -p workspaces/{admin,parent1,parent2,child1,child2}/{uploads,outputs}

# 創建共享資源
mkdir -p shared/{templates,music,effects,fonts,family_album}

# 設置權限
chmod -R 755 workspaces shared
```

#### 步驟7：啟動服務

```bash
# 前台運行（測試）
python3 main_ultimate.py

# 後台運行（生產）
nohup python3 main_ultimate.py > logs/ultimate_system.log 2>&1 &

# 使用systemd（推薦生產環境）
sudo cp scripts/ultimate-system.service /etc/systemd/system/
sudo systemctl enable ultimate-system
sudo systemctl start ultimate-system
sudo systemctl status ultimate-system
```

## 🎯 系統架構

### 核心組件

```
Ultimate AI Video System
├── GPU Orchestrator (GPU編排器)
│   ├── 6-GPU智能分配
│   ├── 負載均衡
│   └── 健康監控
├── Memory Manager (記憶體管理器)
│   ├── 3TB RAM管理
│   ├── 模型常駐
│   └── 緩存優化
├── Model Cache (模型緩存)
│   ├── 零冷啟動
│   ├── 預加載系統
│   └── LRU策略
└── 10 AI Engines (AI引擎)
    ├── Digital Human Ultra
    ├── Voice Clone Unlimited
    ├── Photo to Video Pro
    ├── Video Enhancer 8K
    ├── Face Swap Realtime
    ├── Motion Transfer
    ├── Virtual Human 3D
    ├── Music Generator
    ├── Smart Editor
    └── VFX Compositor
```

### GPU分配策略

```yaml
GPU 0-1: 數字人生成 (雙卡並行)
GPU 2:   聲音克隆
GPU 3:   照片轉視頻 + 動作遷移
GPU 4:   視頻增強 + 換臉
GPU 5:   輔助功能 (3D、音樂、特效)
```

### 記憶體分配

```
總記憶體: 3TB
├── 系統預留: 200GB
├── AI模型: 180GB (常駐)
├── 任務緩存: 1TB
├── 用戶工作區: 500GB
└── 其他: 1.12TB
```

## 👥 家庭成員配置

系統支持5個家庭成員同時使用：

1. **管理員** (admin)
   - 最高優先級
   - 無配額限制
   - 完整功能訪問

2. **家長1-2** (parent1, parent2)
   - 高優先級
   - 每日100個任務
   - 進階功能訪問

3. **小朋友1-2** (child1, child2)
   - 中等優先級
   - 每日50個任務
   - 兒童友好模式

配置文件: `configs/family_users.yaml`

## 🎨 功能特性

### 1. 數字人生成

- **支持的分辨率**: 720p, 1080p, 4K, 8K
- **幀率**: 30/60/120 FPS
- **特性**:
  - 真實眨眼動畫
  - 微表情生成
  - 呼吸動畫
  - 唇形精確同步

### 2. 聲音克隆

- **參考音頻長度**: 30秒 - 10分鐘
- **支持語言**: 中文、英文、日文、韓文
- **情感控制**: 中性、開心、悲傷、生氣、興奮
- **韻律調整**: 速度、音高、能量

### 3. 照片轉視頻

- 全身動畫生成
- 物理模擬
- 深度感知
- 光照適應

### 4. 視頻增強

- 8K超分辨率
- 面部修復
- 降噪穩定
- 色彩調整

### 5. 新年特別功能

- 家庭拜年視頻自動生成
- 全家福批次處理
- 新年特效包
- 快速預覽模式

## 📊 性能目標

| 任務類型 | 輸入 | 目標時間 | 輸出質量 |
|---------|------|---------|----------|
| 數字人生成 | 30秒音頻 | 1分鐘 | 4K/60FPS |
| 聲音克隆 | 30秒參考+100字 | 10秒 | 22kHz |
| 照片動畫 | 單張照片 | 30秒 | 5秒視頻 |
| 完整製作 | 照片+聲音+特效 | 3-5分鐘 | 4K/60FPS |

## 🔧 監控和維護

### 查看系統狀態

```bash
# GPU使用情況
nvidia-smi -l 1

# 記憶體使用
free -h

# 服務日誌
tail -f logs/ultimate_system.log

# 系統狀態API
curl http://localhost:8000/api/status
```

### 常見問題

#### GPU記憶體不足

```bash
# 清理GPU緩存
python3 -c "import torch; torch.cuda.empty_cache()"

# 重啟服務
sudo systemctl restart ultimate-system
```

#### 服務無響應

```bash
# 檢查進程
ps aux | grep main_ultimate

# 查看錯誤日誌
tail -n 100 logs/ultimate_system.log

# 強制重啟
pkill -9 -f main_ultimate
python3 main_ultimate.py &
```

## 🔒 安全建議

1. **網絡隔離**: 建議僅在內網訪問
2. **用戶認證**: 生產環境應啟用身份驗證
3. **數據備份**: 定期備份工作區數據
4. **日誌輪轉**: 配置日誌自動清理
5. **資源限制**: 監控並限制用戶配額

## 📚 API文檔

啟動服務後訪問：
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

主要端點：
- `POST /api/digital-human/generate` - 生成數字人
- `POST /api/voice-clone/generate` - 克隆聲音
- `GET /api/status` - 系統狀態
- `GET /api/gpu-status` - GPU狀態
- `WS /ws/status` - 實時狀態更新

## 🎁 新年特別模式

啟用兒童友好模式：

1. 選擇用戶為 child1 或 child2
2. 系統自動切換到簡化界面
3. 提供預設模板
4. 快速模式（降低質量換取速度）

新年特效：
- 煙火動畫
- 春聯背景
- 新年音樂
- 祝福字幕

## 📞 技術支持

如需幫助，請：
1. 查看故障排除文檔: `docs/TROUBLESHOOTING_ULTIMATE.md`
2. 查看API文檔: `docs/API_REFERENCE_ULTIMATE.md`
3. 提交Issue到GitHub倉庫

---

**祝您使用愉快！過年快樂！🎊**
