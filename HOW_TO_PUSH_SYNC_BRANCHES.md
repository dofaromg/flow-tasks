# How to Push Sync Branches - Quick Guide

## What Was Requested

```bash
git push origin sync-mqm-記憶
git push origin sync-mqm-宥麟
git push origin sync-mqm-劉
# Then create PRs on GitHub
```

## The Problem

❌ **These branches don't exist** - they were created in a previous session  
❌ **Target branches (記憶, 宥麟, 劉) don't exist** in the repository  
❌ **Can't push directly** - authentication issues in this environment

## The Solution

Since the branches don't exist, we need to create them first. Here's the **simplest approach**:

### ✅ Quick Solution: Create Branches from PR #328

PR #328 already contains the complete Memory Quick Mount (MQM) module. Just create the target branches directly from it:

```bash
# Run the automated script
bash scripts/create_branches_from_pr328.sh
```

This script will:
1. Create 記憶, 宥麟, 劉 branches from PR #328
2. Each branch will have the complete MQM module
3. Attempt to push them to remote (requires GitHub authentication)

**Result**: Three branches ready to use, each with MQM module included!

### 📋 What's in These Branches?

Each branch (記憶, 宥麟, 劉) will contain:

- ✅ `particle_core/src/memory_quick_mount.py` (568 lines) - Main module
- ✅ `particle_core/src/test_memory_quick_mount.py` (495 lines) - Tests
- ✅ `particle_core/docs/memory_quick_mount.md` (686 lines) - Documentation
- ✅ `particle_core/config/mqm_config.yaml` - Configuration
- ✅ `particle_core/examples/memory_seed_example.json` - Examples
- ✅ Updated `.gitignore` for MQM runtime directories

**Total**: ~1,800 lines of MQM module code per branch

### 🔐 Authentication Required

The repository owner needs to run the script with proper GitHub credentials because:
- This environment can't authenticate with GitHub directly
- Need push access to create branches in the repository

## Alternative Approaches

### Option 2: Traditional Sync (If Target Branches Already Exist)

If 記憶, 宥麟, 劉 branches should already exist:

```bash
# 1. Recreate sync branches
bash scripts/sync_mqm_to_branches.sh

# 2. Push sync branches and create PRs
bash scripts/push_sync_branches_and_create_prs.sh
```

### Option 3: Manual GitHub Web Interface

1. Go to GitHub: https://github.com/dofaromg/flow-tasks
2. Click "Branch: main" dropdown
3. Find branch `copilot/add-memory-quick-mount-module`
4. Click the three dots menu → Create branch from here
5. Name it 記憶, then repeat for 宥麟 and 劉

### Option 4: Using GitHub CLI

If you have `gh` CLI installed:

```bash
# Create branches via API
gh api repos/dofaromg/flow-tasks/git/refs \
  -f ref='refs/heads/記憶' \
  -f sha=$(git rev-parse origin/copilot/add-memory-quick-mount-module)

gh api repos/dofaromg/flow-tasks/git/refs \
  -f ref='refs/heads/宥麟' \
  -f sha=$(git rev-parse origin/copilot/add-memory-quick-mount-module)

gh api repos/dofaromg/flow-tasks/git/refs \
  -f ref='refs/heads/劉' \
  -f sha=$(git rev-parse origin/copilot/add-memory-quick-mount-module)
```

## Verification

After creating branches, verify they exist:

```bash
# List all branches
git branch -a | grep -E '記憶|宥麟|劉'

# Or check on GitHub
# https://github.com/dofaromg/flow-tasks/branches
```

## What Happens Next?

Once branches are created:

1. ✅ Each branch has the MQM module
2. ✅ No sync needed (module already included)
3. ✅ Branches ready for development
4. ✅ Can create PRs if needed to merge back to main

## Need Help?

See detailed documentation:
- `SYNC_BRANCHES_STATUS.md` - Complete situation analysis
- `README_SYNC.md` - Full synchronization guide
- `docs/SYNC_PR328_TO_BRANCHES.md` - Detailed Chinese guide

## Summary

**Current Status**: Branches need to be created  
**Solution**: Run `bash scripts/create_branches_from_pr328.sh` with GitHub auth  
**Result**: Three branches (記憶, 宥麟, 劉) with MQM module ready to use

---

**Note**: This is a simplified guide. For complete technical details, see `SYNC_BRANCHES_STATUS.md`.
