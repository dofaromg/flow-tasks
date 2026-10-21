#!/bin/bash
# 分支整合驗證腳本 (Branch Integration Validation Script)
# 在建立 PR 前執行此腳本以確保所有檢查通過
# Run this script before creating a PR to ensure all checks pass

set -e  # Exit on error

echo "=================================================="
echo "🔍 FlowAgent 分支整合驗證 (Branch Integration Check)"
echo "=================================================="
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print status
print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓ $2${NC}"
    else
        echo -e "${RED}✗ $2${NC}"
    fi
}

# Function to print section header
print_section() {
    echo ""
    echo -e "${BLUE}=== $1 ===${NC}"
    echo ""
}

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${RED}錯誤: 不在 Git 倉庫中 (Not in a Git repository)${NC}"
    exit 1
fi

# Get current branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo -e "當前分支 (Current branch): ${YELLOW}${CURRENT_BRANCH}${NC}"
echo ""

# 1. Check for uncommitted changes
print_section "檢查未提交的變更 (Checking for uncommitted changes)"
if ! git diff-index --quiet HEAD --; then
    echo -e "${YELLOW}⚠ 有未提交的變更 (Uncommitted changes detected)${NC}"
    git status --short
    read -p "是否繼續? (Continue? y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    print_status 0 "無未提交的變更 (No uncommitted changes)"
fi

# 2. Check if branch is up-to-date with origin/main
print_section "檢查分支是否最新 (Checking if branch is up-to-date)"
git fetch origin main --quiet 2>/dev/null || git fetch origin --quiet
if git show-ref --verify --quiet refs/remotes/origin/main; then
    BEHIND=$(git rev-list --count HEAD..origin/main 2>/dev/null || echo "0")
    if [ "$BEHIND" != "0" ] && [ $BEHIND -gt 0 ]; then
        echo -e "${YELLOW}⚠ 分支落後 origin/main $BEHIND 個提交 (Branch is $BEHIND commits behind origin/main)${NC}"
        echo "建議執行: git rebase origin/main (Recommended: git rebase origin/main)"
    else
        print_status 0 "分支是最新的 (Branch is up-to-date)"
    fi
else
    echo -e "${YELLOW}⚠ origin/main 不存在，跳過檢查 (origin/main not found, skipping check)${NC}"
fi

# 3. Check Python installation
print_section "檢查 Python 環境 (Checking Python environment)"
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    print_status 0 "Python 已安裝: $PYTHON_VERSION (Python installed)"
else
    print_status 1 "Python 未安裝 (Python not installed)"
    exit 1
fi

# 4. Install/Check dependencies
print_section "檢查 Python 依賴 (Checking Python dependencies)"
if [ -f "requirements.txt" ]; then
    echo "安裝依賴... (Installing dependencies...)"
    python3 -m pip install -q -r requirements.txt
    print_status $? "依賴安裝完成 (Dependencies installed)"
else
    echo -e "${YELLOW}⚠ requirements.txt 不存在 (requirements.txt not found)${NC}"
fi

# 5. Run Python syntax check
print_section "Python 語法檢查 (Python syntax check)"
echo "檢查 Python 檔案語法... (Checking Python file syntax...)"
SYNTAX_ERROR=0
for file in $(find . -name "*.py" -not -path "./venv/*" -not -path "./.venv/*" -not -path "*/__pycache__/*"); do
    if ! python3 -m py_compile "$file" 2>/dev/null; then
        echo -e "${RED}✗ 語法錯誤: $file${NC}"
        SYNTAX_ERROR=1
    fi
done
print_status $SYNTAX_ERROR "Python 語法檢查 (Python syntax check)"

# 6. Run tests
print_section "執行測試 (Running tests)"

# Check if test files exist
if [ -f "test_integration.py" ]; then
    echo "執行整合測試... (Running integration tests...)"
    if python3 test_integration.py > /tmp/test_integration.log 2>&1; then
        print_status 0 "整合測試通過 (Integration tests passed)"
    else
        print_status 1 "整合測試失敗 (Integration tests failed)"
        echo "查看日誌: /tmp/test_integration.log (See log: /tmp/test_integration.log)"
    fi
