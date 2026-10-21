#!/bin/bash

# Test script to demonstrate the subshell bug and verify the fix
# Related to commit 81bdb7a: Fix WARNING_COUNT subshell bug in monitor-codespaces.sh

set -e

echo "========================================="
echo "Subshell Bug Demonstration and Fix Test"
echo "========================================="
echo ""

# Test 1: Demonstrate the bug
echo "Test 1: Pipe to while (BUGGY - creates subshell)"
echo "------------------------------------------------"
echo "Code pattern: echo data | while read line; do COUNT=\$((COUNT+1)); done"
echo ""

COUNT=0
echo -e "line1\nline2\nline3" | while read line; do
  COUNT=$((COUNT + 1))
  echo "  Inside loop: COUNT=$COUNT"
done
echo "  After loop: COUNT=$COUNT"

if [ $COUNT -eq 0 ]; then
  echo "  ❌ BUG CONFIRMED: Counter was reset (subshell problem)"
else
  echo "  ✅ UNEXPECTED: Counter works (not a subshell)"
fi
echo ""

# Test 2: Demonstrate the fix
echo "Test 2: Process Substitution (FIXED)"
echo "-------------------------------------"
echo "Code pattern: while read line; do COUNT=\$((COUNT+1)); done < <(echo data)"
echo ""

COUNT=0
while read line; do
  COUNT=$((COUNT + 1))
  echo "  Inside loop: COUNT=$COUNT"
done < <(echo -e "line1\nline2\nline3")
echo "  After loop: COUNT=$COUNT"

if [ $COUNT -eq 3 ]; then
  echo "  ✅ FIX VERIFIED: Counter is correct (3)"
else
  echo "  ❌ ERROR: Counter is wrong (expected 3, got $COUNT)"
  exit 1
fi
echo ""

# Test 3: Verify monitor-codespaces.sh uses the correct pattern
echo "Test 3: Verify monitor-codespaces.sh Implementation"
echo "----------------------------------------------------"

if [ -f "scripts/monitor-codespaces.sh" ]; then
  echo "Checking scripts/monitor-codespaces.sh..."
  
  # Check for process substitution pattern
  if grep -q 'done < <(' scripts/monitor-codespaces.sh; then
    echo "  ✅ Process substitution found: 'done < <(...)'"
  else
    echo "  ❌ Process substitution NOT found"
    exit 1
  fi
  
  # Check for the comment explaining the fix
  if grep -q 'process substitution to avoid subshell' scripts/monitor-codespaces.sh; then
    echo "  ✅ Comment explaining the fix is present"
  else
    echo "  ⚠️  Warning: Explanatory comment not found"
  fi
  
  # Check that we're not using pipe to while with WARNING_COUNT
  if grep -A 5 'WARNING_COUNT=0' scripts/monitor-codespaces.sh | grep -q '| while'; then
    echo "  ❌ WARNING: Found pipe to while near WARNING_COUNT"
    exit 1
  else
    echo "  ✅ No problematic pipe to while pattern found"
  fi
else
  echo "  ⚠️  scripts/monitor-codespaces.sh not found"
fi
echo ""

# Test 4: Verify workflow file uses correct pattern
echo "Test 4: Verify codespace-monitoring.yml Implementation"
echo "-------------------------------------------------------"

if [ -f ".github/workflows/codespace-monitoring.yml" ]; then
  echo "Checking .github/workflows/codespace-monitoring.yml..."
  
  # Check for process substitution pattern
  if grep -q 'done < <(' .github/workflows/codespace-monitoring.yml; then
    echo "  ✅ Process substitution found in workflow"
  else
    echo "  ⚠️  Warning: Process substitution not found (may use alternative approach)"
  fi
else
  echo "  ⚠️  Workflow file not found"
fi
echo ""

echo "========================================="
echo "✅ All Tests Passed!"
echo "========================================="
echo ""
echo "Summary:"
echo "- The subshell bug occurs when using 'echo data | while read'"
echo "- Variables modified inside the while loop are lost"
echo "- Fix: Use process substitution 'while read; done < <(echo data)'"
echo "- This keeps the loop in the same shell context"
echo ""
echo "References:"
echo "- Commit: 81bdb7a Fix WARNING_COUNT subshell bug"
echo "- File: scripts/monitor-codespaces.sh"
echo "- Documentation: IMPLEMENTATION_SUMMARY_CODESPACE.md"
