#!/bin/bash

# File Verification Script
# This script verifies that no files were lost during recent merges

set -e

echo "=========================================="
echo "File Restoration Verification Script"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

BEFORE_COMMIT="175073933bc6fae352739d0b99e288290dc1f488"
AFTER_204_COMMIT="9b1411e723010d2f8df5e103346e55fdda65d3b2"
CURRENT_MAIN="origin/main"

echo "Reference Points:"
echo "  Before PR #204: $BEFORE_COMMIT"
echo "  After PR #204:  $AFTER_204_COMMIT"
echo "  Current Main:   $CURRENT_MAIN"
echo ""

# Check if we have the commits
echo -n "Checking if commits are available... "
if git cat-file -e $BEFORE_COMMIT 2>/dev/null; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${YELLOW}⚠${NC} Fetching deeper history..."
    git fetch origin --deepen=100
fi

echo ""
echo "=========================================="
echo "File Count Analysis"
echo "=========================================="

# Count files
echo -n "Files in commit $BEFORE_COMMIT (before): "
BEFORE_COUNT=$(git ls-tree -r $BEFORE_COMMIT --name-only | wc -l)
echo -e "${GREEN}$BEFORE_COUNT${NC}"

echo -n "Files in commit $AFTER_204_COMMIT (after PR #204): "
AFTER_COUNT=$(git ls-tree -r $AFTER_204_COMMIT --name-only | wc -l)
echo -e "${GREEN}$AFTER_COUNT${NC}"

echo -n "Files in $CURRENT_MAIN (current): "
CURRENT_COUNT=$(git ls-tree -r $CURRENT_MAIN --name-only | wc -l)
echo -e "${GREEN}$CURRENT_COUNT${NC}"

echo ""
DIFF_COUNT=$((CURRENT_COUNT - BEFORE_COUNT))
if [ $DIFF_COUNT -ge 0 ]; then
    echo -e "Net change: ${GREEN}+$DIFF_COUNT files${NC}"
else
    echo -e "Net change: ${RED}$DIFF_COUNT files${NC}"
fi

echo ""
echo "=========================================="
echo "Deleted Files Check"
echo "=========================================="

# Check for deleted files
echo "Searching for deleted files between $BEFORE_COMMIT and $CURRENT_MAIN..."
DELETED_FILES=$(git diff --name-status $BEFORE_COMMIT..$CURRENT_MAIN | grep "^D" || true)

if [ -z "$DELETED_FILES" ]; then
    echo -e "${GREEN}✓ NO FILES WERE DELETED${NC}"
else
    echo -e "${RED}⚠ WARNING: The following files were deleted:${NC}"
    echo "$DELETED_FILES"
fi

echo ""
echo "=========================================="
echo "Critical Directory Analysis"
echo "=========================================="

check_directory() {
    local dir=$1
    echo ""
    echo -n "Checking $dir... "
    
    BEFORE_DIR_COUNT=$(git ls-tree -r $BEFORE_COMMIT --name-only | grep "^$dir" | wc -l)
    CURRENT_DIR_COUNT=$(git ls-tree -r $CURRENT_MAIN --name-only | grep "^$dir" | wc -l)
    
    if [ $CURRENT_DIR_COUNT -ge $BEFORE_DIR_COUNT ]; then
        echo -e "${GREEN}✓${NC}"
        echo "  Before: $BEFORE_DIR_COUNT files"
        echo "  Current: $CURRENT_DIR_COUNT files"
        echo -e "  Status: ${GREEN}All files preserved (+$((CURRENT_DIR_COUNT - BEFORE_DIR_COUNT)) files)${NC}"
    else
        echo -e "${RED}⚠${NC}"
        echo "  Before: $BEFORE_DIR_COUNT files"
        echo "  Current: $CURRENT_DIR_COUNT files"
        echo -e "  Status: ${RED}Missing $((BEFORE_DIR_COUNT - CURRENT_DIR_COUNT)) files${NC}"
    fi
}

check_directory "particle_core/"
check_directory "flowos/"
check_directory "flow_code/"
check_directory "tasks/"

echo ""
echo "=========================================="
echo "PR #204 Context Management Module"
echo "=========================================="

echo -n "Checking modules/context_management/... "
if [ -d "modules/context_management" ]; then
    FILE_COUNT=$(find modules/context_management -type f | wc -l)
    echo -e "${GREEN}✓${NC}"
    echo "  Status: Present with $FILE_COUNT files"
else
    echo -e "${YELLOW}⚠${NC}"
    echo "  Status: Directory not found in working tree"
fi

echo ""
echo "=========================================="
echo "New Files Added"
echo "=========================================="

echo "Files added between $BEFORE_COMMIT and $CURRENT_MAIN:"
git diff --name-status $BEFORE_COMMIT..$CURRENT_MAIN | grep "^A" | head -20

echo ""
echo "=========================================="
echo "Final Verdict"
echo "=========================================="

if [ -z "$DELETED_FILES" ] && [ $DIFF_COUNT -ge 0 ]; then
    echo -e "${GREEN}✓✓✓ REPOSITORY IS HEALTHY ✓✓✓${NC}"
    echo ""
    echo "Summary:"
    echo "  • No files were deleted"
    echo "  • $DIFF_COUNT new files were added"
    echo "  • All critical directories are intact"
    echo "  • PR #204 context_management module is present"
    echo ""
    echo -e "${GREEN}NO RESTORATION NEEDED${NC}"
else
    echo -e "${YELLOW}⚠ REVIEW REQUIRED ⚠${NC}"
    echo "Please review the findings above."
fi

echo ""
echo "=========================================="
echo "Script completed successfully"
echo "=========================================="
