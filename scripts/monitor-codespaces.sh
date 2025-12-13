#!/bin/bash

# Codespace Monitoring Script
# This script checks the status of GitHub Codespaces and warns about approaching deletion

set -e

# Colors for output
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
WARNING_DAYS=7  # Warn if codespace will be deleted within this many days

echo -e "${BLUE}=== GitHub Codespaces Monitoring ===${NC}\n"

# Check if GitHub CLI is installed
if ! command -v gh &> /dev/null; then
    echo -e "${RED}Error: GitHub CLI (gh) is not installed.${NC}"
    echo "Please install it from: https://cli.github.com/"
    echo ""
    echo "Installation commands:"
    echo "  macOS:   brew install gh"
    echo "  Ubuntu:  sudo apt install gh"
    echo "  Windows: winget install --id GitHub.cli"
    exit 1
fi

# Check if user is authenticated
if ! gh auth status &> /dev/null; then
    echo -e "${RED}Error: Not authenticated with GitHub CLI.${NC}"
    echo "Please run: gh auth login"
    exit 1
fi

echo -e "${GREEN}✓ GitHub CLI is installed and authenticated${NC}\n"

# Get codespace list
echo "Fetching codespace information..."
CODESPACES=$(gh codespace list --json name,repository,state,gitStatus,lastUsedAt,createdAt 2>/dev/null)

if [ -z "$CODESPACES" ] || [ "$CODESPACES" = "[]" ]; then
    echo -e "${YELLOW}No codespaces found.${NC}"
    exit 0
fi

# Parse and display codespace information
echo -e "\n${BLUE}Current Codespaces:${NC}\n"

# Calculate current time
CURRENT_TIME=$(date +%s)

# Track warnings
WARNING_COUNT=0

# Process each codespace
echo "$CODESPACES" | jq -r '.[] | @json' | while read -r codespace; do
    NAME=$(echo "$codespace" | jq -r '.name')
    REPO=$(echo "$codespace" | jq -r '.repository')
    STATE=$(echo "$codespace" | jq -r '.state')
    LAST_USED=$(echo "$codespace" | jq -r '.lastUsedAt')
    CREATED=$(echo "$codespace" | jq -r '.createdAt')
    
    echo -e "${GREEN}Codespace:${NC} $NAME"
    echo -e "  Repository: $REPO"
    echo -e "  State: $STATE"
    
    if [ "$LAST_USED" != "null" ]; then
        LAST_USED_TS=$(date -d "$LAST_USED" +%s 2>/dev/null || date -j -f "%Y-%m-%dT%H:%M:%SZ" "$LAST_USED" +%s 2>/dev/null)
        if [ -n "$LAST_USED_TS" ]; then
            DAYS_SINCE_USED=$(( ($CURRENT_TIME - $LAST_USED_TS) / 86400 ))
            DAYS_UNTIL_DELETION=$((30 - $DAYS_SINCE_USED))
            
            echo -e "  Last used: $LAST_USED (${DAYS_SINCE_USED} days ago)"
            
            if [ $DAYS_UNTIL_DELETION -le 0 ]; then
                echo -e "  ${RED}⚠️  CRITICAL: May be deleted soon!${NC}"
                WARNING_COUNT=$((WARNING_COUNT + 1))
            elif [ $DAYS_UNTIL_DELETION -le $WARNING_DAYS ]; then
                echo -e "  ${YELLOW}⚠️  WARNING: Will be deleted in ~${DAYS_UNTIL_DELETION} days${NC}"
                WARNING_COUNT=$((WARNING_COUNT + 1))
            else
                echo -e "  ${GREEN}✓ Status: Safe (${DAYS_UNTIL_DELETION} days remaining)${NC}"
            fi
        fi
    else
        echo -e "  Last used: Never"
    fi
    
    echo ""
done

# Summary
echo -e "\n${BLUE}=== Summary ===${NC}"
TOTAL=$(echo "$CODESPACES" | jq '. | length')
echo "Total codespaces: $TOTAL"

if [ $WARNING_COUNT -gt 0 ]; then
    echo -e "${YELLOW}⚠️  $WARNING_COUNT codespace(s) require attention!${NC}\n"
    echo "Recommended actions:"
    echo "  1. Visit: https://github.com/codespaces"
    echo "  2. Connect to codespaces approaching deletion"
    echo "  3. Run: gh codespace code -c CODESPACE_NAME"
    echo "  4. Delete unused codespaces: gh codespace delete -c CODESPACE_NAME"
else
    echo -e "${GREEN}✓ All codespaces are active${NC}"
fi

echo ""
echo "For more information, see: CODESPACE_MANAGEMENT.md"
