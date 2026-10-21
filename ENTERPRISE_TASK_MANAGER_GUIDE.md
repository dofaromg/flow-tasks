# 企業級長時間作業管理系統指南

## Enterprise Long-Running Task Management System Guide

## 概述 / Overview

企業級長時間作業管理系統為 FlowAgent 提供完整的異步任務調度、執行、監控和管理能力，專為長時間運行的企業級操作而設計。

The Enterprise Long-Running Task Management System provides comprehensive asynchronous task scheduling, execution, monitoring, and management capabilities for FlowAgent, designed specifically for long-running enterprise operations.

## 核心特性 / Core Features

### 1. 異步任務執行 / Asynchronous Task Execution
- ✅ 多執行緒/多進程執行
- ✅ 非阻塞任務提交
- ✅ 並發任務處理
- ✅ 可配置工作執行緒數量

### 2. 任務隊列管理 / Task Queue Management
- ✅ 優先級隊列系統（CRITICAL > HIGH > NORMAL > LOW）
- ✅ 任務調度（立即、延遲、定期）
- ✅ 任務排隊與分發
- ✅ 負載均衡

### 3. 進度追蹤與監控 / Progress Tracking & Monitoring
- ✅ 實時狀態更新
- ✅ 進度百分比追蹤
- ✅ 執行時間記錄
- ✅ 指標收集與報告

### 4. 錯誤處理與重試 / Error Handling & Retry
- ✅ 自動重試機制
- ✅ 指數退避策略
- ✅ 錯誤日誌記錄
- ✅ 失敗任務隊列

### 5. 持久化存儲 / Persistent Storage
- ✅ 任務定義持久化
- ✅ 執行結果持久化
- ✅ 跨會話數據恢復
- ✅ JSON 格式存儲

### 6. 任務控制 / Task Control
- ✅ 任務取消
- ✅ 超時設置
- ✅ 任務元數據
- ✅ 任務生命週期管理

## 快速開始 / Quick Start

### 安裝 / Installation

```bash
# 已包含在 FlowAgent 系統中，無需額外安裝
# Already included in FlowAgent, no additional installation needed
```

### 基本使用 / Basic Usage

```python
from enterprise_task_manager import EnterpriseTaskManager, TaskPriority

# 創建任務管理器
manager = EnterpriseTaskManager(
    max_workers=4,           # 工作執行緒數
    storage_dir="task_storage",  # 存儲目錄
    use_processes=False      # 使用執行緒（True 則使用進程）
)

# 啟動管理器
manager.start()

# 提交任務
task_id = manager.submit_task(
    func=my_function,        # 要執行的函數
    arg1, arg2,              # 位置參數
    name="My Task",          # 任務名稱
    priority=TaskPriority.HIGH,  # 優先級
    max_retries=3,           # 最大重試次數
    timeout_seconds=300,     # 超時（秒）
    kwarg1=value1            # 關鍵字參數
)

# 查詢任務狀態
status = manager.get_task_status(task_id)
print(f"Task status: {status}")

# 獲取任務進度
progress = manager.get_task_progress(task_id)
print(f"Progress: {progress:.1%}")

# 獲取任務結果
result = manager.get_task_result(task_id)
print(f"Result: {result}")

# 查看指標
metrics = manager.get_metrics()
print(f"Metrics: {metrics}")

# 停止管理器
manager.stop()
```

## 使用範例 / Usage Examples

### 範例 1：數據處理任務 / Data Processing Task

```python
def process_large_dataset(data_path, chunk_size=1000):
    """處理大型數據集"""
    # 模擬數據處理
    import time
    results = []
    
    for i in range(10):
        # 處理數據塊
        time.sleep(0.5)
        results.append(f"Processed chunk {i}")
    
    return {
        "processed_chunks": len(results),
        "results": results
    }

# 提交任務
task_id = manager.submit_task(
    process_large_dataset,
    "/data/large_dataset.csv",
    chunk_size=500,
    name="Process Dataset",
    priority=TaskPriority.NORMAL,
    timeout_seconds=600
)
```

### 範例 2：批次任務提交 / Batch Task Submission

