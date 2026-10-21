#!/bin/bash
# Test script for Merkle Signature System
# Verifies that all components are properly installed and functional

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=======================================${NC}"
echo -e "${BLUE}  Merkle System Verification Test${NC}"
echo -e "${BLUE}=======================================${NC}"
echo ""

PASSED=0
FAILED=0

# Test 1: Check merkle-sign.sh exists and is executable
echo -e "${YELLOW}Test 1: Checking merkle-sign.sh...${NC}"
if [[ -x "merkle-sign.sh" ]]; then
    echo -e "${GREEN}✓ merkle-sign.sh exists and is executable${NC}"
    PASSED=$((PASSED + 1))
else
    echo -e "${RED}✗ merkle-sign.sh not found or not executable${NC}"
    FAILED=$((FAILED + 1))
fi
echo ""

# Test 2: Check git-hooks/pre-commit exists and is executable
echo -e "${YELLOW}Test 2: Checking git-hooks/pre-commit...${NC}"
if [[ -x "git-hooks/pre-commit" ]]; then
    echo -e "${GREEN}✓ git-hooks/pre-commit exists and is executable${NC}"
    PASSED=$((PASSED + 1))
else
    echo -e "${RED}✗ git-hooks/pre-commit not found or not executable${NC}"
    FAILED=$((FAILED + 1))
fi
echo ""

# Test 3: Check GitHub Actions workflow exists
echo -e "${YELLOW}Test 3: Checking GitHub Actions workflow...${NC}"
if [[ -f ".github/workflows/merkle-verify.yml" ]]; then
    echo -e "${GREEN}✓ .github/workflows/merkle-verify.yml exists${NC}"
    PASSED=$((PASSED + 1))
else
    echo -e "${RED}✗ .github/workflows/merkle-verify.yml not found${NC}"
    FAILED=$((FAILED + 1))
fi
echo ""

# Test 4: Check documentation exists
echo -e "${YELLOW}Test 4: Checking documentation...${NC}"
if [[ -f "MERKLE_README.md" ]]; then
    echo -e "${GREEN}✓ MERKLE_README.md exists${NC}"
    PASSED=$((PASSED + 1))
else
    echo -e "${RED}✗ MERKLE_README.md not found${NC}"
    FAILED=$((FAILED + 1))
fi
echo ""

# Test 5: Check installation script exists
echo -e "${YELLOW}Test 5: Checking installation script...${NC}"
if [[ -x "install-merkle.sh" ]]; then
    echo -e "${GREEN}✓ install-merkle.sh exists and is executable${NC}"
    PASSED=$((PASSED + 1))
else
    echo -e "${RED}✗ install-merkle.sh not found or not executable${NC}"
    FAILED=$((FAILED + 1))
fi
echo ""

# Test 6: Test merkle-sign.sh functionality
echo -e "${YELLOW}Test 6: Testing merkle-sign.sh functionality...${NC}"
if ./merkle-sign.sh incremental > /dev/null 2>&1; then
    if [[ -f ".merkle/root.txt" ]] && [[ -f ".merkle/metadata.json" ]]; then
        ROOT=$(cat .merkle/root.txt)
        if [[ "$ROOT" =~ ^[a-f0-9]{64}$ ]]; then
            echo -e "${GREEN}✓ merkle-sign.sh generates valid signatures${NC}"
            echo -e "  Root: $ROOT"
            PASSED=$((PASSED + 1))
        else
            echo -e "${RED}✗ Invalid root hash format${NC}"
            FAILED=$((FAILED + 1))
        fi
    else
        echo -e "${RED}✗ Output files not generated${NC}"
        FAILED=$((FAILED + 1))
    fi
else
    echo -e "${RED}✗ merkle-sign.sh execution failed${NC}"
    FAILED=$((FAILED + 1))
fi
echo ""

# Test 7: Validate metadata JSON
echo -e "${YELLOW}Test 7: Validating metadata JSON...${NC}"
if [[ -f ".merkle/metadata.json" ]]; then
    if python3 -c "import json; json.load(open('.merkle/metadata.json'))" 2>/dev/null; then
        echo -e "${GREEN}✓ Metadata JSON is valid${NC}"
        PASSED=$((PASSED + 1))
    else
        echo -e "${RED}✗ Metadata JSON is invalid${NC}"
        FAILED=$((FAILED + 1))
    fi
else
    echo -e "${RED}✗ Metadata file not found${NC}"
    FAILED=$((FAILED + 1))
fi
echo ""

# Test 8: Check if pre-commit hook is installed
echo -e "${YELLOW}Test 8: Checking pre-commit hook installation...${NC}"
if [[ -x ".git/hooks/pre-commit" ]]; then
    echo -e "${GREEN}✓ Pre-commit hook is installed${NC}"
    PASSED=$((PASSED + 1))
else
    echo -e "${YELLOW}⚠ Pre-commit hook not installed (run: cp git-hooks/pre-commit .git/hooks/pre-commit)${NC}"
    # Don't count as failure since it might not be installed yet
fi
echo ""

# Test 9: Validate GitHub Actions workflow YAML
echo -e "${YELLOW}Test 9: Validating GitHub Actions workflow YAML...${NC}"
if python3 -c "import yaml; yaml.safe_load(open('.github/workflows/merkle-verify.yml'))" 2>/dev/null; then
    echo -e "${GREEN}✓ Workflow YAML is valid${NC}"
    PASSED=$((PASSED + 1))
else
    echo -e "${RED}✗ Workflow YAML is invalid${NC}"
    FAILED=$((FAILED + 1))
fi
echo ""

# Summary
echo -e "${BLUE}=======================================${NC}"
echo -e "${BLUE}  Test Summary${NC}"
echo -e "${BLUE}=======================================${NC}"
echo -e "${GREEN}Passed: $PASSED${NC}"
if [[ $FAILED -gt 0 ]]; then
    echo -e "${RED}Failed: $FAILED${NC}"
    echo ""
    echo -e "${RED}Some tests failed. Please check the output above.${NC}"
    exit 1
else
    echo -e "${GREEN}Failed: 0${NC}"
    echo ""
    echo -e "${GREEN}All tests passed! The Merkle signature system is properly configured.${NC}"
    exit 0
fi
