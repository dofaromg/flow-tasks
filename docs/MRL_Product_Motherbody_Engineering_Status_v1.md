# MRL Product Motherbody Engineering Status v1

Mainline: `MRL_Product_Motherbody_Engineering_v1`

## Status: OFFICIAL WEBSITE PLATFORM LAUNCHED

Branch `MRL_Branch_OfficialWebsite_Platform_Launch_v1` completed.

## Motherbody Component Map

| Component | Identity | Status | Source |
|-----------|----------|--------|--------|
| Layer A | ACTIVE_CPP_V1 | ACTIVE | MRL_LayerA_PIDScope |
| PIDScope | MRL_LayerA_PIDScope | ACTIVE | Layer A signal source |
| PersistentLoop | MRL_PersistentLoop | ACTIVE | ORCHESTRATION_COLLECTOR |
| BaseWorld DB | BaseWorld | ACTIVE | Runtime state ledger |
| EntryGateway | EntryGateway | ACTIVE | External read interface |
| Convergence API | MobiusLoop | ACTIVE | MrLiou_AI_SuperComputer/ai_fusion_core.py |
| Canonical Runtime | DL580 | ACTIVE | Production runtime |

## Official Website Platform

| Entry | Route | Type |
|-------|-------|------|
| MRL Official Homepage | `/mrl` | Next.js page |
| MRL Product Entry | `/api/mrl/product` | API (read-only) |
| MRL World Gateway | `/api/mrl/world-gateway` | API (read-only) |
| MRL Runtime Status | `/api/mrl/status` | API (read-only) |
| Convergence API | `/api/mrl/runtime/convergence` | API (read-only) |
| PersistentLoop Status | `/api/mrl/runtime/persistentloop` | API (read-only) |

## Existing Motherbody Assets (unchanged)

| Asset | Path | Role |
|-------|------|------|
| Particle Core | `particle_core/src/` | Logic pipeline, dictionary agent, AI persona toolkit |
| AI SuperComputer | `MrLiou_AI_SuperComputer/` | Fusion engine, convergence, runtime stacks |
| FlowOS | `flowos/` | Core runtime (particles, personas, chains, seeds, gate) |
| WebGPU Neural Network | `src/modules/` | Attention routing, neuron compute, endpoint management |
| Connectors | `connectors/` | GitHub, Notion, Google Drive, Vercel, GitLab, Dropbox, HuggingFace, iCloud |
| Global Parallel Network | `global_parallel_network/` | Cloud/edge/satellite routing |
| Particle Satellite Network | `particle_satellite_network/` | Distributed routing engine |
| MRL LLM Framework | `particle_core/src/mrl_llm_framework.py` | Knowledge distillation + particle fusion |

## External Services Role

External services = adapter / mirror / ingress only. Not the runtime. Not the motherbody.

## Deploy

- GKE cluster: `modular-cluster` in `asia-east1-a`
- Namespace: `flowagent`
- Container registry: `asia-east1-docker.pkg.dev/flowmemorysync/flowagent/`
- Domain: `mrl.mrliou.com` via GKE Ingress
- CI/CD: `.github/workflows/ci-build.yml` + `.github/workflows/cd-deploy.yml`

## Branch Record

| Branch | Task | Status |
|--------|------|--------|
| MRL_Branch_OfficialWebsite_Platform_Launch_v1 | Official website platform launch | COMPLETED |

## Launch Document

See: `docs/MRL_OfficialWebsite_Platform_Launch_v1.md`
