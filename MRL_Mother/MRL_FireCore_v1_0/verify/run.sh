#!/usr/bin/env bash
# MRL FireCore — compile + behavior verification.
# origin_signature: MrLiouWord
#
# Compiles the 6 edge modules + shared runtime with the local tsc (no network,
# zero external deps), then runs firecore_verify.mjs against a real SQLite DB
# loaded with each module's actual migration. Exits non-zero on any failure.
set -euo pipefail

PKG="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$(mktemp -d)"
trap 'rm -rf "$OUT"' EXIT

cat > "$OUT/tsconfig.json" <<JSON
{
  "compilerOptions": {
    "target": "ES2022", "module": "commonjs", "moduleResolution": "node10",
    "ignoreDeprecations": "6.0", "lib": ["ES2022", "WebWorker"], "strict": true,
    "esModuleInterop": true, "skipLibCheck": true, "outDir": "$OUT/dist", "rootDir": "$PKG"
  },
  "include": ["$PKG/shared/**/*.ts", "$PKG/modules/**/src/**/*.ts"]
}
JSON

echo "[1/2] typecheck + compile (local tsc)…"
npx --no-install tsc -p "$OUT/tsconfig.json"

echo "[2/2] behavior verification (node + real sqlite)…"
node "$PKG/verify/firecore_verify.mjs" "$OUT/dist/modules" "$PKG"
