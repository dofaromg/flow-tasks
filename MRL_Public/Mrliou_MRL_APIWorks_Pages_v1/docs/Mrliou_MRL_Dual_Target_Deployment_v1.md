# Mrliou MRL dual-target deployment v1

`origin_signature: MrLiouWord`

## Boundary

| Target | Build output | Responsibility |
| --- | --- | --- |
| Cloudflare Pages | `out/` | public shell, documentation, local receipt verification |
| Cloudflare Worker | `.open-next/worker.js` and `.open-next/assets` | dynamic Next routes and API execution |
| DL580 / customer BYOH | external to both public bundles | private runtime, weights and customer data |

## Expected dependency tree

```text
Next source + dynamic API routes
├── npm run build
│   ├── next build → .next/ validation
│   └── build:pages → out/ static public entry
│       └── verify:pages → exact inventory + SHA-256 + manifest
├── build:cloudflare → OpenNext → .open-next/worker.js + assets
│   └── middleware → exact-origin GET/OPTIONS CORS for /api/mrl/*
└── CI → source verification + Pages build + browser acceptance + artifact
```

Pages never substitutes for the Worker API. The Worker never publishes the
private MRL mother topology. A Pages build does not assert that a Worker version
has production traffic.

## Existing Pages project settings

The existing `flow-tasks` Pages project should use:

- build command: `npm run build`
- output directory: `out`
- repository root: `/`

The ordinary root build first validates the Next application and then creates
the isolated static output. The OpenNext Worker continues to use
`npm run build:cloudflare` and `wrangler.jsonc`.

`middleware.js` permits credential-free GET/OPTIONS browser access to MRL API
routes from the existing `flow-tasks.pages.dev` and `mrliouword.com` origins.
Additional exact origins can be supplied as a comma-separated
`MRL_PUBLIC_PAGES_ORIGINS` environment value. Wildcards and credentialed CORS
are deliberately unsupported.

## Evidence rules

The builder refuses an existing output directory. The verifier requires the
exact output inventory, rejects symbolic links, checks every non-checksum file
against `SHA256SUMS.txt`, and validates the generated manifest. Browser checks
must confirm that the page loads without console errors or horizontal overflow
and that local receipt validation works without network upload.
