#!/bin/bash

# Quick Codespace Retention Check Script
# Shows a simple summary of codespace retention status

set -e

# Check if GitHub CLI is installed
if ! command -v gh &> /dev/null; then
    echo "GitHub CLI not installed. Install from: https://cli.github.com/"
    exit 1
fi

# Check authentication
if ! gh auth status &> /dev/null; then
    echo "Not authenticated. Run: gh auth login"
    exit 1
fi

echo "Checking codespace retention status..."
echo ""

# List codespaces with retention information
gh codespace list --json name,repository,state,lastUsedAt | jq -r '
  .[] | 
  "Name: \(.name)\n  Repository: \(.repository)\n  State: \(.state)\n  Last used: \(.lastUsedAt // "Never")\n"
'

echo ""
echo "Quick Actions:"
echo "  • Connect to codespace: gh codespace code -c CODESPACE_NAME"
echo "  • Delete codespace:     gh codespace delete -c CODESPACE_NAME"
echo "  • View all codespaces:  https://github.com/codespaces"
echo ""
echo "See CODESPACE_MANAGEMENT.md for detailed guidance."