else
    echo -e "${YELLOW}⚠ test_integration.py 不存在 (test_integration.py not found)${NC}"
fi

if [ -f "test_comprehensive.py" ]; then
    echo "執行綜合測試... (Running comprehensive tests...)"
    if python3 test_comprehensive.py > /tmp/test_comprehensive.log 2>&1; then
        print_status 0 "綜合測試通過 (Comprehensive tests passed)"
    else
        print_status 1 "綜合測試失敗 (Comprehensive tests failed)"
        echo "查看日誌: /tmp/test_comprehensive.log (See log: /tmp/test_comprehensive.log)"
    fi
else
    echo -e "${YELLOW}⚠ test_comprehensive.py 不存在 (test_comprehensive.py not found)${NC}"
fi

# 7. Validate Kubernetes manifests
print_section "驗證 Kubernetes 配置 (Validating Kubernetes manifests)"
if command -v kustomize &> /dev/null; then
    if [ -d "cluster/overlays/prod" ]; then
        echo "建置生產環境配置... (Building production manifests...)"
        if kustomize build cluster/overlays/prod > /tmp/prod-manifests.yaml 2>&1; then
            print_status 0 "Kustomize 建置成功 (Kustomize build successful)"
            
            # Validate YAML syntax
            if python3 -c "import yaml; yaml.safe_load(open('/tmp/prod-manifests.yaml'))" 2>/dev/null; then
                print_status 0 "YAML 語法有效 (YAML syntax valid)"
            else
                print_status 1 "YAML 語法無效 (YAML syntax invalid)"
            fi
        else
            print_status 1 "Kustomize 建置失敗 (Kustomize build failed)"
        fi
    else
        echo -e "${YELLOW}⚠ cluster/overlays/prod 目錄不存在 (Directory not found)${NC}"
    fi
else
    echo -e "${YELLOW}⚠ kustomize 未安裝 (kustomize not installed)${NC}"
    echo "安裝方法 (Installation): curl -s \"https://raw.githubusercontent.com/kubernetes-sigs/kustomize/master/hack/install_kustomize.sh\" | bash"
fi

# 8. Check Docker files if they exist
print_section "檢查 Docker 配置 (Checking Docker configuration)"
DOCKERFILE_COUNT=0
for dockerfile in $(find apps -name "Dockerfile" 2>/dev/null); do
    DOCKERFILE_COUNT=$((DOCKERFILE_COUNT + 1))
    echo "找到 Dockerfile: $dockerfile (Found Dockerfile: $dockerfile)"
done

if [ $DOCKERFILE_COUNT -gt 0 ]; then
    print_status 0 "找到 $DOCKERFILE_COUNT 個 Dockerfile (Found $DOCKERFILE_COUNT Dockerfiles)"
else
    echo -e "${YELLOW}⚠ 未找到 Dockerfile (No Dockerfiles found)${NC}"
fi

# 9. Check for large files
print_section "檢查大型檔案 (Checking for large files)"
LARGE_FILES=$(find . -type f -size +10M -not -path "./.git/*" -not -path "./venv/*" 2>/dev/null)
if [ -z "$LARGE_FILES" ]; then
    print_status 0 "無大型檔案 (No large files)"
else
    echo -e "${YELLOW}⚠ 發現大型檔案 (>10MB): (Large files found)${NC}"
    echo "$LARGE_FILES"
fi

# 10. Summary
print_section "驗證摘要 (Validation Summary)"
echo ""
echo -e "${GREEN}✓ 基本檢查完成 (Basic checks completed)${NC}"
echo ""
echo "建議的下一步 (Recommended next steps):"
echo "1. 審查所有輸出和警告 (Review all output and warnings)"
echo "2. 確保所有測試通過 (Ensure all tests pass)"
echo "3. 建立 Pull Request (Create Pull Request)"
echo "4. 等待自動化 CI/CD 檢查 (Wait for automated CI/CD checks)"
echo ""
echo -e "${BLUE}=================================================="
echo "驗證完成 (Validation Complete)"
echo "==================================================${NC}"
