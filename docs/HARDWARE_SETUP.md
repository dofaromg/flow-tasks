# Hardware Setup Guide - Ultimate AI Video System
# 硬體配置指南

## 🖥️ 系統要求

### 最低配置（可運行但性能受限）

- **GPU**: 1x NVIDIA RTX 3090 (24GB)
- **RAM**: 64GB
- **CPU**: Intel i9 / AMD Ryzen 9
- **Storage**: 500GB SSD
- **Network**: 1Gbps

### 推薦配置（良好性能）

- **GPU**: 2x NVIDIA A100 (40GB each) 或 4x RTX 4090
- **RAM**: 256GB
- **CPU**: 2x Intel Xeon / AMD EPYC (32+ cores each)
- **Storage**: 2TB NVMe SSD
- **Network**: 10Gbps

### 極致配置（本系統設計目標）

- **GPU**: 6x NVIDIA V100 (32GB each) = 192GB GPU Memory
- **RAM**: 3TB DDR4 ECC
- **CPU**: 4x Intel Xeon Platinum / AMD EPYC (128+ cores total)
- **Storage**: 10TB+ NVMe SSD RAID
- **Network**: 10Gbps+ internal, bonded interfaces

## 🎮 GPU 配置

### V100 GPU 規格

```
NVIDIA Tesla V100 32GB
- CUDA Cores: 5120
- Tensor Cores: 640
- Memory: 32GB HBM2
- Memory Bandwidth: 900 GB/s
- FP32 Performance: 15.7 TFLOPS
- FP16 Performance: 125 TFLOPS (with Tensor Cores)
```

### GPU 拓撲配置

理想的6-GPU配置：

```
PCIe Layout:
├── CPU Socket 0
│   ├── GPU 0 (x16 PCIe 3.0/4.0)
│   └── GPU 1 (x16 PCIe 3.0/4.0)
├── CPU Socket 1
│   ├── GPU 2 (x16 PCIe 3.0/4.0)
│   └── GPU 3 (x16 PCIe 3.0/4.0)
├── CPU Socket 2
│   ├── GPU 4 (x16 PCIe 3.0/4.0)
│   └── GPU 5 (x16 PCIe 3.0/4.0)
```

### GPU 分配策略

本系統的GPU分配：

```yaml
GPU 0-1: 數字人生成引擎
  - 需要大量VRAM用於模型加載
  - 雙GPU並行加速
  - DataParallel模式
  
GPU 2: 聲音克隆引擎
  - 中等VRAM需求
  - 快速推理
  
GPU 3: 照片轉視頻 + 動作遷移
  - 高VRAM需求
  - 序列生成
  
GPU 4: 視頻增強 + 換臉
  - 高帶寬需求
  - 批次處理
  
GPU 5: 輔助功能
  - 3D建模、音樂生成、特效
  - 彈性分配
```

### NVIDIA 驅動安裝

```bash
# Ubuntu 22.04
# 1. 添加NVIDIA倉庫
sudo add-apt-repository ppa:graphics-drivers/ppa
sudo apt update

# 2. 安裝驅動（推薦525或更新）
sudo apt install nvidia-driver-525

# 3. 重啟
sudo reboot

# 4. 驗證
nvidia-smi
```

### CUDA 安裝

```bash
# 安裝CUDA 11.8
wget https://developer.download.nvidia.com/compute/cuda/11.8.0/local_installers/cuda_11.8.0_520.61.05_linux.run
sudo sh cuda_11.8.0_520.61.05_linux.run

# 設置環境變量
echo 'export PATH=/usr/local/cuda-11.8/bin:$PATH' >> ~/.bashrc
echo 'export LD_LIBRARY_PATH=/usr/local/cuda-11.8/lib64:$LD_LIBRARY_PATH' >> ~/.bashrc
source ~/.bashrc

# 驗證
nvcc --version
```

### cuDNN 安裝

