# Mrliou MRL Cloudflare production deploy repair — 2026-10-18

origin_signature: MrLiouWord

Follow-up to `Mrliou_MRL_Cloudflare_Entry_Repair_20260909.md`. That repair covered the
non-production path (`npx wrangler versions upload`). This one covers production.

## Direct evidence

User-provided Workers Builds logs, 2026-10-18, main `3464738`:
`flow-tasks` build `9b51d1d3-ca6a-4e28-8bec-c8dedf7226f5` (09:38:39–09:39:45 UTC) and
`mrlflow-tasks` build `3c116ffa-13b7-47e1-b4da-50251418efdb` (09:24:36–09:25:57 UTC).
Both end the same way:

```text
Executing user build command: npm run build
Success: Build command completed
Executing user deploy command: npx wrangler deploy
 ⛅️ wrangler 4.130.0
OpenNext project detected, calling `opennextjs-cloudflare deploy`
ERROR Could not find compiled Open Next config, did you run the build command?
Failed: error occurred while running deploy command
```

Excerpt only. `npm run build` is `next build`, which does not create `.open-next/`.
Wrangler delegates the deploy to OpenNext before the `wrangler.jsonc` custom build
(`npm run build:cloudflare`) runs; neither log contains that custom build.
Preview builds succeed because `versions upload` does run the custom build.

GitHub check runs on main since `478f9b9`: 7 of 19 production builds report success with
no change to `package.json`, `package-lock.json`, `wrangler.jsonc` or `open-next.config.ts`.
Why those succeeded is not recovered (待找回); no success log was provided.

## Repair (no dashboard change)

1. `scripts/Mrliou_MRL_opennext_build.mjs`: runs `opennextjs-cloudflare build` with the
   `MRL_OPENNEXT_BUILD=1` guard. With `--postbuild` it runs only when `WORKERS_CI=1`
   (Workers Builds default variable) and the guard is unset.
2. `package.json`: `postbuild` calls the script with `--postbuild`; `build:cloudflare`
   calls it without the flag. `build` stays `next build`.
3. `.github/workflows/Mrliou_MRL_Cloudflare_Package.yml`: also triggers on the script.

| Path | Result |
|---|---|
| Workers Builds production: `npm run build` → `wrangler deploy` | `next build`, then OpenNext build (its nested `npm run build` skips postbuild), `.open-next/` exists for `opennextjs-cloudflare deploy` |
| Workers Builds preview: `npm run build` → `wrangler versions upload` | Same build step; the custom build then packages again |
| Local, GitHub Actions, Docker, DL580: `npm run build` | `next build` only; postbuild exits 0 |
| `npm run build:cloudflare` / `check:cloudflare` | Same OpenNext build as before, with the guard |

No route, domain, DNS, service name, ownership or license change. The dashboard build and
deploy commands stay as they are.

## Verification

- Stub simulation of all paths: production builds `.open-next` once and terminates; preview
  custom build does not recurse; local build runs `next build` only; OpenNext failure exit 3
  propagates; missing `npx` exits 1 with the spawn error.
- `npm run lint` / `npm run build` were not run in the authoring session (npm registry
  unreachable there); `Mrliou_MRL_Cloudflare_Package` runs lint and the full
  Next/OpenNext build plus Wrangler dry-run on the PR.
- Production proof needs the post-merge `flow-tasks` and `mrlflow-tasks` logs: expect
  `MRL OpenNext build done` before `npx wrangler deploy`, then a deployed version for the
  merge commit. A dry-run or preview success does not prove production.

Rollback: restore the two `package.json` script lines; the script and this note are additive.
