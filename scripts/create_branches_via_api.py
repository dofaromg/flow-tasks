#!/usr/bin/env python3
"""
Create branches (記憶, 宥麟, 劉) from PR #328 using GitHub API

This script creates the target branches directly from the PR #328 branch
which contains the complete Memory Quick Mount (MQM) module.

Usage:
    python scripts/create_branches_via_api.py [--token YOUR_GITHUB_TOKEN]

The GitHub token can also be provided via GITHUB_TOKEN environment variable.
"""

import os
import sys
import argparse
import subprocess
import json

def run_command(cmd):
    """Run a shell command and return output"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {cmd}")
        print(f"Error: {e.stderr}")
        return None

def get_sha_for_branch(branch_name):
    """Get the SHA for a given branch"""
    cmd = f"git rev-parse origin/{branch_name}"
    sha = run_command(cmd)
    if sha:
        print(f"✓ Found SHA for {branch_name}: {sha[:8]}")
    else:
        print(f"✗ Could not find SHA for {branch_name}")
    return sha

def create_branch_via_api(owner, repo, branch_name, sha, token=None):
    """Create a branch using GitHub API"""
    url = f"https://api.github.com/repos/{owner}/{repo}/git/refs"
    
    data = {
        "ref": f"refs/heads/{branch_name}",
        "sha": sha
    }
    
    # Use curl for simplicity
    headers = ["-H", "Accept: application/vnd.github.v3+json"]
    if token:
        headers.extend(["-H", f"Authorization: token {token}"])
    
    cmd = [
        "curl", "-s", "-X", "POST", url,
        *headers,
        "-d", json.dumps(data)
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False
        )
        
        response = json.loads(result.stdout)
        
        if "ref" in response:
            print(f"✓ Successfully created branch: {branch_name}")
            return True
        elif "message" in response:
            if "already exists" in response["message"].lower():
                print(f"⚠ Branch {branch_name} already exists")
                return True
            else:
                print(f"✗ Failed to create {branch_name}: {response['message']}")
                return False
        else:
            print(f"✗ Unexpected response for {branch_name}: {result.stdout[:200]}")
            return False
            
    except Exception as e:
        print(f"✗ Error creating branch {branch_name}: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(
        description="Create target branches from PR #328 using GitHub API"
    )
    parser.add_argument(
        "--token",
        help="GitHub personal access token (or set GITHUB_TOKEN env var)"
    )
    parser.add_argument(
        "--owner",
        default="dofaromg",
        help="Repository owner (default: dofaromg)"
    )
    parser.add_argument(
        "--repo",
        default="flow-tasks",
        help="Repository name (default: flow-tasks)"
    )
    
    args = parser.parse_args()
    
    # Get token from argument or environment
    token = args.token or os.environ.get("GITHUB_TOKEN")
    
    if not token:
        print("⚠ Warning: No GitHub token provided.")
        print("   Branch creation may fail without authentication.")
        print("   Provide token via --token argument or GITHUB_TOKEN env var.")
        print()
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            print("Cancelled.")
            sys.exit(0)
    
    print("=" * 60)
    print("Creating Branches from PR #328 via GitHub API")
    print("=" * 60)
    print()
    
    # Configuration
    source_branch = "copilot/add-memory-quick-mount-module"
    target_branches = ["記憶", "宥麟", "劉"]
    
    # Get SHA of source branch
    print(f"Step 1: Getting SHA for {source_branch}...")
    sha = get_sha_for_branch(source_branch)
    
    if not sha:
        print(f"\n✗ Could not find source branch: {source_branch}")
        print("   Make sure you have fetched the latest branches.")
        sys.exit(1)
    
    print()
    print("Step 2: Creating target branches...")
    print(f"   Source SHA: {sha}")
    print(f"   Target branches: {', '.join(target_branches)}")
    print()
    
    # Create each branch
    success_count = 0
    for branch in target_branches:
        print(f"Creating branch: {branch}")
        if create_branch_via_api(args.owner, args.repo, branch, sha, token):
            success_count += 1
        print()
    
    # Summary
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"Successfully created: {success_count}/{len(target_branches)} branches")
    print()
    
    if success_count == len(target_branches):
        print("✓ All branches created successfully!")
        print()
        print("Each branch now contains the complete MQM module:")
        print("  - particle_core/src/memory_quick_mount.py")
        print("  - particle_core/src/test_memory_quick_mount.py")
        print("  - particle_core/docs/memory_quick_mount.md")
        print("  - particle_core/config/mqm_config.yaml")
        print("  - particle_core/examples/memory_seed_example.json")
        print()
        print("Verify at: https://github.com/dofaromg/flow-tasks/branches")
    else:
        print("⚠ Some branches failed to create.")
        print("  Check error messages above for details.")
        print("  You may need to provide a valid GitHub token.")
    
    print()

if __name__ == "__main__":
    main()
