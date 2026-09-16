# Mrliou MRL Public Route Evidence v1

This layer performs read-only HTTP GET probes. It does not deploy, change DNS,
select a Cloudflare version, alter traffic allocation or declare a route to be
the canonical APIWorks service.

The checked-in route map preserves the three version-specific Preview URLs
observed on 2026-09-13. `canonical_route_decision` remains `UNRESOLVED`, and
every entry explicitly keeps `production_traffic_asserted: false`.

The receipt binds the probe runner Git SHA, route-map SHA-256, timestamp, HTTP
status, bounded response size and SHA-256, selected non-secret headers, Worker
Version ID, observed deployment Git SHA and traffic scope. Response bodies are
not retained. URLs containing credentials or fragments are rejected; public
capture requires HTTPS and does not follow redirects.

Run on an authorized mainline checkout:

```bash
python scripts/Mrliou_MRL_public_route_receipt_v1.py \
  --route-map config/MRL_APIWorks_public_routes.observed.json \
  --output /absolute/path/Mrliou_MRL_Public_Route_Evidence \
  --git-head "$(git rev-parse HEAD)"
```

Recheck a captured artifact without network access:

```bash
python scripts/Mrliou_MRL_public_route_receipt_v1.py \
  --verify-only /absolute/path/Mrliou_MRL_Public_Route_Evidence
```

`PUBLIC_ROUTE_HTTP_PASS` proves only that every listed version-specific URL
returned its configured status during that probe. It does not prove production
traffic activation, canonical-route ownership, customer deployment, payment or
revenue.

The workflow deliberately lets capture and offline verification reach the
artifact-upload step even when a route fails. It uploads the FAIL receipt first
and only then enforces the job gate, so an HTTP 500, timeout or checksum failure
cannot disappear behind a red workflow status.
