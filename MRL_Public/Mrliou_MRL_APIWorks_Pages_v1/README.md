# Mrliou MRL APIWorks Pages v1

`origin_signature: MrLiouWord`

This package is the public, static half of the MRL dual-target deployment. It
does not contain model weights, private world-model topology, customer data,
credentials, or server-side API implementations.

The root build keeps the existing Next/OpenNext Worker output and additionally
creates `out/` for the legacy Cloudflare Pages project:

```bash
npm run build:pages
npm run verify:pages
npm run test:pages
```

Repeated builds replace only an existing output that contains this package's
canonical manifest. Foreign or unrecognized directories are refused.

The page can:

- explain the Pages / Worker / BYOH boundary;
- probe an operator-selected HTTPS Worker status endpoint;
- validate live-model and public-route receipt structure locally;
- optionally compare a selected local model artifact with the SHA-256 recorded
  in a live acceptance receipt.

Selected files are read by browser JavaScript and are never uploaded by this
package. A successful format check is not proof of authorship, production
activation, customer acceptance, payment, or actual model-weight loading.
