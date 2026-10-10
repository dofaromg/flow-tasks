#!/usr/bin/env bash
# vector-attention-engine — compile + behavior verification. origin_signature: MrLiouWord
set -euo pipefail
PKG="$(cd "$(dirname "$0")/.." && pwd)"; OUT="$(mktemp -d)"; trap 'rm -rf "$OUT"' EXIT
cat > "$OUT/tsconfig.json" <<JSON
{ "compilerOptions": { "target":"ES2022","module":"commonjs","moduleResolution":"node10","ignoreDeprecations":"6.0","lib":["ES2022","WebWorker"],"strict":true,"esModuleInterop":true,"skipLibCheck":true,"outDir":"$OUT/dist","rootDir":"$PKG/src" }, "include":["$PKG/src/**/*.ts","$PKG/env.d.ts"] }
JSON
echo "[1/2] typecheck + compile…"; npx --no-install tsc -p "$OUT/tsconfig.json"
echo "[2/2] behavior verification…"; node "$PKG/verify/vector_verify.mjs" "$OUT/dist"
