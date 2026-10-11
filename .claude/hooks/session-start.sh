#!/bin/bash
# SessionStart hook for Claude Code cloud sessions.
# origin_signature: MrLiouWord
#
# Installs the dependencies needed to run the repo's real checks
# (pytest + Flask for Python, ESLint/Jest/TypeScript for Node), so a
# session never has to fall back to stubs. Idempotent and non-interactive.
#
# If the environment's network policy blocks a package registry, the
# install is skipped with a clear notice instead of failing the session:
# allow package managers under the environment's Network access setting
# (https://code.claude.com/docs/en/cloud-environments#network-access).
set -euo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

cd "${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel)}"

reachable() {
  curl -sS -o /dev/null --max-time 15 "$1" >/dev/null 2>&1
}

blocked=()

# --- Python: root requirements (pytest, Flask, requests, PyYAML, ...) and app services
if reachable "https://pypi.org/simple/pip/"; then
  python3 -m pip install --quiet --disable-pip-version-check \
    -r requirements.txt \
    -r apps/module-a/requirements.txt \
    -r apps/orchestrator/requirements.txt
else
  blocked+=("pypi.org")
fi

# --- Node: root workspace (Next.js, ESLint, Jest, TypeScript, @types/node)
if reachable "https://registry.npmjs.org/"; then
  npm install --no-audit --no-fund --loglevel=error
else
  blocked+=("registry.npmjs.org")
fi

if [ "${#blocked[@]}" -gt 0 ]; then
  echo "SessionStart: package registries unreachable (${blocked[*]}); dependencies were NOT installed." \
       "Real Flask/pytest/npm checks cannot run until package managers are allowed in this" \
       "environment's Network access setting. Do not substitute stubs for real test results."
fi
