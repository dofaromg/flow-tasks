#!/bin/bash

# Script to push sync branches and create PRs for PR #328 MQM synchronization
# This script should be run by the repository owner with proper GitHub credentials

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Configuration
SYNC_BRANCHES=("sync-mqm-記憶" "sync-mqm-宥麟" "sync-mqm-劉")
TARGET_BRANCHES=("記憶" "宥麟" "劉")
REPO_OWNER="dofaromg"
REPO_NAME="flow-tasks"

print_info "========================================"
print_info "PR #328 Sync Branch Push & PR Creation"
print_info "========================================"
echo ""

# Step 1: Check if sync branches exist
print_step "Step 1: Checking if sync branches exist locally..."
MISSING_BRANCHES=()
for branch in "${SYNC_BRANCHES[@]}"; do
    if git show-ref --verify --quiet "refs/heads/${branch}"; then
        print_info "✓ Branch ${branch} exists"
    else
        print_warning "✗ Branch ${branch} does not exist"
        MISSING_BRANCHES+=("${branch}")
    fi
done
echo ""

# If branches are missing, offer to recreate them
if [ ${#MISSING_BRANCHES[@]} -gt 0 ]; then
    print_warning "Some sync branches are missing."
    echo "Would you like to recreate them using the sync script? (y/n)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        print_info "Running sync script to recreate branches..."
        if [ -f "scripts/sync_mqm_to_branches.sh" ]; then
            bash scripts/sync_mqm_to_branches.sh
            echo ""
        else
            print_error "Sync script not found at scripts/sync_mqm_to_branches.sh"
            exit 1
        fi
    else
        print_error "Cannot proceed without sync branches. Please create them first."
        exit 1
    fi
fi

# Step 2: Push sync branches to remote
print_step "Step 2: Pushing sync branches to remote..."
echo "This will push the following branches:"
for i in "${!SYNC_BRANCHES[@]}"; do
    echo "  - ${SYNC_BRANCHES[$i]}"
done
echo ""
echo "Proceed with push? (y/n)"
read -r response

if [[ "$response" =~ ^[Yy]$ ]]; then
    for branch in "${SYNC_BRANCHES[@]}"; do
        print_info "Pushing ${branch}..."
        if git push origin "${branch}"; then
            print_info "✓ Successfully pushed ${branch}"
        else
            print_error "✗ Failed to push ${branch}"
            exit 1
        fi
    done
    echo ""
    print_info "All sync branches pushed successfully!"
else
    print_warning "Skipping branch push."
    exit 0
fi
echo ""

# Step 3: Create Pull Requests
print_step "Step 3: Creating Pull Requests..."
echo "This will create PRs for each sync branch to merge into target branches."
echo ""

# Check if gh CLI is available
if command -v gh &> /dev/null; then
    print_info "GitHub CLI (gh) detected. Creating PRs..."
    echo ""
    
    for i in "${!SYNC_BRANCHES[@]}"; do
        sync_branch="${SYNC_BRANCHES[$i]}"
        target_branch="${TARGET_BRANCHES[$i]}"
        
        print_info "Creating PR: ${sync_branch} → ${target_branch}"
        
        # Create PR using gh CLI
        if gh pr create \
            --repo "${REPO_OWNER}/${REPO_NAME}" \
            --base "${target_branch}" \
            --head "${sync_branch}" \
            --title "同步 Memory Quick Mount 模組到 ${target_branch} 分支" \
            --body "此 PR 從 PR #328 同步 Memory Quick Mount (MQM) 模組到 ${target_branch} 分支。

## 變更內容

- \`particle_core/src/memory_quick_mount.py\` (568 行) - 主模組
- \`particle_core/src/test_memory_quick_mount.py\` (495 行) - 測試套件
- \`particle_core/docs/memory_quick_mount.md\` (686 行) - 雙語文檔
- \`particle_core/config/mqm_config.yaml\` (4 行) - 配置範本
- \`particle_core/examples/memory_seed_example.json\` (17 行) - 範例檔案
- 更新 \`.gitignore\` 以包含 MQM 運行時目錄

## MQM 模組功能

- ⚡ 粒子級數據壓縮
- 💾 記憶種子掛載
- 📸 代理狀態快照
- 🔄 狀態再水化
- 🚀 緩存集成

## 測試

請在合併前運行：
\`\`\`bash
python particle_core/src/test_memory_quick_mount.py
\`\`\`

來源: PR #328 (copilot/add-memory-quick-mount-module)
"; then
            print_info "✓ PR created for ${sync_branch} → ${target_branch}"
        else
            print_warning "✗ Failed to create PR or PR already exists for ${sync_branch}"
        fi
        echo ""
    done
    
    print_info "✓ All PRs created (or already exist)"
else
    print_warning "GitHub CLI (gh) not found."
    print_info "Please create PRs manually or install gh CLI:"
    print_info "  https://cli.github.com/"
    echo ""
    print_info "Manual PR creation commands:"
    for i in "${!SYNC_BRANCHES[@]}"; do
        sync_branch="${SYNC_BRANCHES[$i]}"
        target_branch="${TARGET_BRANCHES[$i]}"
        echo "  gh pr create --base ${target_branch} --head ${sync_branch} \\"
        echo "    --title '同步 Memory Quick Mount 模組到 ${target_branch} 分支'"
    done
    echo ""
    print_info "Or create PRs via GitHub web interface:"
    for i in "${!SYNC_BRANCHES[@]}"; do
        sync_branch="${SYNC_BRANCHES[$i]}"
        target_branch="${TARGET_BRANCHES[$i]}"
        echo "  https://github.com/${REPO_OWNER}/${REPO_NAME}/compare/${target_branch}...${sync_branch}"
    done
fi

echo ""
print_info "========================================"
print_info "✓ Process Complete"
print_info "========================================"
echo ""
print_info "Summary:"
print_info "  - Sync branches pushed to remote"
print_info "  - PRs created (or instructions provided)"
print_info ""
print_info "Next steps:"
print_info "  1. Review the PRs on GitHub"
print_info "  2. Run tests on each branch"
print_info "  3. Merge when ready"
