# MRL Official Website Platform Launch v1

Branch: `MRL_Branch_OfficialWebsite_Platform_Launch_v1`
Mainline: `MRL_Product_Motherbody_Engineering_v1`

## Task

Complete MRL official website platform launch.
Connect existing MRL motherbody results to official website platform deployment.

## Engineering Facts

| Component | Identity | Role |
|-----------|----------|------|
| Layer A | ACTIVE_CPP_V1 | C++ signal source |
| PIDScope | MRL_LayerA_PIDScope | Layer A signal source |
| PersistentLoop | MRL_PersistentLoop | ORCHESTRATION_COLLECTOR |
| BaseWorld DB | BaseWorld | Runtime state ledger |
| EntryGateway | EntryGateway | External read interface |
| Convergence API | MobiusLoop | Recursive convergence detection |
| Canonical Runtime | DL580 | Production runtime |
| External Services | — | adapter / mirror / ingress only |

## Files Created

### Official Website Page

| File | Purpose |
|------|---------|
| `pages/mrl.js` | MRL Official Website homepage (route: `/mrl`) |

### API Routes (read-only gateway)

| Route | File | Purpose |
|-------|------|---------|
| `/api/mrl/status` | `pages/api/mrl/status.js` | Full MRL runtime status |
| `/api/mrl/product` | `pages/api/mrl/product.js` | MRL product entry |
| `/api/mrl/world-gateway` | `pages/api/mrl/world-gateway.js` | MRL World Gateway entry |
| `/api/mrl/runtime/convergence` | `pages/api/mrl/runtime/convergence.js` | Convergence API status |
| `/api/mrl/runtime/persistentloop` | `pages/api/mrl/runtime/persistentloop.js` | PersistentLoop / BaseWorld / EntryGateway status |

### MRL_Website Structure

| Directory | Purpose |
|-----------|---------|
| `MRL_Website/MRL_HomePage/` | Homepage module definition |
| `MRL_Website/MRL_ProductEntry/` | Product entry module definition |
| `MRL_Website/MRL_WorldGatewayEntry/` | World Gateway entry module definition |
| `MRL_Website/MRL_RuntimeStatus/` | Runtime status module definition |
| `MRL_Website/MRL_Deploy/` | Deployment config (Ingress + Kustomization) |

### Deploy Configuration

| File | Purpose |
|------|---------|
| `MRL_Website/MRL_Deploy/ingress.yaml` | GKE Ingress + ManagedCertificate for `mrl.mrliou.com` |
| `MRL_Website/MRL_Deploy/kustomization.yaml` | Kustomize config for MRL platform deploy |

### Documentation

| File | Purpose |
|------|---------|
| `docs/MRL_OfficialWebsite_Platform_Launch_v1.md` | This file - launch record |
| `docs/MRL_Product_Motherbody_Engineering_Status_v1.md` | Mainline backfill status |

## Routes

| Route | Method | Description |
|-------|--------|-------------|
| `/mrl` | GET | MRL Official Website homepage |
| `/api/mrl/status` | GET | Runtime status (Layer A, PersistentLoop, BaseWorld, EntryGateway, DL580) |
| `/api/mrl/product` | GET | Product motherbody entry |
| `/api/mrl/world-gateway` | GET | World Gateway with connector list |
| `/api/mrl/runtime/convergence` | GET | Convergence API (MobiusLoop, threshold, engine) |
| `/api/mrl/runtime/persistentloop` | GET | PersistentLoop + BaseWorld + EntryGateway status |

## Services

- **nextjs-frontend** (existing): Serves `/mrl` page and all `/api/mrl/*` routes
- **Ingress**: `mrl-official-platform-ingress` routes `mrl.mrliou.com` to nextjs-frontend
- **ManagedCertificate**: `mrl-official-cert` for TLS on `mrl.mrliou.com`

## Deploy

- Existing GKE deployment (`apps/nextjs-frontend/deployment.yaml`) serves the new pages
- Ingress added at `MRL_Website/MRL_Deploy/ingress.yaml`
- Domain: `mrl.mrliou.com` (configure DNS A record to GKE static IP `mrl-official-ip`)
- TLS via GKE ManagedCertificate

### Deploy Steps

1. Build: `npm run build` (Next.js standalone output includes new pages/routes)
2. Container: existing `ci-build.yml` workflow builds and pushes `nextjs-frontend` image
3. Apply Ingress: `kubectl apply -k MRL_Website/MRL_Deploy/`
4. DNS: Point `mrl.mrliou.com` A record to the GKE static IP
5. Verify: `curl https://mrl.mrliou.com/api/mrl/status`

## Verification

| Item | Status |
|------|--------|
| Official website | PASS - `/mrl` page renders full MRL platform |
| World Gateway | PASS - `/api/mrl/world-gateway` returns gateway data with connectors |
| Runtime Status | PASS - `/api/mrl/status` returns all component states |
| Layer A active_cpp_v1 shown | PASS - Displayed in product entry + runtime status + page hero |
| DL580 canonical runtime shown | PASS - Displayed in all API responses + page footer |
| PersistentLoop shown | PASS - `/api/mrl/runtime/persistentloop` |
| BaseWorld shown | PASS - `/api/mrl/runtime/persistentloop` |
| EntryGateway shown | PASS - `/api/mrl/runtime/persistentloop` + world-gateway |
| Convergence API shown | PASS - `/api/mrl/runtime/convergence` |
