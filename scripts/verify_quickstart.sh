#!/bin/bash
# FlowAgent Quick Start Verification Script
# 
# This script verifies that all quick start deployment methods are properly configured
# and ready to use.
#
# Usage: bash scripts/verify_quickstart.sh

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}FlowAgent Quick Start Verification${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Track overall status
ALL_CHECKS_PASSED=true

# Function to check file existence
check_file() {
    local file="$1"
    local description="$2"
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} $description"
        return 0
    else
        echo -e "${RED}✗${NC} $description (MISSING: $file)"
        ALL_CHECKS_PASSED=false
        return 1
    fi
}

# Function to check directory existence
check_dir() {
    local dir="$1"
    local description="$2"
    if [ -d "$dir" ]; then
        echo -e "${GREEN}✓${NC} $description"
        return 0
    else
        echo -e "${RED}✗${NC} $description (MISSING: $dir)"
        ALL_CHECKS_PASSED=false
        return 1
    fi
}

# Function to check command availability
check_command() {
    local cmd="$1"
    local description="$2"
    if command -v "$cmd" &> /dev/null; then
        local version=""
        case "$cmd" in
            kubectl)
                version=$(kubectl version --client 2>&1 | head -1 || echo "version unknown")
                ;;
            *)
                version=$($cmd --version 2>&1 | head -1 || echo "version unknown")
                ;;
        esac
        echo -e "${GREEN}✓${NC} $description ($version)"
        return 0
    else
        echo -e "${YELLOW}⚠${NC} $description (not installed - optional)"
        return 1
    fi
}

echo -e "${YELLOW}=== 1. GKE Deployment Files ===${NC}"
check_file "scripts/oneclick_gke_init.sh" "GKE initialization script"
check_dir "cluster/overlays/prod" "Production Kubernetes overlay"
check_file "cluster/overlays/prod/kustomization.yaml" "Production kustomization"
check_dir "cluster/base" "Kubernetes base configuration"
check_file "cluster/base/kustomization.yaml" "Base kustomization"
echo ""

echo -e "${YELLOW}=== 2. Docker Compose Deployment Files ===${NC}"
check_file "docker-compose.yml" "Docker Compose configuration"
check_file ".env.docker-example" "Environment variable example"
echo ""

echo -e "${YELLOW}=== 3. Application Deployments ===${NC}"
check_dir "apps/nextjs-frontend" "Next.js frontend application"
check_file "apps/nextjs-frontend/deployment.yaml" "Next.js Kubernetes deployment"
check_file "apps/nextjs-frontend/Dockerfile" "Next.js Dockerfile"
check_dir "apps/astro-frontend" "Astro frontend application"
check_file "apps/astro-frontend/deployment.yaml" "Astro Kubernetes deployment"
check_file "apps/astro-frontend/package.json" "Astro package.json"
check_dir "apps/mongodb" "MongoDB database"
check_file "apps/mongodb/deployment.yaml" "MongoDB Kubernetes deployment"
check_dir "apps/module-a" "Module-A service"
check_dir "apps/orchestrator" "Orchestrator service"
echo ""

echo -e "${YELLOW}=== 4. Particle Language Core ===${NC}"
check_dir "particle_core" "Particle core directory"
check_file "particle_core/demo.py" "Particle core demo"
check_file "particle_core/requirements.txt" "Particle core requirements"
check_dir "particle_core/src" "Particle core source files"
check_file "particle_core/src/logic_pipeline.py" "Logic pipeline module"
check_file "particle_core/src/cli_runner.py" "CLI runner module"
check_file "particle_core/src/rebuild_fn.py" "Function rebuilder module"
echo ""

echo -e "${YELLOW}=== 5. Root Python Files ===${NC}"
check_file "requirements.txt" "Root requirements.txt"
check_file ".env.example" "Environment variable example"
echo ""

