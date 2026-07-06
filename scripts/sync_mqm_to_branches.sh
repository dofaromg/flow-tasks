#!/bin/bash

# Sync Memory Quick Mount (MQM) module from PR #328 to other branches
# Usage: ./sync_mqm_to_branches.sh [branch_name]
# If no branch name provided, syncs to all target branches

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Source branch containing MQM module
SOURCE_BRANCH="origin/copilot/add-memory-quick-mount-module"

# Target branches to sync to
TARGET_BRANCHES=("記憶" "宥麟" "劉")

# MQM files to copy
MQM_FILES=(
    "particle_core/src/memory_quick_mount.py"
    "particle_core/src/test_memory_quick_mount.py"
    "particle_core/docs/memory_quick_mount.md"
    "particle_core/config/mqm_config.yaml"
    "particle_core/examples/memory_seed_example.json"
)

# .gitignore entries to add
GITIGNORE_ADDITIONS='
# Memory Quick Mount (MQM) runtime directories
context/
snapshots/
# Memory Quick Mount - Dynamic files
particle_core/context/
particle_core/snapshots/
particle_core/backups/
particle_core/cache/
/tmp/test_context/
/tmp/test_snapshots/
/tmp/test_cache/'

# Function to print colored messages
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to sync MQM to a specific branch
sync_to_branch() {
    local branch=$1
    local sync_branch="sync-mqm-${branch}"
    
    print_info "==================================="
    print_info "Syncing MQM to branch: ${branch}"
    print_info "==================================="
    
    # Check if branch exists
    if ! git show-ref --verify --quiet "refs/remotes/origin/${branch}"; then
        print_error "Branch origin/${branch} does not exist. Skipping."
        return 1
    fi
    
    # Create temporary sync branch
    print_info "Creating sync branch: ${sync_branch}"
    git checkout -b "${sync_branch}" "origin/${branch}" 2>/dev/null || {
        print_warning "Branch ${sync_branch} already exists, using it..."
        git checkout "${sync_branch}"
        git reset --hard "origin/${branch}"
    }
    
    # Copy MQM files from source branch
    print_info "Copying MQM files from ${SOURCE_BRANCH}..."
    for file in "${MQM_FILES[@]}"; do
        if git ls-tree -r "${SOURCE_BRANCH}" "${file}" | grep -q "${file}"; then
            git checkout "${SOURCE_BRANCH}" -- "${file}"
            print_info "  ✓ Copied ${file}"
        else
            print_warning "  ✗ File ${file} not found in ${SOURCE_BRANCH}"
        fi
    done
    
    # Update .gitignore if needed
    print_info "Updating .gitignore..."
    if ! grep -q "Memory Quick Mount (MQM) runtime directories" .gitignore 2>/dev/null; then
        echo "${GITIGNORE_ADDITIONS}" >> .gitignore
        print_info "  ✓ Added MQM entries to .gitignore"
    else
        print_info "  ✓ .gitignore already contains MQM entries"
    fi
    
    # Check if there are changes to commit
    if git diff --cached --quiet && git diff --quiet; then
        print_warning "No changes to commit for branch ${branch}"
        git checkout -
        return 0
    fi
    
    # Stage all changes
    git add .
    
    # Commit changes
    print_info "Committing changes..."
    git commit -m "Synchronize Memory Quick Mount module from PR #328 to ${branch} branch

Added Memory Quick Mount (MQM) module for particle-based state management:
- particle_core/src/memory_quick_mount.py - Main MQM module
- particle_core/src/test_memory_quick_mount.py - Comprehensive test suite
- particle_core/docs/memory_quick_mount.md - Documentation
- particle_core/config/mqm_config.yaml - Configuration template
- particle_core/examples/memory_seed_example.json - Example seed file
- Updated .gitignore for MQM runtime directories

Synced from: ${SOURCE_BRANCH}
Target branch: ${branch}"
    
    print_info "✓ Successfully synced to ${sync_branch}"
    print_info ""
    print_info "To push to remote branch ${branch}, run:"
    echo "  git push origin ${sync_branch}:${branch}"
    print_info ""
    
    # Return to previous branch
    git checkout -
    
    return 0
}

# Main execution
main() {
    local target_branch=$1
    
    print_info "Memory Quick Mount (MQM) Module Synchronization"
    print_info "Source: ${SOURCE_BRANCH}"
    print_info ""
    
    # Save current branch
    ORIGINAL_BRANCH=$(git branch --show-current)
    
    if [ -n "${target_branch}" ]; then
        # Sync to specific branch
        print_info "Target: ${target_branch} (single branch mode)"
        sync_to_branch "${target_branch}"
    else
        # Sync to all target branches
        print_info "Target: All branches (${TARGET_BRANCHES[*]})"
        print_info ""
        
        for branch in "${TARGET_BRANCHES[@]}"; do
            sync_to_branch "${branch}" || print_error "Failed to sync to ${branch}"
            echo ""
        done
    fi
    
    # Return to original branch
    git checkout "${ORIGINAL_BRANCH}" 2>/dev/null || git checkout copilot/sync-other-branches
    
    print_info "==================================="
    print_info "Synchronization complete!"
    print_info "==================================="
    print_info ""
    print_info "Next steps:"
    print_info "1. Review the changes in the sync branches"
    print_info "2. Test the MQM module on each branch"
    print_info "3. Push the sync branches to remote:"
    for branch in "${TARGET_BRANCHES[@]}"; do
        echo "   git push origin sync-mqm-${branch}:${branch}"
    done
}

# Run main function
main "$@"
