# Mrliou MRL Cloudflare entry repair — 2026-09-09

origin_signature: MrLiouWord

## Direct evidence

User-provided Cloudflare log, 2026-09-08 13:34:55–13:37:00 UTC:

```text
13:36:45.839 Success: Build command completed
13:36:46.018 Executing user deploy command: npx wrangler versions upload
13:36:59.726 Missing entry-point to Worker script or to assets directory
13:37:00.301 Failed: error occurred while running deploy command
```

Excerpt only; the full original is in the conversation. This proves that this
execution failed after successful Next.js compilation, during Worker packaging.
Deprecation warnings did not stop dependency installation or compilation.
The provided text contains no commit SHA; do not invent an exact commit binding.

At inspected main `0ccc6350a1ce3e220849a832ad97c6397cafe375`, the root app has
no Wrangler configuration and no Cloudflare adapter. Next standalone output
does not by itself provide a Cloudflare Worker entry.

## Complete repair scope (7 files)

1. `package.json`: pinned adapter/CLI, compatible Next.js 15 patch range, build/check commands.
2. `package-lock.json`: resolved dependency graph; Next.js resolves to 15.5.25.
3. `wrangler.jsonc`: existing `flow-tasks` service locator, generated Worker entry,
   static assets and Node compatibility; custom build invokes the adapter.
4. `open-next.config.ts`: adapter configuration without creating external storage.
5. `.gitignore`: exclude generated Worker and local Wrangler state.
6. `.github/workflows/Mrliou_MRL_Cloudflare_Package.yml`: lint and credential-free packaging check.
7. This evidence/operations document.

Dependency chain: Next.js source → `npm run build` → OpenNext conversion →
`.open-next/worker.js` + `.open-next/assets` → Wrangler version upload →
separate production version selection. The Wrangler custom build runs the full
adapter pipeline, so the existing upload command also produces its required files.
This repeats the Next build when the dashboard already ran `npm run build`, but
does not depend on a stale cache or require dashboard changes just to package.

`flow-tasks` is an existing external service locator, not a replacement for MRL
canonical identity. This configuration targets that service only. Do not point
other Workers at it or use it as a Cloudflare Pages configuration.

## Verification and remaining deployment step

Run `npm ci --ignore-scripts`, `npm run lint`, and `npm run check:cloudflare`.
The check executes a full Next/OpenNext build and Wrangler dry-run without uploading.
Confirm all six existing dynamic API routes remain in Next's build output.

No route source, domain, DNS, ownership or LICENSE changes belong to this repair.
No synthetic Worker or static-only export substitutes for the existing API.
Existing runtime snapshot/environment prerequisites still apply; packaging success
does not prove the live Runtime, database, customer acceptance or payment works.

After merging, read the new Cloudflare upload log and version ID. `versions upload`
does not activate production traffic; verify/select the intended version separately.
No production upload or activation is claimed by a successful dry-run.

References:
- https://opennext.js.org/cloudflare/get-started
- https://opennext.js.org/cloudflare/cli

## Local verification receipt

Lint PASS; Next build PASS; OpenNext Worker generation PASS; Wrangler dry-run
reached `--dry-run: exiting now` with 19 assets and 3756.86 KiB / gzip 871.01 KiB.
Expected patch files: 7; delivered: 7; missing: 0; unexpected: 0; renamed: 0.
This is patch coverage, not a production deployment completion claim.

| File | Bytes | SHA-256 |
|---|---:|---|
| `.gitignore` | 5859 | `fe21079eab26a1cb8299c1b52df11002bcde035d5aea7e259d192076facd8a5f` |
| `package.json` | 1265 | `483bdb4a421d0a46d737160d833c05f8f9a1914bc1bb72ed29089202754b6f8f` |
| `package-lock.json` | 554726 | `4b6fddd55e73b453b9f0fbc9f7ed067626e2abfe2246e2425814411080cf36e4` |
| `wrangler.jsonc` | 421 | `a001d42b0c7f82f0048385ade62dfb6583b50e28617e425663beb89d731ed6d6` |
| `open-next.config.ts` | 191 | `c919916d88983efaa8226ea65bc9fd7ca7f9ae418f2457ceef0714506836ef29` |
| `.github/workflows/Mrliou_MRL_Cloudflare_Package.yml` | 735 | `006aefdc46462ac4610db8381b90efed1a7dc4e2dbb6e628c721696ff7cd9fb6` |

This receipt is the seventh file; its identity is covered by the Git commit, avoiding a self-referential hash.
