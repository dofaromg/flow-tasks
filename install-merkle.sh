#!/bin/bash
# Quick installation script for Merkle Signature System
# This script automates the setup process described in MERKLE_README.md

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=======================================${NC}"
echo -e "${BLUE}  Merkle Signature System Installer  ${NC}"
echo -e "${BLUE}=======================================${NC}"
echo ""

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${RED}Error: Not a git repository${NC}"
    exit 1
fi

# Step 1: Make merkle-sign.sh executable
echo -e "${YELLOW}Step 1: Making merkle-sign.sh executable...${NC}"
if [[ ! -f "merkle-sign.sh" ]]; then
    echo -e "${RED}Error: merkle-sign.sh not found${NC}"
    exit 1
fi
chmod +x merkle-sign.sh
echo -e "${GREEN}✓ merkle-sign.sh is now executable${NC}"
echo ""

# Step 2: Install pre-commit hook
echo -e "${YELLOW}Step 2: Installing pre-commit hook...${NC}"
if [[ ! -f "git-hooks/pre-commit" ]]; then
    echo -e "${RED}Error: git-hooks/pre-commit not found${NC}"
    exit 1
fi

if [[ -f ".git/hooks/pre-commit" ]]; then
    echo -e "${YELLOW}Warning: pre-commit hook already exists${NC}"
    read -p "Overwrite existing hook? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Skipping pre-commit hook installation${NC}"
    else
        cp git-hooks/pre-commit .git/hooks/pre-commit
        chmod +x .git/hooks/pre-commit
        echo -e "${GREEN}✓ Pre-commit hook installed and made executable${NC}"
    fi
else
    cp git-hooks/pre-commit .git/hooks/pre-commit
    chmod +x .git/hooks/pre-commit
    echo -e "${GREEN}✓ Pre-commit hook installed and made executable${NC}"
fi
echo ""

# Step 3: Verify GitHub Actions workflow
echo -e "${YELLOW}Step 3: Verifying GitHub Actions workflow...${NC}"
if [[ -f ".github/workflows/merkle-verify.yml" ]]; then
    echo -e "${GREEN}✓ GitHub Actions workflow file exists${NC}"
else
    echo -e "${RED}Warning: .github/workflows/merkle-verify.yml not found${NC}"
    echo -e "${YELLOW}Please ensure the workflow file is committed to the repository${NC}"
fi
echo ""

# Step 4: Generate initial Merkle signature
echo -e "${YELLOW}Step 4: Generating initial Merkle signature...${NC}"
echo -e "${BLUE}This may take a moment for large repositories...${NC}"
if ./merkle-sign.sh full; then
    echo ""
    echo -e "${GREEN}✓ Merkle signature generated successfully${NC}"
    echo ""
    echo -e "${BLUE}Merkle Root:${NC}"
    cat .merkle/root.txt
    echo ""
    echo -e "${BLUE}Metadata:${NC}"
    if command -v jq &> /dev/null; then
        cat .merkle/metadata.json | jq .
    else
        cat .merkle/metadata.json
    fi
else
    echo -e "${RED}Error: Failed to generate Merkle signature${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}=======================================${NC}"
echo -e "${GREEN}  Installation Complete!${NC}"
echo -e "${GREEN}=======================================${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "1. The pre-commit hook is now active and will run on every commit"
echo "2. GitHub Actions will verify signatures on push/pull requests"
echo "3. Read MERKLE_README.md for more information"
echo ""
echo -e "${YELLOW}Note:${NC} The .merkle/ directory is excluded from git by default"
echo "      Only metadata files will be committed automatically"
echo ""
