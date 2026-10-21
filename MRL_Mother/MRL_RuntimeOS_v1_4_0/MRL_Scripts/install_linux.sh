#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/.."
node --version
npm install --no-audit --no-fund
npm run acceptance
