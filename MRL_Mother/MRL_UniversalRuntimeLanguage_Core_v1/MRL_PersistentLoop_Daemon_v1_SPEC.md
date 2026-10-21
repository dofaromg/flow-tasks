# MRL_PersistentLoop_Daemon_v1 — 規格（SPEC，尚未實作）

origin_signature: `MrLiouWord`
狀態：**準備中 / 規格**。本檔僅定義介面與驗收，**尚未實作**，不得宣稱完成。
範圍紀律：下一增量**只做這一件事**；不接 live BaseWorld DB、不改遠端 schema、不宣稱 DL580 stable。

---

## 1. 目標

在既有 `MRL_Runtime/MRL_PersistentLoop.py` 之上，建立可驗證的常駐循環生命週期：

```
disk checkpoint → restart → replay → restore → verification → runtime structurefield reload
```

**對接既有命名，不得產生平行命名（v2 canonical）**：
- 復用 `MRL_PersistentLoop`（checkpoint 落盤 + 重啟存活），不另造第二套 loop。
- 復用 `MRL_ReplayRestore_Core`（exact replay / restore）。
- 復用 `MRL_Verification`（六項驗收 token）。
- 復用 `MRL_RuntimeStructureField`（StructureField 重建/重載；`MRL_RuntimeGraph` 為歷史 alias）。
- 新增物件名：`MRL_PersistentLoop_Daemon_v1`（單一真實來源）。

---

## 2. 生命週期（六階段，皆須可驗證）

| 階段 | 行為 | 復用 |
|---|---|---|
| 1. disk checkpoint | 每步將 `{iteration, structurefield_hash, mrliouir_hash, replay_cursor}` 落盤 | `MRL_PersistentLoop._persist` |
| 2. restart | 新 daemon 實例自磁碟載入最新 checkpoint（模擬 crash 後重啟） | `MRL_PersistentLoop._load` |
| 3. replay | 由 checkpoint 的 `replay_cursor` 起，重播事件序 | `MRL_ReplayRestore_Core.replay` |
| 4. restore | 折疊回 checkpoint 當下 state，續播至尾 | `MRL_ReplayRestore_Core.restore` |
| 5. verification | 重啟後 state hash == 重啟前 state hash（exact） | `MRL_Verification.verify` |
| 6. structurefield reload | 由 checkpoint 的 `structurefield_hash` 重建 RuntimeStructureField 並比對 hash 相等 | `MRL_RuntimeStructureField.build` |

---

## 3. 提議介面（proposed API，待實作確認）

```python
class MRL_PersistentLoop_Daemon_v1:
    def __init__(self, runtime_dir: str, loop_id: str = "daemon"): ...
    def boot(self, mrliouir: dict) -> dict:      # 首次啟動：建 StructureField + replay_structurefield，落盤
    def tick(self) -> dict:                      # 前進一步 + checkpoint
    def crash_and_restart(self) -> "MRL_PersistentLoop_Daemon_v1":  # 回傳自磁碟接續之新實例
    def recover(self) -> dict:                   # replay → restore → verification → structurefield reload
    def acceptance(self) -> dict:                # 回傳六階段逐項 PASS/FAIL + token
```

checkpoint 格式（擴充既有 `persistent_loop_<id>.json`，不破壞相容）：
```json
{
  "loop_id": "...", "iteration": N, "history": [...],
  "replay_cursor": N, "structurefield_hash": "...", "mrliouir_hash": "...",
  "origin_signature": "MrLiouWord"
}
```

---

## 4. 驗收標準（acceptance，全須實跑）

- `recover()` 後：`state_hash_before == state_hash_after`（exact）。
- `crash_and_restart()` 後 `iteration` 與崩潰前相等（不丟步）。
- structurefield reload 後 `structurefield_hash` 與崩潰前相等。
- 連續 N 次 crash/restart 後仍收斂同一最終 state hash（冪等 recover）。
- 全通過輸出 `MRL_PERSISTENT_LOOP_DAEMON_ACCEPTANCE_PASS`。

交付物（規劃）：
- `MRL_Runtime/MRL_PersistentLoop_Daemon_v1.py`
- `acceptance/MRL_PersistentLoop_Daemon_Acceptance.py`（stdlib）
- `tests/test_MRL_persistent_loop_daemon.py`（pytest，供 CI）

---

## 5. 非目標（NON-goals，本增量不做）

- ❌ OS 服務註冊（systemd / Windows service）——本增量為 in-process daemon 模型。
- ❌ live `MRL_BaseWorld_DB_v1` 連線 / 遠端 schema 變更。
- ❌ 宣稱 DL580 stable（未於 DL580 實跑前不得宣稱）。
- ❌ 任何 §4 之外的新方向。

---

## 6. 開工前置（待 MrLiou 複查 PR #35 後）

1. PR #35（P0 核心）CI 綠且經複查。
2. 確認本增量落點（branch / PR）。
3. 依本 SPEC 實作 → 實跑 acceptance → 回填結果，**不擴散其他模組**。

origin_signature: `MrLiouWord`
