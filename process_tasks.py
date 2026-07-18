#!/usr/bin/env python3
"""
FlowAgent Task Processor.
Automatically receives, parses, validates, and reports code generation tasks.
"""

import html
import json
import os
import py_compile
import re
import shutil
import subprocess
import sys
import tempfile
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import yaml


class TaskProcessor:
    """Validate FlowAgent task definitions and repository health checks."""

    TASK_FILE_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}_.+\.yaml")
    REQUIRED_TASK_FIELDS = ("task_id", "language", "description")
    EXCLUDED_SCAN_DIRS = {
        ".git",
        ".next",
        ".pytest_cache",
        "__pycache__",
        "node_modules",
        "tasks/results",
    }
    TEXT_EXTENSIONS = {
        ".c",
        ".css",
        ".env",
        ".html",
        ".js",
        ".json",
        ".jsx",
        ".md",
        ".mjs",
        ".py",
        ".sh",
        ".toml",
        ".ts",
        ".tsx",
        ".txt",
        ".yaml",
        ".yml",
    }
    MAX_COMMAND_OUTPUT_EXCERPT_CHARS = 2000
    MAX_PYTHON_FILES_TO_CHECK = 200
    MAX_SCAN_FILE_SIZE_BYTES = 500_000
    SECRET_FILENAME_PATTERN = re.compile(
        r"(?i)(secret|credential|password|auth|oauth|private[-_ ]?key|token|apikey|api[-_ ]?key|personal[-_ ]?access[-_ ]?token)"
    )
    SECRET_CONTENT_PATTERNS = {
        "private_key_block": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
        "github_token": re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{20,}\b"),
        "aws_access_key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
        "generic_secret_assignment": re.compile(
            r"(?i)\b(password|passwd|secret|token|api[_-]?key)\b\s*[:=]\s*['\"]?[^'\"\s]{12,}"
        ),
    }

    def __init__(self, tasks_dir: str = "tasks"):
        self.root_dir = Path.cwd()
        self.tasks_dir = Path(tasks_dir)
        self.results_dir = self.tasks_dir / "results"
        self.results_dir.mkdir(exist_ok=True)

    @staticmethod
    def _is_task_definition(task_file: Path) -> bool:
        """Return True when the file matches the repository task naming pattern."""
        return bool(TaskProcessor.TASK_FILE_PATTERN.fullmatch(task_file.name))

    @staticmethod
    def _check(check: str, message: str, status: str = "passed") -> Dict[str, str]:
        return {"check": check, "status": status, "message": message}

    @staticmethod
    def _warning(warning_type: str, message: str) -> Dict[str, str]:
        return {"type": warning_type, "message": message, "severity": "warning"}

    @staticmethod
    def _error(error_type: str, message: str, traceback_text: Optional[str] = None) -> Dict[str, str]:
        error = {"type": error_type, "message": message, "severity": "error"}
        if traceback_text:
            error["traceback"] = traceback_text
        return error

    def load_task(self, task_file: str) -> Dict[str, Any]:
        """Load task definition from YAML file."""
        task_path = self.tasks_dir / task_file
        if not task_path.exists():
            raise FileNotFoundError(f"Task file not found: {task_path}")

        with open(task_path, "r", encoding="utf-8") as task_input:
            task = yaml.safe_load(task_input)
        if not isinstance(task, dict):
            raise ValueError(f"Task file must contain a YAML mapping: {task_path}")
        return task

    def _run_command(self, command: List[str], timeout: int = 120) -> Dict[str, Any]:
        """Run a command and return a compact result without leaking long output."""
        started_at = time.time()
        try:
            completed = subprocess.run(
                command,
                cwd=self.root_dir,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
            output = (completed.stdout + completed.stderr).strip()
            return {
                "returncode": completed.returncode,
                "duration_ms": round((time.time() - started_at) * 1000, 2),
                "output_excerpt": output[-self.MAX_COMMAND_OUTPUT_EXCERPT_CHARS:],
            }
        except subprocess.TimeoutExpired as timeout_error:
            return {
                "returncode": 124,
                "duration_ms": round((time.time() - started_at) * 1000, 2),
                "output_excerpt": f"Command timed out after {timeout_error.timeout}s",
            }

    def _validate_schema(self, task: Dict[str, Any], result: Dict[str, Any]) -> None:
        missing = [field for field in self.REQUIRED_TASK_FIELDS if not task.get(field)]
        if missing:
            result["errors"].append(
                self._error("schema", f"Missing required task field(s): {', '.join(missing)}")
            )
        else:
            result["checks"].append(
                self._check("schema", "Required task fields are present")
            )

        if not task.get("target_file") and not task.get("target_directory"):
            result["errors"].append(
                self._error("schema", "Task must define target_file or target_directory")
            )
        else:
            result["checks"].append(
                self._check("schema_target", "Task target is declared")
            )

    def _validate_python_file(self, target_path: Path, result: Dict[str, Any]) -> None:
        try:
            py_compile.compile(str(target_path), doraise=True)
            result["checks"].append(
                self._check("python_syntax", f"Python syntax check passed: {target_path}")
            )
        except py_compile.PyCompileError as compile_error:
            result["errors"].append(
                self._error("python_syntax", f"Python syntax check failed: {compile_error.msg}")
            )
            return

        try:
            import importlib.util

            module_spec = importlib.util.spec_from_file_location("task_module", target_path)
            if module_spec is None or module_spec.loader is None:
                raise ImportError(f"Could not load module spec for {target_path}")
            task_module = importlib.util.module_from_spec(module_spec)
            module_spec.loader.exec_module(task_module)
            result["checks"].append(
                self._check("python_import", "Python module imports successfully")
            )
        except Exception as import_error:
            result["errors"].append(
                self._error(
                    "python_import",
                    f"Python import failed: {str(import_error)}",
                    traceback.format_exc(),
                )
            )

    def _validate_python_directory(self, target_path: Path, result: Dict[str, Any]) -> None:
        python_files = sorted(target_path.rglob("*.py"))[: self.MAX_PYTHON_FILES_TO_CHECK]
        failures = []
        for python_file in python_files:
            try:
                py_compile.compile(str(python_file), doraise=True)
            except py_compile.PyCompileError as compile_error:
                failures.append(f"{python_file}: {compile_error.msg}")
                if len(failures) >= 10:
                    break

        if failures:
            result["errors"].append(
                self._error("python_syntax", "Python syntax failures: " + "; ".join(failures))
            )
        elif python_files:
            result["checks"].append(
                self._check(
                    "python_syntax",
                    f"Python syntax check passed for {len(python_files)} file(s)",
                )
            )

    def _validate_c_file(self, target_path: Path, result: Dict[str, Any]) -> None:
        if not shutil.which("gcc"):
            result["warnings"].append(self._warning("c_compile", "gcc is not available; skipped C compile check"))
            return

        with tempfile.TemporaryDirectory(prefix="flowagent-c-") as tmp_dir:
            output_path = Path(tmp_dir) / target_path.stem
            compile_result = self._run_command(["gcc", "-o", str(output_path), str(target_path)], timeout=60)

        if compile_result["returncode"] == 0:
            result["checks"].append(
                self._check(
                    "c_compile",
                    f"C compile check passed in {compile_result['duration_ms']:.2f}ms",
                )
            )
        else:
            result["errors"].append(
                self._error("c_compile", f"C compile failed: {compile_result['output_excerpt']}")
            )

    def _count_lines(self, target_path: Path) -> int:
        try:
            with open(target_path, "r", encoding="utf-8") as source_file:
                return sum(1 for _ in source_file)
        except Exception:
            return 0

    def validate_task_implementation(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Validate if a task has been implemented correctly."""
        start_time = time.time()
        result: Dict[str, Any] = {
            "task_id": task.get("task_id", "unknown"),
            "task_name": task.get("name", "Unknown Task"),
            "validation_time": datetime.now().isoformat(),
            "status": "unknown",
            "checks": [],
            "errors": [],
            "warnings": [],
            "metrics": {
                "execution_time_ms": 0,
                "files_checked": 0,
                "lines_of_code": 0,
            },
            "metadata": {
                "description": task.get("description", ""),
                "priority": task.get("priority", "medium"),
                "tags": task.get("tags", []),
            },
        }

        self._validate_schema(task, result)
        target_file = task.get("target_file") or task.get("target_directory")
        if not target_file:
            result["status"] = "failed"
            result["metrics"]["execution_time_ms"] = round((time.time() - start_time) * 1000, 2)
            return result

        target_path = Path(target_file)
        if str(target_file).endswith("/") or task.get("target_directory"):
            if target_path.exists() and target_path.is_dir():
                result["checks"].append(
                    self._check("directory_exists", f"Target directory exists: {target_file}")
                )
                files = [path for path in target_path.rglob("*") if path.is_file()]
                result["metrics"]["files_checked"] = min(len(files), 10000)
                result["metrics"]["lines_of_code"] = sum(
                    self._count_lines(path)
                    for path in files[:500]
                    if path.suffix.lower() in self.TEXT_EXTENSIONS
                )

                if str(task.get("language", "")).lower() == "python":
                    self._validate_python_directory(target_path, result)
            else:
                result["errors"].append(
                    self._error("validation", f"Target directory missing: {target_file}")
                )
        else:
            if target_path.exists() and target_path.is_file():
                result["checks"].append(
                    self._check("file_exists", f"Target file exists: {target_file}")
                )
                result["metrics"]["files_checked"] = 1
                result["metrics"]["lines_of_code"] = self._count_lines(target_path)

                suffix = target_path.suffix.lower()
                if suffix == ".py":
                    self._validate_python_file(target_path, result)
                elif suffix == ".c":
                    self._validate_c_file(target_path, result)
            else:
                result["errors"].append(
                    self._error("validation", f"Target file missing: {target_file}")
                )

        result["status"] = "failed" if result["errors"] else "passed"
        result["metrics"]["execution_time_ms"] = round((time.time() - start_time) * 1000, 2)
        return result

    def _iter_scan_files(self) -> Iterable[Path]:
        for root, dirs, files in os.walk(self.root_dir):
            root_path = Path(root)
            rel_root = root_path.relative_to(self.root_dir)
            dirs[:] = [
                directory
                for directory in dirs
                if str(rel_root / directory) not in self.EXCLUDED_SCAN_DIRS
                and directory not in self.EXCLUDED_SCAN_DIRS
            ]
            for filename in files:
                path = root_path / filename
                rel_path = path.relative_to(self.root_dir)
                if any(part in self.EXCLUDED_SCAN_DIRS for part in rel_path.parts):
                    continue
                yield path

    def _scan_for_secret_candidates(self, max_findings: int = 40) -> Dict[str, Any]:
        """Find secret-like filenames or patterns without returning secret values."""
        findings: List[Dict[str, str]] = []
        scanned_files = 0

        for path in self._iter_scan_files():
            rel_path = str(path.relative_to(self.root_dir))
            if self.SECRET_FILENAME_PATTERN.search(path.name):
                findings.append({"path": rel_path, "type": "sensitive_filename"})

            if path.suffix.lower() not in self.TEXT_EXTENSIONS:
                if len(findings) >= max_findings:
                    break
                continue

            try:
                if path.stat().st_size > self.MAX_SCAN_FILE_SIZE_BYTES:
                    continue
                content = path.read_text(encoding="utf-8", errors="ignore")
                scanned_files += 1
            except OSError:
                continue

            for pattern_name, pattern in self.SECRET_CONTENT_PATTERNS.items():
                if pattern.search(content):
                    findings.append({"path": rel_path, "type": pattern_name})
                    break

            if len(findings) >= max_findings:
                break

        return {
            "status": "warning" if findings else "passed",
            "scanned_files": scanned_files,
            "findings": findings[:max_findings],
            "truncated": len(findings) >= max_findings,
        }

    def run_repository_checks(self) -> Dict[str, Any]:
        """Run repository-level health checks requested by the cleanup plan."""
        checks: List[Dict[str, str]] = []
        warnings: List[Dict[str, Any]] = []
        errors: List[Dict[str, str]] = []

        command_checks = [
            ("npm_lint", ["npm", "run", "lint"], 180),
            ("npm_build", ["npm", "run", "build"], 240),
            ("kubernetes_render", ["kubectl", "kustomize", "cluster/overlays/prod/"], 120),
        ]
        for check_name, command, timeout in command_checks:
            if shutil.which(command[0]) is None:
                warnings.append(self._warning(check_name, f"{command[0]} is not available; skipped {' '.join(command)}"))
                continue

            command_result = self._run_command(command, timeout=timeout)
            if command_result["returncode"] == 0:
                checks.append(
                    self._check(
                        check_name,
                        f"{' '.join(command)} passed in {command_result['duration_ms']:.2f}ms",
                    )
                )
            else:
                errors.append(
                    self._error(check_name, f"{' '.join(command)} failed: {command_result['output_excerpt']}")
                )

        secret_audit = self._scan_for_secret_candidates()
        if secret_audit["status"] == "passed":
            checks.append(
                self._check(
                    "secrets_audit",
                    f"No high-confidence secret patterns found in {secret_audit['scanned_files']} text file(s)",
                )
            )
        else:
            warnings.append(
                {
                    "type": "secrets_audit",
                    "message": (
                        "Secret-like filenames or patterns were found; review listed paths manually. "
                        "Values are intentionally not included in this report."
                    ),
                    "severity": "warning",
                    "findings": secret_audit["findings"],
                    "truncated": secret_audit["truncated"],
                }
            )

        return {
            "status": "failed" if errors else "passed",
            "checks": checks,
            "warnings": warnings,
            "errors": errors,
        }

    def process_all_tasks(self) -> Dict[str, Any]:
        """Process all task files in the tasks directory."""
        processing_start = time.time()
        task_files = sorted(
            task_file
            for task_file in self.tasks_dir.glob("*.yaml")
            if self._is_task_definition(task_file)
        )

        summary: Dict[str, Any] = {
            "processing_time": datetime.now().isoformat(),
            "total_tasks": len(task_files),
            "passed": 0,
            "failed": 0,
            "warnings": 0,
            "tasks": [],
            "repository_checks": {},
            "overall_metrics": {
                "total_execution_time_ms": 0,
                "total_files_checked": 0,
                "total_lines_of_code": 0,
                "average_task_time_ms": 0,
            },
            "summary": {"pass_rate": 0.0, "recommendations": []},
        }

        task_results_to_write = []
        for task_file in task_files:
            try:
                task = self.load_task(task_file.name)
                result = self.validate_task_implementation(task)
            except Exception as processing_error:
                result = {
                    "task_id": task_file.stem,
                    "task_name": task_file.stem,
                    "validation_time": datetime.now().isoformat(),
                    "status": "failed",
                    "checks": [],
                    "warnings": [],
                    "errors": [
                        self._error(
                            "processing",
                            f"Failed to process task: {str(processing_error)}",
                            traceback.format_exc(),
                        )
                    ],
                    "metrics": {"execution_time_ms": 0, "files_checked": 0, "lines_of_code": 0},
                    "metadata": {"description": "", "priority": "medium", "tags": []},
                }

            if result["status"] == "passed":
                summary["passed"] += 1
            else:
                summary["failed"] += 1
            summary["warnings"] += len(result.get("warnings", []))
            summary["overall_metrics"]["total_execution_time_ms"] += result["metrics"]["execution_time_ms"]
            summary["overall_metrics"]["total_files_checked"] += result["metrics"]["files_checked"]
            summary["overall_metrics"]["total_lines_of_code"] += result["metrics"]["lines_of_code"]
            summary["tasks"].append(result)
            task_results_to_write.append((task_file.stem, result))

        repository_checks = self.run_repository_checks()
        summary["repository_checks"] = repository_checks
        summary["warnings"] += len(repository_checks.get("warnings", []))
        if repository_checks["status"] == "failed":
            summary["failed"] += 1

        processing_time_ms = round((time.time() - processing_start) * 1000, 2)
        summary["overall_metrics"]["total_execution_time_ms"] = processing_time_ms
        if summary["total_tasks"] > 0:
            summary["overall_metrics"]["average_task_time_ms"] = round(
                processing_time_ms / summary["total_tasks"], 2
            )
            summary["summary"]["pass_rate"] = round(
                (summary["passed"] / summary["total_tasks"]) * 100, 2
            )

        if summary["failed"] > 0:
            summary["summary"]["recommendations"].append(
                f"⚠️ {summary['failed']} validation area(s) failed. Review errors and fix issues."
            )
        if summary["warnings"] > 0:
            summary["summary"]["recommendations"].append(
                f"ℹ️ {summary['warnings']} warning(s) detected. Review for potential improvements."
            )
        if summary["failed"] == 0:
            summary["summary"]["recommendations"].append("✅ All blocking validations passed.")

        for task_stem, result in task_results_to_write:
            result_file = self.results_dir / f"{task_stem}_result.json"
            with open(result_file, "w", encoding="utf-8") as result_output_file:
                json.dump(result, result_output_file, ensure_ascii=False, indent=2)

        summary_file = self.results_dir / "task_processing_summary.json"
        with open(summary_file, "w", encoding="utf-8") as summary_output_file:
            json.dump(summary, summary_output_file, ensure_ascii=False, indent=2)

        self._generate_markdown_report(summary)
        self._generate_html_report(summary)
        return summary

    def _generate_markdown_report(self, summary: Dict[str, Any]) -> None:
        """Generate a Markdown report for easy reading."""
        lines = [
            "# FlowAgent Task Processing Report\n\n",
            f"**Report Generated:** {summary['processing_time']}\n\n",
            "## Executive Summary\n\n",
            f"- **Total Tasks:** {summary['total_tasks']}\n",
            f"- **Passed Tasks:** {summary['passed']} ✅\n",
            f"- **Failed Validation Areas:** {summary['failed']} ❌\n",
            f"- **Warnings:** {summary['warnings']} ⚠️\n",
            f"- **Task Pass Rate:** {summary['summary']['pass_rate']}%\n",
            f"- **Total Execution Time:** {summary['overall_metrics']['total_execution_time_ms']:.2f}ms\n",
            f"- **Average Task Time:** {summary['overall_metrics']['average_task_time_ms']:.2f}ms\n\n",
            "## Overall Metrics\n\n",
            f"- **Total Files Checked:** {summary['overall_metrics']['total_files_checked']}\n",
            f"- **Total Lines of Code:** {summary['overall_metrics']['total_lines_of_code']}\n\n",
        ]

        if summary["summary"]["recommendations"]:
            lines.append("## Recommendations\n\n")
            for rec in summary["summary"]["recommendations"]:
                lines.append(f"- {rec}\n")
            lines.append("\n")

        lines.append("## Repository Health Checks\n\n")
        repository_checks = summary.get("repository_checks", {})
        for check in repository_checks.get("checks", []):
            lines.append(f"- ✅ {check.get('message', check.get('check'))}\n")
        for warning in repository_checks.get("warnings", []):
            lines.append(f"- ⚠️ **[{warning.get('type', 'warning')}]** {warning.get('message')}\n")
            for finding in warning.get("findings", [])[:20]:
                lines.append(f"  - `{finding['path']}` ({finding['type']})\n")
        for error in repository_checks.get("errors", []):
            lines.append(f"- ❌ **[{error.get('type', 'error')}]** {error.get('message')}\n")
        lines.append("\n")

        lines.append("## Task Details\n\n")
        for task in summary["tasks"]:
            status_emoji = "✅" if task["status"] == "passed" else "❌"
            lines.append(f"### {status_emoji} {task['task_id']}\n\n")
            if task.get("metadata", {}).get("description"):
                lines.append(f"**Description:** {task['metadata']['description']}\n\n")
            lines.append("**Metrics:**\n")
            lines.append(f"- Execution Time: {task['metrics']['execution_time_ms']:.2f}ms\n")
            lines.append(f"- Files Checked: {task['metrics']['files_checked']}\n")
            lines.append(f"- Lines of Code: {task['metrics']['lines_of_code']}\n\n")
            if task.get("checks"):
                lines.append("**Checks:**\n")
                for check in task["checks"]:
                    lines.append(f"- ✅ {check.get('message', check.get('check'))}\n")
                lines.append("\n")
            if task.get("errors"):
                lines.append("**Errors:**\n")
                for error in task["errors"]:
                    lines.append(f"- ❌ **[{error.get('type', 'error')}]** {error.get('message')}\n")
                lines.append("\n")
            if task.get("warnings"):
                lines.append("**Warnings:**\n")
                for warning in task["warnings"]:
                    lines.append(f"- ⚠️ **[{warning.get('type', 'warning')}]** {warning.get('message')}\n")
                lines.append("\n")
            lines.append("---\n\n")

        with open(self.results_dir / "report.md", "w", encoding="utf-8") as report_file:
            report_file.write("".join(lines))

    def _generate_html_report(self, summary: Dict[str, Any]) -> None:
        """Generate an HTML report with escaped report data."""
        pass_rate = summary["summary"]["pass_rate"]
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FlowAgent Task Processing Report</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; line-height: 1.6; color: #333; background: #f5f5f5; padding: 20px; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; border-radius: 10px; padding: 30px; box-shadow: 0 2px 10px rgba(0,0,0,.1); }}
        .summary-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; margin: 24px 0; }}
        .metric-card {{ color: white; background: #667eea; padding: 16px; border-radius: 8px; }}
        .success {{ background: #11998e; }} .danger {{ background: #e74c3c; }} .warning {{ background: #d68910; }}
        .metric-value {{ font-size: 2em; font-weight: 700; }}
        .task-card {{ background: #f8f9fa; border-left: 4px solid #3498db; padding: 16px; margin: 12px 0; border-radius: 5px; }}
        .task-card.passed {{ border-left-color: #2ecc71; }} .task-card.failed {{ border-left-color: #e74c3c; }}
        .check-item {{ background: #d5f4e6; color: #166534; padding: 8px; margin: 4px 0; border-radius: 4px; }}
        .warning-item {{ background: #fcf3cf; color: #92400e; padding: 8px; margin: 4px 0; border-radius: 4px; }}
        .error-item {{ background: #fadbd8; color: #991b1b; padding: 8px; margin: 4px 0; border-radius: 4px; }}
        code {{ background: #eef2f7; padding: 2px 4px; border-radius: 3px; }}
    </style>
</head>
<body><div class="container">
    <h1>📊 FlowAgent Task Processing Report</h1>
    <p>Generated: {html.escape(summary['processing_time'])}</p>
    <div class="summary-grid">
        <div class="metric-card"><div>Total Tasks</div><div class="metric-value">{summary['total_tasks']}</div></div>
        <div class="metric-card success"><div>Passed Tasks</div><div class="metric-value">{summary['passed']}</div></div>
        <div class="metric-card danger"><div>Failed Areas</div><div class="metric-value">{summary['failed']}</div></div>
        <div class="metric-card warning"><div>Warnings</div><div class="metric-value">{summary['warnings']}</div></div>
    </div>
    <p><strong>Task Pass Rate:</strong> {pass_rate:.1f}%</p>
"""

        if summary["summary"]["recommendations"]:
            html_content += "<h2>Recommendations</h2><ul>"
            for rec in summary["summary"]["recommendations"]:
                html_content += f"<li>{html.escape(rec)}</li>"
            html_content += "</ul>"

        html_content += "<h2>Repository Health Checks</h2>"
        repository_checks = summary.get("repository_checks", {})
        for check in repository_checks.get("checks", []):
            html_content += f"<div class='check-item'>✓ {html.escape(check.get('message', check.get('check', '')))}</div>"
        for warning in repository_checks.get("warnings", []):
            html_content += f"<div class='warning-item'>⚠️ [{html.escape(warning.get('type', 'warning'))}] {html.escape(warning.get('message', ''))}"
            findings = warning.get("findings", [])[:20]
            if findings:
                html_content += "<ul>"
                for finding in findings:
                    html_content += f"<li><code>{html.escape(finding['path'])}</code> ({html.escape(finding['type'])})</li>"
                html_content += "</ul>"
            html_content += "</div>"
        for error in repository_checks.get("errors", []):
            html_content += f"<div class='error-item'>✗ [{html.escape(error.get('type', 'error'))}] {html.escape(error.get('message', ''))}</div>"

        html_content += "<h2>Task Details</h2>"
        for task in summary["tasks"]:
            status_class = html.escape(task["status"])
            html_content += f"<div class='task-card {status_class}'><h3>{html.escape(task['task_id'])}</h3>"
            html_content += f"<p><strong>Status:</strong> {status_class}</p>"
            description = task.get("metadata", {}).get("description")
            if description:
                html_content += f"<p><strong>Description:</strong> {html.escape(description)}</p>"
            html_content += f"<p><strong>Metrics:</strong> {task['metrics']['execution_time_ms']:.2f}ms, {task['metrics']['files_checked']} files, {task['metrics']['lines_of_code']} LOC</p>"
            for check in task.get("checks", []):
                html_content += f"<div class='check-item'>✓ {html.escape(check.get('message', check.get('check', '')))}</div>"
            for warning in task.get("warnings", []):
                html_content += f"<div class='warning-item'>⚠️ [{html.escape(warning.get('type', 'warning'))}] {html.escape(warning.get('message', ''))}</div>"
            for error in task.get("errors", []):
                html_content += f"<div class='error-item'>✗ [{html.escape(error.get('type', 'error'))}] {html.escape(error.get('message', ''))}</div>"
            html_content += "</div>"

        html_content += "</div></body></html>"
        with open(self.results_dir / "report.html", "w", encoding="utf-8") as report_file:
            report_file.write(html_content)

    def print_summary(self, summary: Dict[str, Any]) -> None:
        """Print a formatted summary of task processing."""
        print("=== FlowAgent Task Processing Summary ===")
        print(f"Processing time: {summary['processing_time']}")
        print(f"Total tasks: {summary['total_tasks']}")
        print(f"Passed tasks: {summary['passed']}")
        print(f"Failed validation areas: {summary['failed']}")
        print(f"Warnings: {summary['warnings']}")
        print()

        for task in summary["tasks"]:
            status_icon = "✓" if task["status"] == "passed" else "✗"
            print(f"{status_icon} {task['task_id']} - {task['status']}")
            for check in task.get("checks", []):
                print(f"  ✓ {check.get('message', check.get('check'))}")
            for warning in task.get("warnings", []):
                print(f"  ⚠ [{warning.get('type', 'warning')}] {warning.get('message')}")
            for error in task.get("errors", []):
                print(f"  ✗ [{error.get('type', 'error')}] {error.get('message')}")
            print()

        repository_checks = summary.get("repository_checks", {})
        print("Repository health checks:")
        for check in repository_checks.get("checks", []):
            print(f"  ✓ {check.get('message', check.get('check'))}")
        for warning in repository_checks.get("warnings", []):
            print(f"  ⚠ [{warning.get('type', 'warning')}] {warning.get('message')}")
            for finding in warning.get("findings", [])[:10]:
                print(f"    - {finding['path']} ({finding['type']})")
        for error in repository_checks.get("errors", []):
            print(f"  ✗ [{error.get('type', 'error')}] {error.get('message')}")
        print()


def main() -> None:
    """Main entry point."""
    processor = TaskProcessor()
    print("🚀 FlowAgent Task Processor")
    print("Automatically receiving, parsing and validating code generation tasks...")
    print()

    summary = processor.process_all_tasks()
    processor.print_summary(summary)

    print("=" * 70)
    print("📄 Reports Generated")
    print("=" * 70)
    print(f"  - JSON Summary: {processor.results_dir / 'task_processing_summary.json'}")
    print(f"  - Markdown Report: {processor.results_dir / 'report.md'}")
    print(f"  - HTML Report: {processor.results_dir / 'report.html'}")
    print(f"  - Individual Results: {processor.results_dir / '*_result.json'}")
    print()

    if summary["failed"] > 0:
        print("❌ Some validation areas failed!")
        sys.exit(1)

    print("✅ All blocking validations passed!")
    sys.exit(0)


if __name__ == "__main__":
    main()
