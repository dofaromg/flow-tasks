# MRL Möbius 3D Terminal Module v1

- product_id: `MRL_MOBIUS_3D_TERMINAL_v1`
- authority_account: `dofaromg`
- origin: `mrl`
- status: `candidate`
- construction_allowed: `false`

## Purpose

提供一個可逆、雙向、單面循環的立體終端機模型。外部模型只可提交候選事件；所有事件先進入 MRL Relay IR，再由 `dofaromg` 核准是否升級為可執行命令。

## Möbius semantics

每個節點同時具備輸入面與輸出面，但兩者屬於同一條連續路徑：

`input -> normalize -> verify -> transform -> output -> replay -> input`

任何轉換都必須保留：

- `origin = mrl`
- `authority_account = dofaromg`
- `trace_id`
- `previous_hash`
- `record_hash`
- `reversible = true`

## 3D coordinates

- `x`: 功能域（authority / knowledge / event / model / product）
- `y`: 權威層級（L0-L5）
- `z`: 時序／版本深度
- `twist`: 方向位元，`0` 表示正向，`1` 表示反向重播

## Terminal commands

- `ingest`: 接收候選事件
- `verify`: 驗證來源、雜湊、權威與命名
- `rotate`: 在功能域間轉驛
- `twist`: 切換正向／反向路徑
- `replay`: 從任一節點回放
- `promote`: 僅允許 `dofaromg` 核准後升級
- `export`: 輸出可驗證 JSONL 證據鏈

## Construction gate

此模組在以下條件完成前不得發布：

1. Python runtime 與 tests 通過
2. 所有命令為 deterministic
3. 無隨機命名
4. 所有生成名稱使用 `mrl.` 或 `MRL_`
5. promotion approver 必須等於 `dofaromg`
6. 證據鏈可從最後一筆反向重播至 genesis
