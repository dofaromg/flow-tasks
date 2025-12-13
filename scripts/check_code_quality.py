#!/usr/bin/env python3
"""
Code Quality and Performance Pattern Checker
Scans Python files for common performance anti-patterns and suggests improvements
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple
from dataclasses import dataclass

@dataclass
class Issue:
    """Represents a code quality issue."""
    file_path: str
    line_number: int
    severity: str  # 'critical', 'high', 'medium', 'low'
    pattern: str
    description: str
    suggestion: str

class CodeQualityChecker:
    """Checks for performance anti-patterns in Python code."""
    
    def __init__(self, base_dir: str = "."):
        self.base_dir = Path(base_dir)
        self.issues: List[Issue] = []
        
        # Define patterns to detect
        self.patterns = {
            # Critical patterns
            # Match subprocess with f-string or format() which could allow injection
            r'subprocess\.(?:getoutput|call|Popen)\s*\(\s*f["\']': {
                'severity': 'critical',
                'pattern': 'subprocess with f-string interpolation',
                'description': 'Command injection vulnerability - user input in shell command',
                'suggestion': 'Use subprocess.run([list, of, args], ...) with argument list'
            },
            r'subprocess\.(?:getoutput|call|Popen)\s*\([^)]*\.format\(': {
                'severity': 'critical',
                'pattern': 'subprocess with .format() interpolation',
                'description': 'Potential command injection - string interpolation in shell command',
                'suggestion': 'Use subprocess.run with argument list instead of string formatting'
            },
            
            # High priority patterns
            # Note: rglob('*') is acceptable for ZIP operations with is_file() check
            # These patterns are commented out to reduce false positives
            # Uncomment and refine if needed for specific use cases
            
            # Medium priority patterns
            # More specific pattern: look for self.X_trace or self.X_history = []
            r'self\.(\w*(?:trace|history|log|events)\w*)\s*=\s*\[\]': {
                'severity': 'medium',
                'pattern': 'Unbounded list for traces/logs/history',
                'description': 'Potential memory leak with unbounded collection',
                'suggestion': 'Consider using deque(maxlen=N) for bounded memory'
            },
            r'copy\.deepcopy\([^)]+\).*\n.*copy\.deepcopy': {
                'severity': 'medium',
                'pattern': 'Multiple deepcopy calls',
                'description': 'Multiple deep copies can be expensive',
                'suggestion': 'Consider JSON round-trip or single copy'
            },
            
            # Low priority patterns
            # Note: Detecting repeated JSON serialization is complex and context-dependent
            # Removing this pattern to avoid false positives
            # Manual code review is more effective for this case
        }
    
    def check_file(self, file_path: Path) -> None:
        """Check a single Python file for issues."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
            
            # Check each pattern
            for pattern, info in self.patterns.items():
                matches = re.finditer(pattern, content, re.MULTILINE | re.IGNORECASE)
                for match in matches:
                    # Find line number
                    line_num = content[:match.start()].count('\n') + 1
                    
                    self.issues.append(Issue(
                        file_path=str(file_path.relative_to(self.base_dir)),
                        line_number=line_num,
                        severity=info['severity'],
                        pattern=info['pattern'],
                        description=info['description'],
                        suggestion=info['suggestion']
                    ))
        except Exception as e:
            print(f"Warning: Could not check {file_path}: {e}", file=sys.stderr)
    
    def check_directory(self, directory: Path = None) -> None:
        """Recursively check all Python files in directory."""
        if directory is None:
            directory = self.base_dir
        
        # Find all Python files
        python_files = list(directory.rglob("*.py"))
        
        # Filter out common excludes
        excludes = ['node_modules', '.git', '__pycache__', 'venv', 'env', '.venv']
        python_files = [
            f for f in python_files 
            if not any(exclude in f.parts for exclude in excludes)
        ]
        
        print(f"Checking {len(python_files)} Python files...")
        
        for py_file in python_files:
            self.check_file(py_file)
    
    def print_report(self) -> None:
        """Print a formatted report of issues found."""
        if not self.issues:
            print("\n✅ No performance anti-patterns detected!")
            print("Code quality checks passed.")
            return
        
        # Group issues by severity
        by_severity = {
            'critical': [i for i in self.issues if i.severity == 'critical'],
            'high': [i for i in self.issues if i.severity == 'high'],
            'medium': [i for i in self.issues if i.severity == 'medium'],
            'low': [i for i in self.issues if i.severity == 'low'],
        }
        
        print("\n" + "="*80)
        print("CODE QUALITY AND PERFORMANCE REPORT")
        print("="*80)
        
        severity_icons = {
            'critical': '🔴',
            'high': '🟠',
            'medium': '🟡',
            'low': '🟢'
        }
        
        total_issues = len(self.issues)
        print(f"\nTotal issues found: {total_issues}\n")
        
        for severity in ['critical', 'high', 'medium', 'low']:
            issues = by_severity[severity]
            if not issues:
                continue
            
            icon = severity_icons[severity]
            print(f"\n{icon} {severity.upper()} Priority ({len(issues)} issues)")
            print("-" * 80)
            
            for issue in issues:
                print(f"\nFile: {issue.file_path}")
                print(f"Line: {issue.line_number}")
                print(f"Pattern: {issue.pattern}")
                print(f"Issue: {issue.description}")
                print(f"Suggestion: {issue.suggestion}")
        
        print("\n" + "="*80)
        print(f"Summary: {total_issues} total issues")
        print(f"  🔴 Critical: {len(by_severity['critical'])}")
        print(f"  🟠 High: {len(by_severity['high'])}")
        print(f"  🟡 Medium: {len(by_severity['medium'])}")
        print(f"  🟢 Low: {len(by_severity['low'])}")
        print("="*80)
        
        if by_severity['critical']:
            print("\n⚠️  CRITICAL issues require immediate attention!")
            return 2  # Exit code 2 for critical issues
        elif by_severity['high']:
            print("\n⚠️  HIGH priority issues should be addressed soon.")
            return 1  # Exit code 1 for high priority issues
        else:
            print("\n✅ No critical or high priority issues found.")
            return 0  # Exit code 0 for success
    
    def generate_json_report(self, output_file: str = "code_quality_report.json") -> None:
        """Generate a JSON report of issues."""
        import json
        
        report = {
            "total_issues": len(self.issues),
            "by_severity": {
                "critical": len([i for i in self.issues if i.severity == 'critical']),
                "high": len([i for i in self.issues if i.severity == 'high']),
                "medium": len([i for i in self.issues if i.severity == 'medium']),
                "low": len([i for i in self.issues if i.severity == 'low']),
            },
            "issues": [
                {
                    "file": i.file_path,
                    "line": i.line_number,
                    "severity": i.severity,
                    "pattern": i.pattern,
                    "description": i.description,
                    "suggestion": i.suggestion
                }
                for i in self.issues
            ]
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\nJSON report saved to: {output_file}")

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Check code quality and performance patterns"
    )
    parser.add_argument(
        '--dir', '-d',
        default='.',
        help='Directory to scan (default: current directory)'
    )
    parser.add_argument(
        '--json', '-j',
        action='store_true',
        help='Generate JSON report'
    )
    parser.add_argument(
        '--output', '-o',
        default='code_quality_report.json',
        help='JSON report output file'
    )
    
    args = parser.parse_args()
    
    checker = CodeQualityChecker(args.dir)
    checker.check_directory()
    exit_code = checker.print_report()
    
    if args.json:
        checker.generate_json_report(args.output)
    
    sys.exit(exit_code or 0)

if __name__ == "__main__":
    main()
