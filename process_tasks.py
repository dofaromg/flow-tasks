#!/usr/bin/env python3
"""
Basic task processor for the flow-tasks system
Processes YAML task files and executes them
"""

import os
import yaml
import subprocess
import sys
from pathlib import Path

def load_task(task_file):
    """Load and parse a YAML task file"""
    try:
        with open(task_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Error loading task file {task_file}: {e}")
        return None

def process_task(task_data):
    """Process a single task"""
    if not task_data:
        return False
    
    task_id = task_data.get('task_id', 'unknown')
    language = task_data.get('language', '')
    description = task_data.get('description', '')
    target_file = task_data.get('target_file', '')
    
    print(f"Processing task: {task_id}")
    print(f"Language: {language}")
    print(f"Description: {description}")
    print(f"Target file: {target_file}")
    
    # Check if target file exists
    if target_file and os.path.exists(target_file):
        print(f"✓ Target file {target_file} exists")
        
        # If it's a Python file, try to run it
        if target_file.endswith('.py'):
            try:
                print(f"Testing Python file: {target_file}")
                # Use importlib to import the file directly, regardless of package structure
                import_script = (
                    "import importlib.util, sys; "
                    "spec = importlib.util.spec_from_file_location('test_module', sys.argv[1]); "
                    "module = importlib.util.module_from_spec(spec); "
                    "spec.loader.exec_module(module)"
                )
                result = subprocess.run(
                    [sys.executable, '-c', import_script, target_file],
                    capture_output=True, text=True, timeout=PYTHON_IMPORT_TIMEOUT
                )
                if result.returncode == 0:
                    print("✓ Python file imports successfully")
                else:
                    print(f"⚠ Python file has import issues: {result.stderr}")
            except Exception as e:
                print(f"⚠ Error testing Python file: {e}")
        
        return True
    else:
        print(f"✗ Target file {target_file} does not exist")
        return False

def main():
    """Main task processor function"""
    tasks_dir = Path("tasks")
    
    if not tasks_dir.exists():
        print("No tasks directory found")
        return
    
    # Find all YAML task files
    task_files = list(tasks_dir.glob("*.yaml")) + list(tasks_dir.glob("*.yml"))
    
    if not task_files:
        print("No task files found")
        return
    
    print(f"Found {len(task_files)} task file(s)")
    
    processed = 0
    successful = 0
    
    for task_file in task_files:
        print(f"\n{'='*50}")
        task_data = load_task(task_file)
        if process_task(task_data):
            successful += 1
        processed += 1
    
    print(f"\n{'='*50}")
    print(f"Task processing complete: {successful}/{processed} successful")

if __name__ == "__main__":
    main()