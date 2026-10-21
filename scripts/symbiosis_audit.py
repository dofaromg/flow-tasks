#!/usr/bin/env python3
"""
RootLaw Symbiosis Audit Script
Verifies the integrity and consistency of the RootLaw Package absorption mapping.
"""

import argparse
import sys
from pathlib import Path


def check_absorption_map(map_file_path: Path) -> bool:
    """
    Verify the absorption map file exists and is valid.
    
    Args:
        map_file_path: Path to the Absorption_Map.md file
        
    Returns:
        True if checks pass, False otherwise
    """
    if not map_file_path.exists():
        print(f"❌ Error: Absorption map not found at {map_file_path}", file=sys.stderr)
        return False
    
    if not map_file_path.is_file():
        print(f"❌ Error: {map_file_path} is not a file", file=sys.stderr)
        return False
    
    # Read and validate content
    try:
        content = map_file_path.read_text(encoding='utf-8')
    except Exception as e:
        print(f"❌ Error reading {map_file_path}: {e}", file=sys.stderr)
        return False
    
    # Check for required sections
    required_sections = [
        "# Absorption Map",
        "## Purpose",
        "## Mapping Table"
    ]
    
    for section in required_sections:
        if section not in content:
            print(f"❌ Error: Missing required section '{section}' in absorption map", file=sys.stderr)
            return False
    
    # Check that RootLaws_v1.md is referenced
    if "RootLaws_v1.md" not in content:
        print("❌ Error: Absorption map does not reference RootLaws_v1.md", file=sys.stderr)
        return False
    
    # Check that laws 1-42 are referenced
    if "1–42" not in content and "1-42" not in content:
        print("❌ Warning: Absorption map does not clearly reference laws 1-42", file=sys.stderr)
    
    print(f"✅ Absorption map validated successfully: {map_file_path}")
    return True


def verify_rootlaw_file(rootlaw_dir: Path) -> bool:
    """
    Verify the RootLaws_v1.md file exists and has the expected structure.
    
    Args:
        rootlaw_dir: Directory containing the RootLaw package files
        
    Returns:
        True if checks pass, False otherwise
    """
    rootlaw_file = rootlaw_dir / "RootLaws_v1.md"
    
    if not rootlaw_file.exists():
        print(f"❌ Error: RootLaws_v1.md not found in {rootlaw_dir}", file=sys.stderr)
        return False
    
    try:
        content = rootlaw_file.read_text(encoding='utf-8')
    except Exception as e:
        print(f"❌ Error reading {rootlaw_file}: {e}", file=sys.stderr)
        return False
    
    import re
    
    # Count laws with Chinese numbering pattern (第N條)
    law_numbers = set()
    for match in re.finditer(r'第(\d+)條', content):
        law_numbers.add(int(match.group(1)))
    
    # Also check for simple numbered format (1. through 42.)
    if not law_numbers:
        for line in content.split('\n'):
            line = line.strip()
            if line.endswith('.') and line[:-1].isdigit():
                law_numbers.add(int(line[:-1]))
    
    # Verify all laws 1-42 are present
    expected_laws = set(range(1, 43))
    missing_laws = expected_laws - law_numbers
    
    if missing_laws:
        print(f"❌ Error: Missing laws in RootLaws_v1.md: {sorted(missing_laws)}", file=sys.stderr)
        return False
    
    print(f"✅ RootLaws_v1.md structure verified: All 42 laws present")
    return True


def check_related_files(rootlaw_dir: Path) -> bool:
    """
    Verify that related files referenced in the absorption map exist.
    
    Args:
        rootlaw_dir: Directory containing the RootLaw package files
        
    Returns:
        True if checks pass, False otherwise
    """
    required_files = [
        "RootLaws_v1.md",
        "Execution_Laws.md",
        "Evidence_Index.md",
        "Progress_Snapshot.md"
    ]
    
    all_exist = True
    for filename in required_files:
        filepath = rootlaw_dir / filename
        if not filepath.exists():
            print(f"⚠️  Warning: Expected file not found: {filepath}", file=sys.stderr)
            all_exist = False
        else:
            print(f"✅ Found: {filename}")
    
    return all_exist


def main():
    """Main entry point for the symbiosis audit."""
    parser = argparse.ArgumentParser(
        description="RootLaw Symbiosis Audit - Verify RootLaw Package integrity"
    )
    parser.add_argument(
        "--map",
        type=Path,
        required=True,
        help="Path to the Absorption_Map.md file"
    )
    
    args = parser.parse_args()
    
    # Get the RootLaw directory from the map file path
    rootlaw_dir = args.map.parent
    
    print("=" * 60)
    print("RootLaw Symbiosis Audit")
    print("=" * 60)
    print(f"RootLaw Directory: {rootlaw_dir}")
    print(f"Absorption Map: {args.map}")
    print()
    
    # Run all checks
    checks_passed = True
    
    print("🔍 Checking absorption map...")
    if not check_absorption_map(args.map):
        checks_passed = False
    print()
    
    print("🔍 Verifying RootLaws_v1.md structure...")
    if not verify_rootlaw_file(rootlaw_dir):
        checks_passed = False
    print()
    
    print("🔍 Checking related files...")
    if not check_related_files(rootlaw_dir):
        checks_passed = False
    print()
    
    # Final summary
    print("=" * 60)
    if checks_passed:
        print("✅ All symbiosis checks PASSED")
        print("=" * 60)
        return 0
    else:
        print("❌ Some symbiosis checks FAILED")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
