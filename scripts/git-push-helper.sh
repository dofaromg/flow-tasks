#!/bin/bash
# Git Push Helper Script
# Usage: ./scripts/git-push-helper.sh [branch-name]
#
# This script helps push changes to origin with proper validation

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get current branch name
CURRENT_BRANCH=$(git branch --show-current)
TARGET_BRANCH=${1:-$CURRENT_BRANCH}

echo -e "${GREEN}=== Git Push Helper ===${NC}"
echo -e "Target branch: ${YELLOW}${TARGET_BRANCH}${NC}"
echo ""

# Check if there are uncommitted changes
if [[ -n $(git status --porcelain) ]]; then
    echo -e "${RED}Error: You have uncommitted changes${NC}"
    echo "Please commit or stash your changes before pushing"
    git status --short
    exit 1
fi

# Check if branch exists
if ! git rev-parse --verify "$TARGET_BRANCH" >/dev/null 2>&1; then
    echo -e "${RED}Error: Branch '$TARGET_BRANCH' does not exist${NC}"
    exit 1
fi

# Check remote status
echo "Fetching remote status..."
if ! git fetch origin "$TARGET_BRANCH" 2>&1; then
    echo -e "${YELLOW}Warning: Could not fetch remote branch (may not exist yet)${NC}"
    echo -e "${YELLOW}Will attempt to push...${NC}"
    git push -u origin "$TARGET_BRANCH"
    echo -e "${GREEN}✓ Successfully pushed to origin/$TARGET_BRANCH${NC}"
    exit 0
fi

# Compare with remote
LOCAL=$(git rev-parse "$TARGET_BRANCH" 2>/dev/null || echo "")
REMOTE=$(git rev-parse "origin/$TARGET_BRANCH" 2>/dev/null || echo "")

if [ -z "$REMOTE" ]; then
    # Remote branch doesn't exist, push with upstream tracking
    echo -e "${YELLOW}Remote branch does not exist. Creating...${NC}"
    git push -u origin "$TARGET_BRANCH"
    echo -e "${GREEN}✓ Successfully pushed to origin/$TARGET_BRANCH${NC}"
elif [ "$LOCAL" = "$REMOTE" ]; then
    echo -e "${GREEN}✓ Branch is up to date with origin${NC}"
    echo "Nothing to push"
else
    echo -e "${YELLOW}Pushing changes to origin...${NC}"
    git push origin "$TARGET_BRANCH"
    echo -e "${GREEN}✓ Successfully pushed to origin/$TARGET_BRANCH${NC}"
fi

echo ""
echo -e "${GREEN}Done!${NC}"