```python
# 批次提交多個任務
task_ids = []

for i in range(10):
    task_id = manager.submit_task(
        process_item,
        item_id=i,
        name=f"Process Item {i}",
        priority=TaskPriority.NORMAL if i < 5 else TaskPriority.LOW
    )
    task_ids.append(task_id)

# 監控所有任務
while True:
    all_done = True
    for task_id in task_ids:
        status = manager.get_task_status(task_id)
        if status not in ["completed", "failed"]:
            all_done = False
            break
    
    if all_done:
        break
    
    time.sleep(1)

# 收集結果
results = [manager.get_task_result(tid) for tid in task_ids]
```

### 範例 3：定期任務 / Scheduled Task

```python
from datetime import datetime, timedelta

# 調度未來執行的任務
future_time = datetime.now() + timedelta(hours=1)

task_id = manager.submit_task(
    send_report,
    report_type="daily",
    name="Daily Report",
    scheduled_for=future_time
)
```

### 範例 4：重試邏輯 / Retry Logic

```python
def unreliable_api_call(url):
    """可能失敗的 API 調用"""
    import random
    import requests
    
    if random.random() < 0.7:  # 70% 失敗率
        raise Exception("API temporary unavailable")
    
    return requests.get(url).json()

# 提交帶重試的任務
task_id = manager.submit_task(
    unreliable_api_call,
    "https://api.example.com/data",
    name="API Call with Retry",
    max_retries=5,  # 最多重試 5 次
    timeout_seconds=30
)
```

### 範例 5：進度監控 / Progress Monitoring

```python
import time

task_id = manager.submit_task(
    long_running_computation,
    name="Long Computation"
)

# 實時監控進度
while True:
    status = manager.get_task_status(task_id)
    progress = manager.get_task_progress(task_id)
    
    print(f"Status: {status}, Progress: {progress:.1%}")
    
    if status in ["completed", "failed", "cancelled"]:
        break
    
    time.sleep(2)

# 獲取最終結果
result = manager.get_task_result(task_id)
print(f"Final result: {result}")
```

## 任務狀態 / Task Status

任務可能處於以下狀態：

| 狀態 | 說明 |
|------|------|
| `pending` | 任務已創建但尚未排隊 |
| `queued` | 任務在隊列中等待執行 |
| `running` | 任務正在執行 |
| `completed` | 任務成功完成 |
| `failed` | 任務執行失敗 |
| `cancelled` | 任務被取消 |
| `retrying` | 任務失敗後正在重試 |

## 優先級系統 / Priority System

```python
from enterprise_task_manager import TaskPriority

TaskPriority.CRITICAL  # 最高優先級 (0)
TaskPriority.HIGH      # 高優先級 (1)
TaskPriority.NORMAL    # 普通優先級 (2) - 默認
TaskPriority.LOW       # 低優先級 (3)
```

## 指標與監控 / Metrics & Monitoring

```python
metrics = manager.get_metrics()

# 可用指標：
# - total_tasks: 總任務數
# - completed_tasks: 完成任務數
# - failed_tasks: 失敗任務數
# - cancelled_tasks: 取消任務數
# - active_tasks: 活躍任務數
# - total_execution_time: 總執行時間
# - average_execution_time: 平均執行時間
# - success_rate: 成功率 (0.0 - 1.0)
```

## 最佳實踐 / Best Practices

### 1. 工作執行緒配置
```python
# CPU 密集型任務
manager = EnterpriseTaskManager(
    max_workers=os.cpu_count(),
    use_processes=True  # 使用多進程
)

# I/O 密集型任務
manager = EnterpriseTaskManager(
    max_workers=os.cpu_count() * 2,
    use_processes=False  # 使用多執行緒
)
```

### 2. 錯誤處理
```python
# 為可能失敗的任務設置重試
task_id = manager.submit_task(
    risky_operation,
    max_retries=3,
    timeout_seconds=60
)

# 檢查錯誤
result = manager.get_task_result(task_id)
if result['status'] == 'failed':
    print(f"Error: {result['error']}")
```

### 3. 資源管理
```python
# 始終確保清理
try:
    manager.start()
    # ... 執行任務 ...
finally:
    manager.stop()
```

### 4. 任務隔離
```python
# 將長時間任務與快速任務分開
quick_manager = EnterpriseTaskManager(max_workers=10)
long_manager = EnterpriseTaskManager(max_workers=2)
```