echo -e "${YELLOW}=== 6. Documentation ===${NC}"
check_file "README.md" "Main README"
check_file "DEPLOYMENT.md" "Deployment guide"
check_file "DEPLOYMENT_QUICK_REFERENCE.md" "Quick reference"
check_file "DOCKER_COMPOSE_GUIDE.md" "Docker Compose guide"
echo ""

echo -e "${YELLOW}=== 7. Development Tools ===${NC}"
check_command "gcloud" "Google Cloud SDK" || true
check_command "kubectl" "Kubernetes CLI" || true
check_command "docker" "Docker" || true
check_command "docker-compose" "Docker Compose" || true
check_command "npm" "Node Package Manager" || true
check_command "python" "Python" || true
check_command "pip" "Python Package Manager" || true
echo ""

# YAML Validation
echo -e "${YELLOW}=== 8. Configuration Validation ===${NC}"
if command -v python &> /dev/null; then
    # Check docker-compose.yml
    if python -c "import yaml; yaml.safe_load(open('docker-compose.yml'))" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} docker-compose.yml is valid YAML"
    else
        echo -e "${RED}✗${NC} docker-compose.yml has YAML syntax errors"
        ALL_CHECKS_PASSED=false
    fi
    
    # Check kustomization files
    for kustomize_file in $(find cluster -name "kustomization.yaml" 2>/dev/null); do
        if python -c "import yaml; yaml.safe_load(open('$kustomize_file'))" 2>/dev/null; then
            echo -e "${GREEN}✓${NC} $kustomize_file is valid YAML"
        else
            echo -e "${RED}✗${NC} $kustomize_file has YAML syntax errors"
            ALL_CHECKS_PASSED=false
        fi
    done
else
    echo -e "${YELLOW}⚠${NC} Python not available, skipping YAML validation"
fi
echo ""

# Python Syntax Check
echo -e "${YELLOW}=== 9. Python Syntax Validation ===${NC}"
if command -v python &> /dev/null; then
    python_errors=0
    for py_file in particle_core/src/*.py; do
        if [ -f "$py_file" ]; then
            if python -m py_compile "$py_file" 2>/dev/null; then
                echo -e "${GREEN}✓${NC} $(basename $py_file) has valid Python syntax"
            else
                echo -e "${RED}✗${NC} $(basename $py_file) has Python syntax errors"
                python_errors=$((python_errors + 1))
                ALL_CHECKS_PASSED=false
            fi
        fi
    done
    
    if [ $python_errors -eq 0 ]; then
        echo -e "${GREEN}✓${NC} All Python files are syntactically valid"
    fi
else
    echo -e "${YELLOW}⚠${NC} Python not available, skipping syntax validation"
fi
echo ""

# Quick Start Instructions
echo -e "${BLUE}========================================${NC}"
if [ "$ALL_CHECKS_PASSED" = true ]; then
    echo -e "${GREEN}✓ All checks passed!${NC}"
    echo ""
    echo -e "${YELLOW}Quick Start Options:${NC}"
    echo ""
    echo "1. GKE Deployment (Production):"
    echo "   bash scripts/oneclick_gke_init.sh"
    echo "   kubectl apply -k cluster/overlays/prod/"
    echo ""
    echo "2. Docker Compose (Local):"
    echo "   cp .env.docker-example .env"
    echo "   docker-compose up -d"
    echo "   # Access: http://localhost:3000"
    echo ""
    echo "3. Astro Frontend (Local Development):"
    echo "   cd apps/astro-frontend"
    echo "   npm install"
    echo "   npm run dev"
    echo "   # Access: http://localhost:4321"
    echo ""
    echo "4. Particle Language Core (Local Development):"
    echo "   python -m venv .venv"
    echo "   source .venv/bin/activate  # Windows: .venv\\Scripts\\activate"
    echo "   pip install -r particle_core/requirements.txt"
    echo "   cd particle_core"
    echo "   python demo.py demo"
    echo ""
    exit 0
else
    echo -e "${RED}✗ Some checks failed!${NC}"
    echo ""
    echo "Please fix the missing files or configuration errors above."
    echo "Refer to the README.md for complete setup instructions."
    echo ""
    exit 1
fi
