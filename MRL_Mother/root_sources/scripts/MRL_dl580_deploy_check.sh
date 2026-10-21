#!/usr/bin/env bash
# MRL_DL580 自運行部署檢查 (Linux / bash)
# origin_signature=MrLiouWord
# DL580 為 MRL 內部母體自運行主節點；GitHub/Cloud Code 為鏡像與建構器；APFS/Batch072 為部署/備份鏈，非母體本體。
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MRL_HOME="${MRL_HOME:-$(cd "${SCRIPT_DIR}/.." && pwd)}"
MRL_PORT="${MRL_PORT:-8790}"
ORIGIN_SIGNATURE="MrLiouWord"

cd "${MRL_HOME}"

echo "MRL_DL580_DEPLOY_CHECK"
echo "origin_signature=${ORIGIN_SIGNATURE}"
echo "MRL_HOME=${MRL_HOME}"
echo "target_port=${MRL_PORT}"

FAIL=0
pass () { echo "PASS: $1"; }
fail () { echo "FAIL: $1"; FAIL=1; }

# 1. Node version
if command -v node >/dev/null 2>&1; then
  pass "node runtime present ($(node --version))"
else
  fail "node runtime not found on DL580 node"
fi

# 2. package.json
if [ -f "package.json" ]; then
  pass "package.json present"
else
  fail "package.json missing"
fi

# 3. MRL_RuntimeServer.js
if [ -f "MRL_RuntimeServer.js" ]; then
  pass "MRL_RuntimeServer.js present"
else
  fail "MRL_RuntimeServer.js missing"
fi

# 4. required docs
REQUIRED_DOCS=(
  "docs/MRL_完整態主權宣示_v1.md"
  "docs/MRL_中文正名與英文Adapter對照表_v1.md"
  "docs/MRL_四層同步映射表_v1.md"
  "docs/MRL_CloudCode工程建構規格_v1.md"
  "docs/MRL_DL580自運行部署規格_v1.md"
)
for d in "${REQUIRED_DOCS[@]}"; do
  if [ -f "$d" ]; then
    pass "doc present: $d"
  else
    fail "doc missing: $d"
  fi
done

# 5. deploy/dl580 scripts
REQUIRED_DEPLOY=(
  "deploy/dl580/README.md"
  "deploy/dl580/MRL_dl580_start.sh"
  "deploy/dl580/MRL_dl580_start.ps1"
  "deploy/dl580/MRL_systemd_service.template"
  "deploy/dl580/MRL_selfhosted_runner_notes.md"
)
for f in "${REQUIRED_DEPLOY[@]}"; do
  if [ -f "$f" ]; then
    pass "deploy file present: $f"
  else
    fail "deploy file missing: $f"
  fi
done

# 6. (optional) Health 檢查（若 Runtime 已長駐）
if command -v curl >/dev/null 2>&1; then
  if curl -fsS "http://127.0.0.1:${MRL_PORT}/health" >/dev/null 2>&1; then
    echo "INFO: health=reachable"
  else
    echo "INFO: health=not running (start with: bash deploy/dl580/MRL_dl580_start.sh)"
  fi
fi

if [ "$FAIL" -eq 0 ]; then
  echo "MRL_DL580_DEPLOY_CHECK_PASS"
  exit 0
else
  echo "MRL_DL580_DEPLOY_CHECK_FAIL"
  exit 1
fi
