# FlowAgent 測試套件 / FlowAgent Test Suite

此目錄包含 FlowAgent 專案的所有單元測試與整合測試。
This directory contains all unit and integration tests for the FlowAgent project.

## 測試結構 / Test Structure

```
tests/
├── __init__.py                 # 測試包初始化
├── test_particle_unit.py       # 粒子執行單元測試
└── README.md                   # 本文檔
```

## 快速開始 / Quick Start

### 執行所有測試 / Run All Tests

```bash
# 在專案根目錄執行 / Run from project root
python -m pytest tests/ -v

# 或使用簡短命令 / Or use short command
pytest tests/
```

### 執行特定測試 / Run Specific Tests

```bash
# 執行粒子單元測試 / Run particle unit tests
pytest tests/test_particle_unit.py -v

# 執行特定測試類別 / Run specific test class
pytest tests/test_particle_unit.py::TestParticleExecutionUnit -v

# 執行特定測試方法 / Run specific test method
pytest tests/test_particle_unit.py::TestParticleExecutionUnit::test_particle_unit_initialization -v
```

### 使用測試標記 / Using Test Markers

```bash
# 只執行單元測試 / Run only unit tests
pytest -m unit

# 只執行整合測試 / Run only integration tests
pytest -m integration

# 執行粒子系統測試 / Run particle system tests
pytest -m particle

# 執行記憶系統測試 / Run memory system tests
pytest -m memory

# 排除慢速測試 / Exclude slow tests
pytest -m "not slow"

# 組合標記 / Combine markers
pytest -m "unit and particle"
```

### 詳細輸出選項 / Verbose Output Options

```bash
# 詳細輸出 / Verbose output
pytest tests/ -v

# 顯示 print 輸出 / Show print statements
pytest tests/ -s

# 簡短的錯誤追蹤 / Short traceback
pytest tests/ --tb=short

# 完整的錯誤追蹤 / Full traceback
pytest tests/ --tb=long

# 只顯示失敗的測試 / Show only failed tests
pytest tests/ -v --failed-first
```

### 測試覆蓋率 / Test Coverage

```bash
# 執行測試並生成覆蓋率報告 / Run tests with coverage report
pytest tests/ --cov=core --cov=particle_core --cov-report=html

# 查看覆蓋率報告 / View coverage report
# 在瀏覽器打開 htmlcov/index.html
```

## 測試說明 / Test Descriptions

### test_particle_unit.py - 粒子執行單元測試

測試粒子語言核心系統的基本功能：
Tests basic functionality of the Particle Language core system:

#### TestParticleExecutionUnit 類別

1. **test_particle_unit_initialization** - 粒子執行單元初始化
   - 驗證記憶核心與粒子字典的初始化
   - Verifies initialization of memory core and particle dictionary

2. **test_particle_registration** - 粒子註冊功能
   - 測試粒子的註冊與檢索
   - Tests particle registration and retrieval

3. **test_memory_commit** - 記憶提交功能
   - 測試記憶系統的提交與查詢
   - Tests memory system commit and query

4. **test_particle_chain_creation** - 粒子鏈創建
   - 測試粒子鏈的創建與管理
   - Tests particle chain creation and management

5. **test_particle_execution_lifecycle** - 粒子執行生命週期
   - 測試完整的粒子執行流程
   - Tests complete particle execution flow

6. **test_memory_types** - 多種記憶類型
   - 測試所有記憶類型的支援
   - Tests support for all memory types

#### TestParticleIntegration 類別

7. **test_particle_memory_integration** - 粒子與記憶系統整合
   - 測試粒子系統與記憶系統的整合
   - Tests integration between particle and memory systems

## 測試標記 / Test Markers

本專案使用以下測試標記：
This project uses the following test markers:

| 標記 / Marker | 說明 / Description |
|---------------|-------------------|
| `unit` | 單元測試 / Unit tests |
| `integration` | 整合測試 / Integration tests |
| `slow` | 慢速測試 / Slow tests |
| `particle` | 粒子系統相關 / Particle system related |
| `memory` | 記憶系統相關 / Memory system related |
| `core` | 核心模組測試 / Core module tests |
| `api` | API 相關測試 / API related tests |
| `e2e` | 端對端測試 / End-to-end tests |

