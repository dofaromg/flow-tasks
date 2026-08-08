# MRL_MotherGrowthLoop_v1｜母體吸收成長閉環

位置：`particle_core/src/mother_growth_loop.py`

正式系統名稱固定為 `MRL_MotherGrowthLoop_v1`。`MotherGrowthLoop` 與
`mother_growth_loop.py` 僅保留為 DL580 舊排程的相容入口，不再作為產品名稱。

## 閉環

`ConversationExtractor.process_external_analysis_pipeline()`
→ `views.memory_seed`
→ 驗證
→ 不可變版本 Seed
→ active 指標
→ append-only journal
→ MQM 相容 Seed export
→ `prepare_next_task()`

## 保證

- 相同內容不重複升版。
- 內容變更才建立新版本。
- 舊版本不刪除、不覆寫。
- 每版具有重新計算驗證的 SHA-256、parent version/hash 與差異摘要。
- active pointer 的路徑、版本、Seed identity、內容 hash 與 journal event 必須完全一致才可讀取。
- journal 事件具有前後 hash 鏈。
- 每一個版本必須存在對應 journal 事件；版本缺號、錯誤命名與孤兒版本都會驗證失敗。
- rollback 只切換 active 指標、不刪除新版，並同步重建 MQM export。
- 下一次任務只讀取通過 hash 驗證的 active Seed。
- 每次吸收後自動輸出 `exports/<seed>.mqm.json`，可直接加入 MQM 的 `seeds` 配置。
- 異常終止留下的 dead-PID lock 會安全回收；仍在執行的程序不會被強制解鎖。
- Seed ID 採大小寫不敏感 canonical 規則；非安全字元與超長 ID 使用 hash 後綴隔離，避免 Windows 路徑碰撞。

## PowerShell（DL580）

```powershell
.\run_mother_growth_loop.ps1 -Source "D:\input\conversation.json" -SeedId "mrl-core" -Storage "D:\MRL_Mother\memory"

# 僅驗證，不吸收
.\run_mother_growth_loop.ps1 -Action Verify -SeedId "mrl-core"

# 回滾 active 並同步刷新 MQM export
.\run_mother_growth_loop.ps1 -Action Rollback -SeedId "mrl-core" -TargetVersion 1
```

每次 PowerShell 執行都會在 `D:\MRL_Mother\evidence` 保存主機、Python runtime、動作、時間、exit code 與完整驗證輸出，作為 DL580 實機證據。

## Python API

```python
from conversation_extractor import ConversationExtractor
from mother_growth_loop import MRL_MotherGrowthLoop_v1

loop = MRL_MotherGrowthLoop_v1("D:/MRL_Mother/memory")
result = loop.process_and_absorb(
    ConversationExtractor(),
    "D:/input/conversation.json",
    seed_id="mrl-core",
)
assert loop.verify_store("mrl-core")["status"] == "PASS"

next_task = loop.prepare_next_task({"task_id": "next"}, ["mrl-core"])
```

## 接入既有 MQM

```yaml
context_dir: D:/MRL_Mother/context
snapshot_dir: D:/MRL_Mother/snapshots
seeds:
  - D:/MRL_Mother/memory/exports/mrl-core.mqm.json
```

## 驗證

```powershell
python -m unittest particle_core/test_mother_growth_loop.py
```

驗證範圍包含：版本內容 hash、版本檔 identity、parent version/hash、active pointer、journal hash chain、版本事件覆蓋及 MQM rollback 同步。
