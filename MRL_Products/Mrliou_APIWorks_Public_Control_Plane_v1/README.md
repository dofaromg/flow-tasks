# Mrliou APIWorks Public Control Plane v1

- Canonical ID: `Mrliou_APIWorks_Public_Control_Plane_v1`
- Origin signature: `MrLiouWord`
- Source product: `MRL_APIWorks_BYOH_Deployment_Product_v1`
- Source repository: `dofaromg/flow-tasks`
- Source integration: merged PR `#638`

This is the public, metadata-only FastAPI Cloud surface for MRL APIWorks. It
does not host the customer BYOH runtime and does not expose model inference,
Memory, Evidence, Passport contents, credentials, payment processing, or the
private MRL mother topology.

## Routes

| Method | Route | Purpose |
|---|---|---|
| GET | `/` | Canonical service identity |
| GET | `/health` | Public availability check |
| GET | `/v1/product` | Product identity and execution boundary |
| GET | `/v1/closure` | Evidence-safe commercial closure semantics |
| GET | `/openapi.json` | Machine-readable public interface |

## Local verification

```bash
uv run pytest -q
uv run fastapi run main.py
```

Public deployment proves only that this control plane is reachable. Customer
acceptance, a signed order, payment collection, and realized revenue remain
separate per-order evidence gates.