### 5. 監控與日誌
```python
import logging

# 啟用詳細日誌
logging.basicConfig(level=logging.INFO)

# 定期檢查指標
import threading

def monitor_metrics():
    while True:
        metrics = manager.get_metrics()
        if metrics['failed_tasks'] > 10:
            logging.warning("High failure rate detected!")
        time.sleep(60)

monitor_thread = threading.Thread(target=monitor_metrics, daemon=True)
monitor_thread.start()
```

## 性能考量 / Performance Considerations

### 執行緒 vs 進程
- **執行緒**（`use_processes=False`）：
  - 適用於 I/O 密集型任務
  - 較低的記憶體開銷
  - 共享記憶體空間
  
- **進程**（`use_processes=True`）：
  - 適用於 CPU 密集型任務
  - 真正的並行處理
  - 獨立記憶體空間

### 工作執行緒數量
```python
# 公式：max_workers = cpu_count * multiplier
# - CPU 密集型：multiplier = 1
# - I/O 密集型：multiplier = 2-4
# - 混合型：multiplier = 1.5-2

import os
max_workers = os.cpu_count() * 2
```

### 超時設置
```python
# 根據任務類型設置合理的超時
task_id = manager.submit_task(
    quick_task,
    timeout_seconds=30  # 快速任務
)

task_id = manager.submit_task(
    long_task,
    timeout_seconds=3600  # 長時間任務（1小時）
)
```

## 整合範例 / Integration Examples

### 與 Particle Core 整合
```python
from enterprise_task_manager import EnterpriseTaskManager
from particle_core.src.logic_pipeline import LogicPipeline

manager = EnterpriseTaskManager(max_workers=4)
manager.start()

# 異步執行邏輯管線
pipeline = LogicPipeline(enable_cache=True)

task_id = manager.submit_task(
    pipeline.batch_simulate,
    input_batch,
    parallel=True,
    name="Logic Pipeline Batch Processing"
)
```

### 與 AI SuperComputer 整合
```python
from MrLiou_AI_SuperComputer.fusion_strategies import adaptive_fusion

# 異步執行 AI 融合
task_id = manager.submit_task(
    adaptive_fusion,
    ai_outputs,
    name="AI Fusion Task",
    priority=TaskPriority.HIGH
)
```

## 故障排除 / Troubleshooting

### 任務卡住
```python
# 設置超時
task_id = manager.submit_task(
    func,
    timeout_seconds=300  # 5 分鐘超時
)
```

### 高失敗率
```python
# 增加重試次數和超時
task_id = manager.submit_task(
    func,
    max_retries=5,
    timeout_seconds=600
)
```

### 記憶體問題
```python
# 減少工作執行緒或使用進程模式
manager = EnterpriseTaskManager(
    max_workers=2,
    use_processes=True
)
```

## API 參考 / API Reference

### EnterpriseTaskManager

#### 初始化
```python
EnterpriseTaskManager(
    max_workers: int = 4,
    storage_dir: str = "task_storage",
    use_processes: bool = False
)
```

#### 方法
- `start()`: 啟動任務管理器
- `stop()`: 停止任務管理器
- `submit_task()`: 提交任務
- `get_task_status(task_id)`: 獲取任務狀態
- `get_task_result(task_id)`: 獲取任務結果
- `get_task_progress(task_id)`: 獲取任務進度
- `cancel_task(task_id)`: 取消任務
- `get_metrics()`: 獲取指標
- `get_all_tasks()`: 獲取所有任務

## 測試 / Testing

```bash
# 運行測試套件
python test_enterprise_task_manager.py
```

測試涵蓋：
- ✅ 基本任務提交
- ✅ 優先級隊列
- ✅ 任務重試
- ✅ 並發任務
- ✅ 任務超時
- ✅ 指標追蹤
- ✅ 任務持久化
- ✅ 長時間任務範例

## 許可證 / License

與 FlowAgent 主專案相同許可證

## 貢獻 / Contributing

歡迎提交 Issue 和 Pull Request！

## 相關文檔 / Related Documentation

- [Enhanced Computation Guide](./ENHANCED_COMPUTATION_GUIDE.md)
- [Particle Core README](./particle_core/README.md)
- [AI SuperComputer README](./MrLiou_AI_SuperComputer/README.md)
