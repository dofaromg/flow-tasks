#!/usr/bin/env python3
"""
FlowAgent Task Processor
Automatically receives, parses and validates code generation tasks
Enhanced with professional reporting capabilities for software engineers
"""

import os
import sys
import yaml
import json
import importlib.util
import time
import traceback
import html
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

class TaskProcessor:
    def __init__(self, tasks_dir: str = "tasks"):
        self.tasks_dir = Path(tasks_dir)
        self.results_dir = self.tasks_dir / "results"
        self.results_dir.mkdir(exist_ok=True)
        
    def load_task(self, task_file: str) -> Dict[str, Any]:
        """Load task definition from YAML file"""
        task_path = self.tasks_dir / task_file
        if not task_path.exists():
            raise FileNotFoundError(f"Task file not found: {task_path}")
            
        with open(task_path, 'r', encoding='utf-8') as task_file:
            return yaml.safe_load(task_file)
    
    def validate_task_implementation(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Validate if task has been implemented correctly"""
        start_time = time.time()
        
        result = {
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
                "lines_of_code": 0
            },
            "metadata": {
                "description": task.get("description", ""),
                "priority": task.get("priority", "medium"),
                "tags": task.get("tags", [])
            }
        }
        
        target_file = task.get("target_file")
        if not target_file:
            result["errors"].append({
                "type": "configuration",
                "message": "No target_file specified in task",
                "severity": "error"
            })
            result["status"] = "failed"
            result["metrics"]["execution_time_ms"] = (time.time() - start_time) * 1000
            return result
            
        # Check if target file exists
        if target_file.endswith('/'):
            # Directory target
            target_path = Path(target_file)
            if target_path.exists() and target_path.is_dir():
                result["checks"].append({
                    "check": "directory_exists",
                    "status": "passed",
                    "message": f"Target directory exists: {target_file}"
                })
                # Count files in directory
                file_count = len(list(target_path.rglob("*")))
                result["metrics"]["files_checked"] = file_count
                result["status"] = "passed"
            else:
                result["errors"].append({
                    "type": "validation",
                    "message": f"Target directory missing: {target_file}",
                    "severity": "error"
                })
                result["status"] = "failed"
        else:
            # File target
            target_path = Path(target_file)
            if target_path.exists():
                result["checks"].append({
                    "check": "file_exists",
                    "status": "passed",
                    "message": f"Target file exists: {target_file}"
                })
                result["metrics"]["files_checked"] = 1
                
                # Count lines of code efficiently
                try:
                    with open(target_path, 'r', encoding='utf-8') as f:
                        # Count lines without loading entire file
                        line_count = sum(1 for _ in f)
                        result["metrics"]["lines_of_code"] = line_count
                except Exception as e:
                    result["warnings"].append({
                        "type": "metrics",
                        "message": f"Could not count lines: {str(e)}"
                    })
                
                # Try to import/validate Python files
                if target_file.endswith('.py'):
                    try:
                        module_spec = importlib.util.spec_from_file_location("task_module", target_path)
                        task_module = importlib.util.module_from_spec(module_spec)
                        module_spec.loader.exec_module(task_module)
                        result["checks"].append({
                            "check": "python_import",
                            "status": "passed",
                            "message": "Python module imports successfully"
                        })
                        result["status"] = "passed"
                    except Exception as import_error:
                        result["errors"].append({
                            "type": "python_import",
                            "message": f"Python import failed: {str(import_error)}",
                            "severity": "error",
                            "traceback": traceback.format_exc()
                        })
                        result["status"] = "failed"
                else:
                    result["status"] = "passed"
            else:
                result["errors"].append({
                    "type": "validation",
                    "message": f"Target file missing: {target_file}",
                    "severity": "error"
                })
                result["status"] = "failed"
        
        # Calculate execution time
        result["metrics"]["execution_time_ms"] = round((time.time() - start_time) * 1000, 2)
        
        return result
    
    def process_all_tasks(self) -> Dict[str, Any]:
        """Process all task files in the tasks directory"""
        processing_start = time.time()
        
        # Use more specific glob pattern to avoid filtering
        task_files = list(self.tasks_dir.glob("2025-*.yaml"))
        
        summary = {
            "processing_time": datetime.now().isoformat(),
            "total_tasks": len(task_files),
            "passed": 0,
            "failed": 0,
            "warnings": 0,
            "tasks": [],
            "overall_metrics": {
                "total_execution_time_ms": 0,
                "total_files_checked": 0,
                "total_lines_of_code": 0,
                "average_task_time_ms": 0
            },
            "summary": {
                "pass_rate": 0.0,
                "recommendations": []
            }
        }
        
        # Process task files
        for task_file in task_files:
            try:
                task = self.load_task(task_file.name)
                result = self.validate_task_implementation(task)
                
                if result["status"] == "passed":
                    summary["passed"] += 1
                else:
                    summary["failed"] += 1
                
                if result.get("warnings"):
                    summary["warnings"] += len(result["warnings"])
                
                # Aggregate metrics
                summary["overall_metrics"]["total_execution_time_ms"] += result["metrics"]["execution_time_ms"]
                summary["overall_metrics"]["total_files_checked"] += result["metrics"]["files_checked"]
                summary["overall_metrics"]["total_lines_of_code"] += result["metrics"]["lines_of_code"]
                    
                summary["tasks"].append(result)
                
                # Save individual task result
                result_file = self.results_dir / f"{task_file.stem}_result.json"
                with open(result_file, 'w', encoding='utf-8') as result_output_file:
                    json.dump(result, result_output_file, ensure_ascii=False, indent=2)
                    
            except Exception as processing_error:
                error_result = {
                    "task_id": task_file.stem,
                    "task_name": task_file.stem,
                    "status": "error",
                    "errors": [{
                        "type": "processing",
                        "message": f"Failed to process task: {str(processing_error)}",
                        "severity": "error",
                        "traceback": traceback.format_exc()
                    }],
                    "metrics": {
                        "execution_time_ms": 0,
                        "files_checked": 0,
                        "lines_of_code": 0
                    }
                }
                summary["tasks"].append(error_result)
                summary["failed"] += 1
        
        # Calculate overall metrics
        processing_time_ms = (time.time() - processing_start) * 1000
        summary["overall_metrics"]["total_execution_time_ms"] = round(processing_time_ms, 2)
        
        if summary["total_tasks"] > 0:
            summary["overall_metrics"]["average_task_time_ms"] = round(
                processing_time_ms / summary["total_tasks"], 2
            )
            summary["summary"]["pass_rate"] = round(
                (summary["passed"] / summary["total_tasks"]) * 100, 2
            )
        
        # Generate recommendations
        if summary["failed"] > 0:
            summary["summary"]["recommendations"].append(
                f"⚠️  {summary['failed']} task(s) failed validation. Review errors and fix issues."
            )
        if summary["warnings"] > 0:
            summary["summary"]["recommendations"].append(
                f"ℹ️  {summary['warnings']} warning(s) detected. Review for potential improvements."
            )
        if summary["passed"] == summary["total_tasks"]:
            summary["summary"]["recommendations"].append(
                "✅ All tasks passed validation. Great job!"
            )
        
        # Save summary
        summary_file = self.results_dir / "task_processing_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as summary_output_file:
            json.dump(summary, summary_output_file, ensure_ascii=False, indent=2)
        
        # Generate additional report formats
        self._generate_markdown_report(summary)
        self._generate_html_report(summary)
            
        return summary
    
    def _generate_markdown_report(self, summary: Dict[str, Any]) -> None:
        """Generate a Markdown report for easy reading"""
        report_file = self.results_dir / "report.md"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("# FlowAgent Task Processing Report\n\n")
            f.write(f"**Report Generated:** {summary['processing_time']}\n\n")
            
            # Executive Summary
            f.write("## Executive Summary\n\n")
            f.write(f"- **Total Tasks:** {summary['total_tasks']}\n")
            f.write(f"- **Passed:** {summary['passed']} ✅\n")
            f.write(f"- **Failed:** {summary['failed']} ❌\n")
            f.write(f"- **Warnings:** {summary['warnings']} ⚠️\n")
            f.write(f"- **Pass Rate:** {summary['summary']['pass_rate']}%\n")
            f.write(f"- **Total Execution Time:** {summary['overall_metrics']['total_execution_time_ms']:.2f}ms\n")
            f.write(f"- **Average Task Time:** {summary['overall_metrics']['average_task_time_ms']:.2f}ms\n\n")
            
            # Metrics
            f.write("## Overall Metrics\n\n")
            f.write(f"- **Total Files Checked:** {summary['overall_metrics']['total_files_checked']}\n")
            f.write(f"- **Total Lines of Code:** {summary['overall_metrics']['total_lines_of_code']}\n\n")
            
            # Recommendations
            if summary['summary']['recommendations']:
                f.write("## Recommendations\n\n")
                for rec in summary['summary']['recommendations']:
                    f.write(f"- {rec}\n")
                f.write("\n")
            
            # Task Details
            f.write("## Task Details\n\n")
            for task in summary['tasks']:
                status_emoji = "✅" if task['status'] == 'passed' else "❌"
                f.write(f"### {status_emoji} {task['task_id']}\n\n")
                
                if task.get('task_name'):
                    f.write(f"**Name:** {task['task_name']}\n\n")
                
                if task.get('metadata', {}).get('description'):
                    f.write(f"**Description:** {task['metadata']['description']}\n\n")
                
                # Metrics
                f.write("**Metrics:**\n")
                f.write(f"- Execution Time: {task['metrics']['execution_time_ms']:.2f}ms\n")
                f.write(f"- Files Checked: {task['metrics']['files_checked']}\n")
                f.write(f"- Lines of Code: {task['metrics']['lines_of_code']}\n\n")
                
                # Checks
                if task.get('checks'):
                    f.write("**Checks:**\n")
                    for check in task['checks']:
                        if isinstance(check, dict):
                            f.write(f"- ✅ {check.get('message', check.get('check'))}\n")
                        else:
                            f.write(f"- {check}\n")
                    f.write("\n")
                
                # Errors
                if task.get('errors'):
                    f.write("**Errors:**\n")
                    for error in task['errors']:
                        if isinstance(error, dict):
                            f.write(f"- ❌ **[{error.get('type', 'error')}]** {error.get('message')}\n")
                        else:
                            f.write(f"- ❌ {error}\n")
                    f.write("\n")
                
                # Warnings
                if task.get('warnings'):
                    f.write("**Warnings:**\n")
                    for warning in task['warnings']:
                        if isinstance(warning, dict):
                            f.write(f"- ⚠️ **[{warning.get('type', 'warning')}]** {warning.get('message')}\n")
                        else:
                            f.write(f"- ⚠️ {warning}\n")
                    f.write("\n")
                
                f.write("---\n\n")
    
    def _generate_html_report(self, summary: Dict[str, Any]) -> None:
        """Generate an HTML report with visual elements"""
        report_file = self.results_dir / "report.html"
        
        # Calculate pass rate for progress bar - sanitize for HTML
        pass_rate = summary['summary']['pass_rate']
        pass_rate_str = html.escape(f"{pass_rate:.1f}")
        
        # Escape summary values for HTML
        processing_time = html.escape(summary['processing_time'])
        total_tasks = html.escape(str(summary['total_tasks']))
        passed = html.escape(str(summary['passed']))
        failed = html.escape(str(summary['failed']))
        warnings = html.escape(str(summary['warnings']))
        total_exec_time = html.escape(f"{summary['overall_metrics']['total_execution_time_ms']:.2f}")
        avg_task_time = html.escape(f"{summary['overall_metrics']['average_task_time_ms']:.2f}")
        total_files = html.escape(str(summary['overall_metrics']['total_files_checked']))
        total_loc = html.escape(str(summary['overall_metrics']['total_lines_of_code']))
        
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FlowAgent Task Processing Report</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
            padding: 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            padding: 30px;
        }}
        h1 {{
            color: #2c3e50;
            margin-bottom: 10px;
            font-size: 2.5em;
        }}
        .timestamp {{
            color: #7f8c8d;
            margin-bottom: 30px;
            font-size: 0.9em;
        }}
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .metric-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        .metric-card.success {{
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        }}
        .metric-card.danger {{
            background: linear-gradient(135deg, #ee0979 0%, #ff6a00 100%);
        }}
        .metric-card.warning {{
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        }}
        .metric-label {{
            font-size: 0.9em;
            opacity: 0.9;
            margin-bottom: 5px;
        }}
        .metric-value {{
            font-size: 2em;
            font-weight: bold;
        }}
        .progress-bar {{
            height: 30px;
            background: #ecf0f1;
            border-radius: 15px;
            overflow: hidden;
            margin: 20px 0;
        }}
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #11998e 0%, #38ef7d 100%);
            transition: width 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
        }}
        .section {{
            margin: 30px 0;
        }}
        h2 {{
            color: #2c3e50;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #3498db;
        }}
        .task-card {{
            background: #f8f9fa;
            border-left: 4px solid #3498db;
            padding: 20px;
            margin-bottom: 15px;
            border-radius: 5px;
        }}
        .task-card.passed {{
            border-left-color: #2ecc71;
        }}
        .task-card.failed {{
            border-left-color: #e74c3c;
        }}
        .task-header {{
            display: flex;
            align-items: center;
            margin-bottom: 10px;
        }}
        .task-status {{
            width: 30px;
            height: 30px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-right: 10px;
            font-size: 1.2em;
        }}
        .task-status.passed {{
            background: #2ecc71;
            color: white;
        }}
        .task-status.failed {{
            background: #e74c3c;
            color: white;
        }}
        .task-title {{
            font-size: 1.3em;
            font-weight: bold;
            color: #2c3e50;
        }}
        .task-metrics {{
            display: flex;
            gap: 20px;
            margin: 10px 0;
            flex-wrap: wrap;
        }}
        .task-metric {{
            display: flex;
            align-items: center;
            gap: 5px;
            color: #7f8c8d;
            font-size: 0.9em;
        }}
        .checks, .errors, .warnings {{
            margin: 10px 0;
        }}
        .check-item, .error-item, .warning-item {{
            padding: 8px 12px;
            margin: 5px 0;
            border-radius: 4px;
        }}
        .check-item {{
            background: #d5f4e6;
            color: #27ae60;
        }}
        .error-item {{
            background: #fadbd8;
            color: #c0392b;
        }}
        .warning-item {{
            background: #fcf3cf;
            color: #d68910;
        }}
        .recommendations {{
            background: #e8f4f8;
            padding: 15px;
            border-radius: 5px;
            border-left: 4px solid #3498db;
        }}
        .recommendations ul {{
            list-style-position: inside;
            margin-left: 10px;
        }}
        .footer {{
            text-align: center;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #ecf0f1;
            color: #7f8c8d;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 FlowAgent Task Processing Report</h1>
        <div class="timestamp">Generated: {processing_time}</div>
        
        <div class="summary-grid">
            <div class="metric-card">
                <div class="metric-label">Total Tasks</div>
                <div class="metric-value">{total_tasks}</div>
            </div>
            <div class="metric-card success">
                <div class="metric-label">✅ Passed</div>
                <div class="metric-value">{passed}</div>
            </div>
            <div class="metric-card danger">
                <div class="metric-label">❌ Failed</div>
                <div class="metric-value">{failed}</div>
            </div>
            <div class="metric-card warning">
                <div class="metric-label">⚠️ Warnings</div>
                <div class="metric-value">{warnings}</div>
            </div>
        </div>
        
        <div class="progress-bar">
            <div class="progress-fill" style="width: {pass_rate}%">
                {pass_rate_str}% Pass Rate
            </div>
        </div>
        
        <div class="section">
            <h2>⏱️ Performance Metrics</h2>
            <div class="task-metrics">
                <div class="task-metric">
                    <strong>Total Execution Time:</strong> {total_exec_time}ms
                </div>
                <div class="task-metric">
                    <strong>Average Task Time:</strong> {avg_task_time}ms
                </div>
                <div class="task-metric">
                    <strong>Files Checked:</strong> {total_files}
                </div>
                <div class="task-metric">
                    <strong>Lines of Code:</strong> {total_loc}
                </div>
            </div>
        </div>
"""
        
        # Add recommendations (with HTML escaping)
        if summary['summary']['recommendations']:
            html_content += """
        <div class="section">
            <h2>💡 Recommendations</h2>
            <div class="recommendations">
                <ul>
"""
            for rec in summary['summary']['recommendations']:
                html_content += f"                    <li>{html.escape(rec)}</li>\n"
            html_content += """                </ul>
            </div>
        </div>
"""
        
        # Add task details
        html_content += """
        <div class="section">
            <h2>📋 Task Details</h2>
"""
        
        for task in summary['tasks']:
            status_class = task['status']
            status_icon = "✓" if task['status'] == 'passed' else "✗"
            task_id = html.escape(task['task_id'])
            
            html_content += f"""
            <div class="task-card {status_class}">
                <div class="task-header">
                    <div class="task-status {status_class}">{status_icon}</div>
                    <div class="task-title">{task_id}</div>
                </div>
"""
            
            if task.get('metadata', {}).get('description'):
                desc = html.escape(task['metadata']['description'])
                html_content += f"                <p><strong>Description:</strong> {desc}</p>\n"
            
            exec_time = html.escape(f"{task['metrics']['execution_time_ms']:.2f}")
            files_checked = html.escape(str(task['metrics']['files_checked']))
            loc = html.escape(str(task['metrics']['lines_of_code']))
            
            html_content += f"""
                <div class="task-metrics">
                    <div class="task-metric">⏱️ {exec_time}ms</div>
                    <div class="task-metric">📁 {files_checked} files</div>
                    <div class="task-metric">📝 {loc} LOC</div>
                </div>
"""
            
            # Add checks (with HTML escaping)
            if task.get('checks'):
                html_content += "                <div class='checks'>\n"
                for check in task['checks']:
                    if isinstance(check, dict):
                        msg = html.escape(check.get('message', check.get('check', '')))
                    else:
                        msg = html.escape(str(check))
                    html_content += f"                    <div class='check-item'>✓ {msg}</div>\n"
                html_content += "                </div>\n"
            
            # Add errors (with HTML escaping)
            if task.get('errors'):
                html_content += "                <div class='errors'>\n"
                for error in task['errors']:
                    if isinstance(error, dict):
                        error_type = html.escape(error.get('type', 'error'))
                        error_msg = html.escape(error.get('message', ''))
                        msg = f"[{error_type}] {error_msg}"
                    else:
                        msg = html.escape(str(error))
                    html_content += f"                    <div class='error-item'>✗ {msg}</div>\n"
                html_content += "                </div>\n"
            
            # Add warnings (with HTML escaping)
            if task.get('warnings'):
                html_content += "                <div class='warnings'>\n"
                for warning in task['warnings']:
                    if isinstance(warning, dict):
                        warning_type = html.escape(warning.get('type', 'warning'))
                        warning_msg = html.escape(warning.get('message', ''))
                        msg = f"[{warning_type}] {warning_msg}"
                    else:
                        msg = html.escape(str(warning))
                    html_content += f"                    <div class='warning-item'>⚠️ {msg}</div>\n"
                html_content += "                </div>\n"
            
            html_content += "            </div>\n"
        
        html_content += """
        </div>
        
        <div class="footer">
            FlowAgent Task Processor - Automated Code Generation Validation System
        </div>
    </div>
</body>
</html>
"""
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    def print_summary(self, summary: Dict[str, Any]):
        """Print a formatted summary of task processing"""
        print("=" * 70)
        print("FlowAgent Task Processing Summary".center(70))
        print("=" * 70)
        print()
        print(f"📅 Processing Time: {summary['processing_time']}")
        print(f"📊 Total Tasks:     {summary['total_tasks']}")
        print(f"✅ Passed:          {summary['passed']}")
        print(f"❌ Failed:          {summary['failed']}")
        print(f"⚠️  Warnings:        {summary['warnings']}")
        print(f"📈 Pass Rate:       {summary['summary']['pass_rate']}%")
        print()
        print("-" * 70)
        print("Performance Metrics".center(70))
        print("-" * 70)
        print(f"⏱️  Total Execution Time:  {summary['overall_metrics']['total_execution_time_ms']:.2f}ms")
        print(f"⏱️  Average Task Time:     {summary['overall_metrics']['average_task_time_ms']:.2f}ms")
        print(f"📁 Total Files Checked:   {summary['overall_metrics']['total_files_checked']}")
        print(f"📝 Total Lines of Code:   {summary['overall_metrics']['total_lines_of_code']}")
        print()
        
        if summary['summary']['recommendations']:
            print("-" * 70)
            print("Recommendations".center(70))
            print("-" * 70)
            for rec in summary['summary']['recommendations']:
                print(f"  {rec}")
            print()
        
        print("-" * 70)
        print("Task Details".center(70))
        print("-" * 70)
        print()
        
        for task in summary["tasks"]:
            status_icon = "✅" if task["status"] == "passed" else "❌"
            print(f"{status_icon} {task['task_id']} [{task['status'].upper()}]")
            print(f"   ⏱️  Execution: {task['metrics']['execution_time_ms']:.2f}ms | "
                  f"📁 Files: {task['metrics']['files_checked']} | "
                  f"📝 LOC: {task['metrics']['lines_of_code']}")
            
            if task.get("checks"):
                for check in task["checks"]:
                    if isinstance(check, dict):
                        print(f"   ✓ {check.get('message', check.get('check'))}")
                    else:
                        print(f"   {check}")
                    
            if task.get("errors"):
                for error in task["errors"]:
                    if isinstance(error, dict):
                        print(f"   ✗ [{error.get('type', 'error')}] {error.get('message')}")
                    else:
                        print(f"   ✗ {error}")
            
            if task.get("warnings"):
                for warning in task["warnings"]:
                    if isinstance(warning, dict):
                        print(f"   ⚠️  [{warning.get('type', 'warning')}] {warning.get('message')}")
                    else:
                        print(f"   ⚠️  {warning}")
            print()

def main():
    """Main entry point"""
    processor = TaskProcessor()
    
    print("🚀 FlowAgent Task Processor")
    print("Automatically receiving, parsing and validating code generation tasks...")
    print()
    
    summary = processor.process_all_tasks()
    processor.print_summary(summary)
    
    # Print report file locations
    print("=" * 70)
    print("📄 Reports Generated")
    print("=" * 70)
    print(f"  - JSON Summary: {processor.results_dir / 'task_processing_summary.json'}")
    print(f"  - Markdown Report: {processor.results_dir / 'report.md'}")
    print(f"  - HTML Report: {processor.results_dir / 'report.html'}")
    print(f"  - Individual Results: {processor.results_dir / '*_result.json'}")
    print()
    
    # Exit with appropriate code
    if summary["failed"] > 0:
        print("❌ Some tasks failed validation!")
        sys.exit(1)
    else:
        print("✅ All tasks passed validation!")
        sys.exit(0)

if __name__ == "__main__":
    main()