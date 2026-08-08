# MrLiouAI Tasks

`tasks/` contains YAML task definitions and generated validation reports for MrLiouAI-driven implementation work.

## Purpose

Each dated YAML file describes one implementation target, language, expected files/directories, features, and validation hints. `process_tasks.py` loads these files and validates the repository state.

## Entry Points

- Task definitions: `tasks/YYYY-MM-DD_<task-id>.yaml`
- Processor: `process_tasks.py`
- Generated reports: `tasks/results/`

## Task Definition Contract

Required fields:

- `task_id`
- `language`
- `description`
- either `target_file` or `target_directory`

Recommended fields:

- `features`
- `components`
- `build`
- `endpoints`
- `architecture`

## Validate

```bash
python process_tasks.py
```

The processor checks task schema, target existence, Python syntax/imports, C compilation, frontend lint/build, Kubernetes overlay rendering, and secret-like candidates without printing secret values.


## 安全與歷史保留 / Safety and History

- Python 驗證只使用 AST 與 `py_compile`，不匯入或執行目標模組。
- 覆寫 JSON 報告前，原始內容會保存至 `tasks/results/history/<report>/`。
- 完整倉庫檢查預設啟用；需要只跑任務驗證時可明確停用。

```powershell
$env:FLOW_TASKS_REPOSITORY_CHECKS = "0"
python process_tasks.py
```

