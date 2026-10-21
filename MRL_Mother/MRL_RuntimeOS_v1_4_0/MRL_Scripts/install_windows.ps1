Set-Location (Split-Path -Parent $PSScriptRoot)
node --version
npm install --no-audit --no-fund
npm run acceptance