```bash
# 下載cuDNN 8.9（需要NVIDIA Developer賬號）
# 從 https://developer.nvidia.com/cudnn 下載

# 解壓並安裝
tar -xzvf cudnn-linux-x86_64-8.9.x.x_cuda11-archive.tar.xz
sudo cp cudnn-*-archive/include/cudnn*.h /usr/local/cuda/include 
sudo cp -P cudnn-*-archive/lib/libcudnn* /usr/local/cuda/lib64 
sudo chmod a+r /usr/local/cuda/include/cudnn*.h /usr/local/cuda/lib64/libcudnn*
```

## 💾 記憶體配置

### 3TB RAM 配置建議

```
推薦配置：
- 24x 128GB DDR4 ECC RDIMM @ 3200MHz
- 分布在4個CPU Socket
- 每個Socket 6個通道
- 總帶寬：~750 GB/s

或：
- 12x 256GB DDR4 LR-DIMM @ 2933MHz
- 更高密度但頻率略低
```

### 記憶體分配策略

```
總記憶體：3TB (3072GB)
├── 系統保留：200GB (6.5%)
├── AI模型緩存：180GB (5.9%)
│   ├── 數字人模型：~40GB
│   ├── 聲音克隆模型：~30GB
│   ├── 視頻增強模型：~25GB
│   ├── 其他模型：~85GB
├── 任務處理緩存：1TB (33%)
├── 用戶工作區：500GB (16%)
└── 系統可用：1.2TB (39%)
```

### BIOS 設置

```
重要設置：
1. 啟用 ECC Memory
2. 設置 NUMA Mode = Enabled
3. 設置 Memory Frequency = Maximum
4. 啟用 XMP Profile（如果支持）
5. 設置 Memory Interleaving = Auto
```

## 💽 存儲配置

### 推薦存儲方案

```
方案一：高性能RAID
├── 4x 4TB NVMe SSD
├── RAID 10配置
├── 總容量：8TB可用
└── 讀寫速度：~10GB/s

方案二：超大容量
├── 8x 2TB NVMe SSD
├── RAID 5配置
├── 總容量：14TB可用
└── 讀寫速度：~8GB/s

方案三：混合配置（推薦）
├── 2x 2TB NVMe SSD (系統和模型) - RAID 1
├── 6x 2TB NVMe SSD (工作區) - RAID 10
└── 總容量：8TB可用，速度和容量平衡
```

### 目錄結構和掛載

```bash
# 推薦掛載方案
/dev/nvme0n1 → /              # 系統盤
/dev/md0     → /models        # 模型存儲 RAID 1
/dev/md1     → /workspaces    # 工作區 RAID 10
/dev/md2     → /shared        # 共享資源 RAID 10
```

### 文件系統優化

```bash
# 使用ext4或xfs
sudo mkfs.ext4 -T largefile4 -O sparse_super2,extent /dev/md0
sudo mkfs.xfs -i size=512 -n size=8192 /dev/md1

# fstab優化掛載選項
/dev/md0 /models      ext4 defaults,noatime,nodiratime 0 2
/dev/md1 /workspaces  xfs  defaults,noatime,nodiratime 0 2
```

## 🌐 網絡配置

### 網卡配置

```
推薦配置：
- 2x 10GbE NIC（網卡綁定）
- 或 1x 25GbE / 40GbE NIC
- 支持RDMA（如果使用分佈式訓練）
```

### 網絡綁定（Bonding）

```bash
# 安裝ifenslave
sudo apt install ifenslave

# 配置bonding
sudo nano /etc/netplan/01-netcfg.yaml

# 內容：
network:
  version: 2
  ethernets:
    enp1s0:
      dhcp4: no
    enp2s0:
      dhcp4: no
  bonds:
    bond0:
      interfaces: [enp1s0, enp2s0]
      addresses: [192.168.1.100/24]
      gateway4: 192.168.1.1
      nameservers:
        addresses: [8.8.8.8, 8.8.4.4]
      parameters:
        mode: 802.3ad  # LACP
        mii-monitor-interval: 100
        lacp-rate: fast

# 應用配置
sudo netplan apply
```