標記在 `pytest.ini` 中定義。
Markers are defined in `pytest.ini`.

## 測試最佳實踐 / Testing Best Practices

### 1. 測試獨立性 / Test Independence
每個測試應該獨立運行，不依賴其他測試的執行順序或結果。
Each test should run independently without depending on the execution order or results of other tests.

### 2. 清晰的測試命名 / Clear Test Naming
測試方法應該有清晰的名稱，描述測試的內容。
Test methods should have clear names describing what is being tested.

```python
# 好的命名 / Good naming
def test_particle_initialization():
    ...

# 不好的命名 / Bad naming
def test1():
    ...
```

### 3. 使用 setup/teardown / Use setup/teardown
使用 `setup_method` 和 `teardown_method` 來管理測試狀態。
Use `setup_method` and `teardown_method` to manage test state.

```python
def setup_method(self):
    """在每個測試前執行 / Runs before each test"""
    self.memory_core = FlowMemoryCore()

def teardown_method(self):
    """在每個測試後執行 / Runs after each test"""
    self.memory_core = None
```

### 4. 使用斷言訊息 / Use Assertion Messages
為斷言添加有意義的訊息，幫助調試。
Add meaningful messages to assertions to help with debugging.

```python
assert result is not None, "記憶提交應返回結果"
```

### 5. 組織測試 / Organize Tests
將相關的測試組織在同一個類別中。
Group related tests in the same class.

## 持續整合 / Continuous Integration

測試會在以下情況自動執行：
Tests are automatically run in the following scenarios:

- Pull Request 創建時 / When creating a Pull Request
- 代碼推送到主分支時 / When pushing code to main branch
- 每日排程執行 / Daily scheduled runs

## 貢獻測試 / Contributing Tests

### 添加新測試 / Adding New Tests

1. 在 `tests/` 目錄下創建新的測試檔案
   Create a new test file in the `tests/` directory

2. 檔案名稱必須以 `test_` 開頭
   File name must start with `test_`

3. 測試類別名稱以 `Test` 開頭
   Test class names should start with `Test`

4. 測試方法名稱以 `test_` 開頭
   Test method names should start with `test_`

5. 添加適當的測試標記
   Add appropriate test markers

6. 添加清晰的文檔字符串
   Add clear docstrings

### 範例 / Example

```python
import pytest

class TestNewFeature:
    """測試新功能 / Test new feature"""
    
    def setup_method(self):
        """設置測試 / Setup test"""
        pass
    
    @pytest.mark.unit
    @pytest.mark.particle
    def test_new_functionality(self):
        """
        測試新功能
        Test new functionality
        """
        # 測試代碼 / Test code
        assert True, "測試訊息"
```

## 故障排除 / Troubleshooting

### 測試失敗 / Test Failures

如果測試失敗，請檢查：
If tests fail, check:

1. 依賴是否已安裝 / Dependencies are installed
   ```bash
   pip install -r requirements.txt
   ```

2. 路徑是否正確 / Paths are correct
   ```bash
   cd /home/runner/work/flow-tasks/flow-tasks
   pytest tests/
   ```

3. Python 版本 / Python version
   ```bash
   python --version  # 應該是 3.10+
   ```

### 導入錯誤 / Import Errors

如果遇到導入錯誤：
If you encounter import errors:

```bash
# 確保在專案根目錄 / Ensure in project root
export PYTHONPATH=/home/runner/work/flow-tasks/flow-tasks:$PYTHONPATH
```

## 相關文檔 / Related Documentation

- [核心模組 README](../core/README.md)
- [粒子語言核心 README](../particle_core/README.md)
- [專案 README](../README.md)
- [架構文檔](../ARCHITECTURE.md)

---

**最後更新 / Last Updated**: 2026-02-05  
**維護者 / Maintainer**: FlowAgent Team
