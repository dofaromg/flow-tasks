# FlowAgent Tasks

`tasks/` contains YAML task definitions and generated validation reports for FlowAgent-driven implementation work.

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
