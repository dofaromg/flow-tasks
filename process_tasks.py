#!/usr/bin/env python3
"""
FlowAgent Task Processor
Automatically receives, parses and validates code generation tasks
"""

import os
import sys
import yaml
import json
import importlib.util
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

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
            
        with open(task_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def validate_task_implementation(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Validate if task has been implemented correctly"""
        result = {
            "task_id": task.get("task_id", "unknown"),
            "validation_time": datetime.now().isoformat(),
            "status": "unknown",
            "checks": [],
            "errors": []
        }
        
        target_file = task.get("target_file")
        if not target_file:
            result["errors"].append("No target_file specified in task")
            result["status"] = "failed"
            return result
            
        # Check if target file exists
        if target_file.endswith('/'):
            # Directory target
            target_path = Path(target_file)
            if target_path.exists() and target_path.is_dir():
                result["checks"].append(f"✓ Target directory exists: {target_file}")
                result["status"] = "passed"
            else:
                result["errors"].append(f"Target directory missing: {target_file}")
                result["status"] = "failed"
        else:
            # File target
            target_path = Path(target_file)
            if target_path.exists():
                result["checks"].append(f"✓ Target file exists: {target_file}")
                
                # Try to import/validate Python files
                if target_file.endswith('.py'):
                    try:
                        spec = importlib.util.spec_from_file_location("task_module", target_path)
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                        result["checks"].append(f"✓ Python module imports successfully")
                        result["status"] = "passed"
                    except Exception as e:
                        result["errors"].append(f"Python import failed: {str(e)}")
                        result["status"] = "failed"
                else:
                    result["status"] = "passed"
            else:
                result["errors"].append(f"Target file missing: {target_file}")
                result["status"] = "failed"
                
        return result
    
    def process_all_tasks(self) -> Dict[str, Any]:
        """Process all task files in the tasks directory"""
        summary = {
            "processing_time": datetime.now().isoformat(),
            "total_tasks": 0,
            "passed": 0,
            "failed": 0,
            "tasks": []
        }
        
        # Find all YAML task files
        for task_file in self.tasks_dir.glob("*.yaml"):
            if task_file.name.startswith("2025-"):  # Task file pattern
                summary["total_tasks"] += 1
                
                try:
                    task = self.load_task(task_file.name)
                    result = self.validate_task_implementation(task)
                    
                    if result["status"] == "passed":
                        summary["passed"] += 1
                    else:
                        summary["failed"] += 1
                        
                    summary["tasks"].append(result)
                    
                    # Save individual task result
                    result_file = self.results_dir / f"{task_file.stem}_result.json"
                    with open(result_file, 'w', encoding='utf-8') as f:
                        json.dump(result, f, ensure_ascii=False, indent=2)
                        
                except Exception as e:
                    error_result = {
                        "task_id": task_file.stem,
                        "status": "error",
                        "errors": [f"Failed to process task: {str(e)}"]
                    }
                    summary["tasks"].append(error_result)
                    summary["failed"] += 1
        
        # Save summary
        summary_file = self.results_dir / "task_processing_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
            
        return summary
    
    def print_summary(self, summary: Dict[str, Any]):
        """Print a formatted summary of task processing"""
        print("=== FlowAgent Task Processing Summary ===")
        print(f"Processing time: {summary['processing_time']}")
        print(f"Total tasks: {summary['total_tasks']}")
        print(f"Passed: {summary['passed']}")
        print(f"Failed: {summary['failed']}")
        print()
        
        for task in summary["tasks"]:
            status_icon = "✓" if task["status"] == "passed" else "✗"
            print(f"{status_icon} {task['task_id']} - {task['status']}")
            
            if "checks" in task:
                for check in task["checks"]:
                    print(f"  {check}")
                    
            if "errors" in task:
                for error in task["errors"]:
                    print(f"  ✗ {error}")
            print()

def main():
    """Main entry point"""
    processor = TaskProcessor()
    
    print("FlowAgent Task Processor")
    print("Automatically receiving, parsing and validating code generation tasks...")
    print()
    
    summary = processor.process_all_tasks()
    processor.print_summary(summary)
    
    # Exit with appropriate code
    if summary["failed"] > 0:
        print("Some tasks failed validation!")
        sys.exit(1)
    else:
        print("All tasks passed validation!")
        sys.exit(0)

if __name__ == "__main__":
    main()