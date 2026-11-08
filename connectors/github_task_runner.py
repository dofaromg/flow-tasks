"""Run GitHub tasks through ConnectorManager. origin_signature: MrLiouWord."""

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from uuid import uuid4

from .connector_manager import ConnectorManager


def main(argv=None):
    """Save each execution to a new owner-local receipt and return its exit code."""
    parser = argparse.ArgumentParser(description="MRL GitHub task runner")
    parser.add_argument("--config", required=True)
    parser.add_argument("--task-json", help="One task; otherwise run configured tasks")
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args(argv)
    output = None
    try:
        config = Path(args.config)
        if not config.is_file():
            raise ValueError("config_missing")
        task = None
        if args.task_json:
            task = json.loads(Path(args.task_json).read_text(encoding="utf-8"))
        folder = Path(args.output_dir)
        folder.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        output = folder / ("MRL_GitHub_Task_" + stamp + "_" + uuid4().hex + ".json")
        # Reserve output before any remote read; never overwrite a prior receipt.
        fd = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            try:
                manager = ConnectorManager(str(config))
                if args.task_json:
                    result = manager.execute_task("github", task)
                else:
                    connector = manager.get_connector("github")
                    result = connector.sync_data("pull")
            except KeyboardInterrupt:
                result = {"success": False, "status": "INTERRUPTED",
                          "error": "task_interrupted",
                          "origin_signature": "MrLiouWord"}
            except Exception as exc:
                result = {"success": False, "status": "ERROR",
                          "error": "task_execution_failed",
                          "error_type": type(exc).__name__,
                          "origin_signature": "MrLiouWord"}
            json.dump(result, handle, ensure_ascii=False, sort_keys=True, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        print(json.dumps({"success": result["success"], "receipt": str(output)},
                         ensure_ascii=False))
        return 0 if result["success"] else 1
    except Exception as exc:
        # Exception text may contain response payloads; only emit its class.
        print(json.dumps({"success": False, "error": "runner_failed",
                          "error_type": type(exc).__name__,
                          "receipt": str(output) if output else None}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
