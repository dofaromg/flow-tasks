# Mrliou 母體吸收成長閉環

位置：`particle_core/src/mother_growth_loop.py`

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
- 每版具有 SHA-256、parent hash 與差異摘要。
- journal 事件具有前後 hash 鏈。
- rollback 只切換 active 指標，不刪除新版。
- 下一次任務只讀取通過 hash 驗證的 active Seed。
- 每次吸收後自動輸出 `exports/<seed>.mqm.json`，可直接加入 MQM 的 `seeds` 配置。

## PowerShell（DL580）

```powershell
.\run_mother_growth_loop.ps1 -Source "D:\input\conversation.json" -SeedId "mrl-core" -Storage "D:\MRL_Mother\memory"
```

## Python API

```python
from conversation_extractor import ConversationExtractor
from mother_growth_loop import MotherGrowthLoop

loop = MotherGrowthLoop("D:/MRL_Mother/memory")
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