## 🔋 電源和散熱

### 電源要求

```
計算：
- 6x V100 GPU: 6 × 300W = 1800W
- 4x CPU (150W each): 600W
- 記憶體 (3TB): ~200W
- 存儲和其他: ~200W
- 總計：~2800W

推薦配置：
- 2x 2000W Platinum/Titanium PSU（冗餘）
- 或 3x 1600W PSU
- UPS: 5000VA以上
```

### 散熱要求

```
散熱需求：
- GPU散熱：水冷或高端風冷
- CPU散熱：水冷（推薦）
- 機箱風扇：至少8個120mm或更大
- 環境溫度：建議 < 25°C
- 機房散熱：空調制冷，功率至少5kW
```

## 🔧 系統優化

### BIOS設置

```
性能設置：
1. Turbo Boost: Enabled
2. Hyper-Threading: Enabled
3. C-States: Disabled（最大性能）
4. PCIe Max Link Speed: Gen 4.0
5. IOMMU: Enabled（虛擬化）
6. Power Profile: Maximum Performance
```

### Linux內核參數

```bash
# /etc/sysctl.conf
# 網絡優化
net.core.rmem_max = 134217728
net.core.wmem_max = 134217728
net.ipv4.tcp_rmem = 4096 87380 67108864
net.ipv4.tcp_wmem = 4096 65536 67108864

# 文件系統
fs.file-max = 2097152
vm.swappiness = 10

# 應用設置
sudo sysctl -p
```

### GPU性能模式

```bash
# 設置所有GPU為最大性能模式
sudo nvidia-smi -pm 1
sudo nvidia-smi --auto-boost-default=0
for i in {0..5}; do
    sudo nvidia-smi -i $i -pl 300  # 設置功率限制為300W
done

# 驗證
nvidia-smi -q -d PERFORMANCE
```

## 📊 性能基準測試

### GPU測試

```bash
# CUDA測試
cd /usr/local/cuda/samples/1_Utilities/deviceQuery
sudo make
./deviceQuery

# 性能測試
cd /usr/local/cuda/samples/1_Utilities/bandwidthTest
sudo make
./bandwidthTest
```

### 記憶體測試

```bash
# 安裝測試工具
sudo apt install sysbench

# 記憶體帶寬測試
sysbench memory --memory-total-size=100G run
```

### 存儲測試

```bash
# 安裝fio
sudo apt install fio

# 順序讀寫測試
fio --name=seqread --rw=read --bs=1M --size=10G --numjobs=4 --runtime=60
fio --name=seqwrite --rw=write --bs=1M --size=10G --numjobs=4 --runtime=60

# 隨機讀寫測試
fio --name=randread --rw=randread --bs=4K --size=10G --numjobs=4 --runtime=60
fio --name=randwrite --rw=randwrite --bs=4K --size=10G --numjobs=4 --runtime=60
```

## 🔐 安全建議

1. **物理安全**：服務器放置在安全的機房
2. **網絡隔離**：使用防火牆隔離內外網
3. **訪問控制**：僅允許家庭網絡訪問
4. **數據備份**：定期備份到外部存儲
5. **監控告警**：配置溫度、功耗監控

## 📞 故障排除

### GPU無法識別

```bash
# 檢查PCIe
lspci | grep -i nvidia

# 重裝驅動
sudo apt purge nvidia-*
sudo apt install nvidia-driver-525
sudo reboot
```

### 記憶體錯誤

```bash
# 運行記憶體測試
sudo apt install memtest86+
# 重啟選擇memtest86+進行測試
```

### 溫度過高

```bash
# 檢查GPU溫度
nvidia-smi --query-gpu=temperature.gpu --format=csv

# 檢查CPU溫度
sensors

# 如果溫度持續>80°C，檢查：
1. 散熱器是否正常工作
2. 導熱膏是否需要更換
3. 機箱通風是否良好
```

---

**🎊 硬體配置完成後，即可開始部署系統！🎊**
