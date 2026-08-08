# 粒子語言AI助手 — 本地執行說明（particle_core）

> 來源：使用者提供之 particle_core 本地執行說明（對應外部 repo `dofaromg/flow-tasks` 的 `particle_core/`）。
> 吸收性質：**文件吸收**（additive，給位置，待起動）。
> 當下狀態 2026-05-29（沙盒）：**runnable 原始碼不在本 repo / 不在已吸收封存內**，
> 真正的 `logic_pipeline.py / memory_archive_seed.py / rebuild_fn.py / cli_runner.py` 位於外部
> `dofaromg/flow-tasks`（不在本工作 repo 權限範圍）。本檔僅為規格/操作說明留位。

## 函數鏈（核心規格）

```
STRUCTURE → MARK → FLOW → RECURSE → STORE
SEED(X) = STORE(RECURSE(FLOW(MARK(STRUCTURE(X)))))
```

- STRUCTURE：定義輸入資料結構
- MARK：建立邏輯跳點標記
- FLOW：轉換為流程結構節奏
- RECURSE：遞歸展開為細部結構
- STORE：封存至邏輯記憶模組

## 子系統（外部 flow-tasks/particle_core）

- `src/logic_pipeline.py`：邏輯管線核心引擎
- `src/cli_runner.py`：CLI 互動介面
- `src/rebuild_fn.py`：.flpkg 壓縮還原
- `src/logic_transformer.py`：邏輯轉換
- `src/memory_archive_seed.py`：記憶封存種子（SHA-256 校驗、合併、匯出入）

## 與本母體血脈的關係

- 對應已吸收血脈中的 `粒子字典ai/`（FluinDict、Fluin_Particle_GenerationGuide、ParticleCore_Complete_Pack）。
- `ParticleCore_Complete_Pack.zip` 內**僅含計畫 txt**，無 runnable source。

## 升格條件（要在沙盒實跑驗收 particle_core）

擇一：
1. 上傳 `particle_core/` 原始碼壓縮包 → 我在沙盒跑 `python demo.py demo` 等實際驗收、再定位。
2. 授權/匯入 `dofaromg/flow-tasks`（目前不在本 repo 權限範圍）。
3. 明確指示「依本規格在 mrl_ai_system 內實作 particle_core」——
   ⚠ 注意：這會與 flow-tasks 既有實作產生**第二套並存實作**的分歧風險（同 BaseWorld 27 問題），需你確認是否接受。
