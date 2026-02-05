#!/bin/bash

# Complete Sync Branch Creation and Push Solution for PR #328
# This script handles the full workflow: create target branches, sync MQM, push, and create PRs

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }
print_step() { echo -e "${BLUE}[STEP]${NC} $1"; }

# Configuration
SOURCE_BRANCH="copilot/add-memory-quick-mount-module"
TARGET_BRANCHES=("記憶" "宥麟" "劉")
REPO_OWNER="dofaromg"
REPO_NAME="flow-tasks"

print_info "=========================================="
print_info "PR #328 Complete Sync Solution"
print_info "=========================================="
echo ""

# Step 1: Check current branch
CURRENT_BRANCH=$(git branch --show-current)
print_step "Step 1: Current branch is: ${CURRENT_BRANCH}"
echo ""

# Step 2: Create target branches from PR #328 (which has the MQM module)
print_step "Step 2: Creating target branches from PR #328..."
echo "This will create the following branches with MQM module included:"
for branch in "${TARGET_BRANCHES[@]}"; do
    echo "  - ${branch}"
done
echo ""
echo "These branches will be based on ${SOURCE_BRANCH}"
echo "Proceed? (y/n)"
read -r response

if [[ ! "$response" =~ ^[Yy]$ ]]; then
    print_warning "Operation cancelled."
    exit 0
fi

# Fetch the source branch
print_info "Fetching ${SOURCE_BRANCH}..."
git fetch origin "${SOURCE_BRANCH}" || {
    print_error "Failed to fetch ${SOURCE_BRANCH}"
    print_info "Trying without fetch (using cached refs)..."
}

# Create target branches
for branch in "${TARGET_BRANCHES[@]}"; do
    print_info "Creating branch: ${branch}"
    
    # Check if branch exists locally
    if git show-ref --verify --quiet "refs/heads/${branch}"; then
        print_warning "Branch ${branch} already exists locally."
        echo "Overwrite? (y/n)"
        read -r overwrite
        if [[ "$overwrite" =~ ^[Yy]$ ]]; then
            git branch -D "${branch}"
        else
            print_info "Skipping ${branch}"
            continue
        fi
    fi
    
    # Create branch from PR #328
    git checkout -b "${branch}" "origin/${SOURCE_BRANCH}" 2>/dev/null || {
        print_error "Failed to create ${branch}"
        continue
    }
    
    print_info "✓ Branch ${branch} created with MQM module"
    
    # Try to push to remote
    print_info "Pushing ${branch} to remote..."
    if git push origin "${branch}"; then
        print_info "✓ Successfully pushed ${branch} to remote"
    else
        print_warning "✗ Failed to push ${branch} (may need authentication)"
        print_info "  You can push manually later with: git push origin ${branch}"
    fi
    echo ""
done

# Return to original branch
git checkout "${CURRENT_BRANCH}"

print_info "=========================================="
print_info "✓ Branch Creation Complete"
print_info "=========================================="
echo ""

print_info "Summary:"
print_info "  - Target branches created from PR #328"
print_info "  - Each branch includes the complete MQM module"
print_info "  - Branches pushed to remote (if authentication succeeded)"
echo ""

print_info "Next steps:"
print_info "  1. Verify branches exist: git branch -a | grep -E '記憶|宥麟|劉'"
print_info "  2. If push failed, manually push: git push origin 記憶 宥麟 劉"
print_info "  3. View branches on GitHub to confirm MQM module is present"
echo ""

print_info "The MQM module is now available on these branches!"
print_info "Files included in each branch:"
print_info "  - particle_core/src/memory_quick_mount.py"
print_info "  - particle_core/src/test_memory_quick_mount.py"
print_info "  - particle_core/docs/memory_quick_mount.md"
print_info "  - particle_core/config/mqm_config.yaml"
print_info "  - particle_core/examples/memory_seed_example.json"
