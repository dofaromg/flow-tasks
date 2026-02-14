# CLAUDE.md

## Project Overview

**flow-tasks** (package name: `flow-next-app`, v3.0.0) is a multi-component distributed system by MRLiou combining:

- **Next.js frontend** (v15 + React 18) with GrowthBook feature flags
- **FlowAgent AI personality system** with Particle Language Core
- **WebGPU-accelerated neural network** modules for computation routing
- **Python microservices** (Flask) deployed on Google Kubernetes Engine (GKE)
- **GitOps CI/CD** via GitHub Actions + ArgoCD

Primary languages: **TypeScript**, **Python**, **Bash**, with some C, Perl, Go, and Rust.

Documentation is **bilingual** (English and Traditional Chinese) throughout the codebase.

---

## Repository Structure

```
flow-tasks/
├── src/                        # WebGPU neural network modules (TypeScript)
│   ├── modules/
│   │   ├── neuron/             # NeuronComputeCore - GPU neural computations
│   │   ├── attention/          # AttentionRoutingLayer - multi-head attention
│   │   ├── endpoint/           # ComputeEndpointManager - endpoint management
│   │   ├── routing/            # PLSRoutingEngine - particle language routing
│   │   └── types/              # Shared TypeScript interfaces
│   ├── neural-links/           # Neural linking utilities
│   └── tests/                  # Integration tests
├── particle_core/              # Particle Language Core System (Python)
│   ├── src/                    # logic_pipeline, fluin_dict_agent, ai_persona_toolkit, etc.
│   │   ├── memory/             # Memory management
│   │   └── wire/               # C interface (PD_AI_wire.h)
│   ├── language_spec/          # Particle language specification
│   └── tests/
├── flowos/                     # FlowOS Runtime Skeleton (TypeScript)
│   └── src/
│       ├── core/               # Particles, personas, chains, seeds, gate
│       ├── app/                # Conversations, projects, memory, artifacts, tools
│       ├── adapters/           # Envoy, K8s, JetStream
│       └── storage/
├── apps/                       # Kubernetes application manifests
│   ├── module-a/               # Python microservice (Flask)
│   ├── orchestrator/           # Service orchestrator
│   ├── nextjs-frontend/        # Next.js web app deployment
│   ├── astro-frontend/         # Astro static site
│   ├── mongodb/                # Database deployment + secrets
│   ├── monitoring/             # Prometheus configuration
│   └── keda/                   # Autoscaling (KEDA)
├── cluster/                    # Kubernetes cluster config (Kustomize)
│   ├── base/                   # Namespace, base kustomization
│   └── overlays/
│       ├── prod/
│       └── monitoring/
├── argocd/                     # GitOps (ArgoCD) config
├── connectors/                 # Service integrations (Python)
│   ├── github_connector.py
│   ├── notion_connector.py
│   ├── google_drive_connector.py
│   ├── vercel_connector.py
│   ├── gitlab_connector.py
│   ├── dropbox_connector.py
│   ├── huggingface_connector.py
│   └── icloud_connector.py
├── adapters/                   # Service adapters (github, notion)
├── core/                       # Core modules (memory_system.py, particle_dict.py)
├── modules/                    # Context management module
├── tools/                      # Specialized tools (ai-computer/)
├── lib/                        # Shared libraries (identify.ts, growthbook.ts)
├── pages/                      # Next.js pages (index.js)
├── scripts/                    # Deployment, sync, and utility scripts
├── config/                     # Config files (dev-mode.yaml, connectors.yaml)
├── docs/                       # Documentation (implementation, archive, performance)
├── tests/                      # Python test suite
├── .github/workflows/          # CI/CD pipelines (17 workflows)
├── git-hooks/                  # Pre-commit: Merkle signature verification
├── MrLiou_AI_SuperComputer/    # AI supercomputer framework
├── particle-chat-v42/          # Chat application with particle integration
├── particle-edge-v4/           # Edge computing particle system
├── particle_unified_system/    # Unified particle execution
├── particle_satellite_network/ # Distributed satellite network
├── global_parallel_network/    # Parallel network processing
├── vector-attention-engine/    # Attention mechanism vector processing
├── neural-links/               # Neural linking infrastructure
├── pipeline_vnext/             # Next-generation pipeline
└── hcra-context-manager/       # Context management system
```

---

## Development Commands

### JavaScript / Next.js

```bash
npm run dev              # Start development server (Next.js)
npm run build            # Production build
npm run start            # Start production server
npm run lint             # ESLint (next/core-web-vitals)
npm run test             # Run Jest tests
npm run test:watch       # Jest in watch mode
npm run test:coverage    # Jest with coverage report
```

### Python

```bash
pip install -r requirements.txt          # Install Python dependencies
pytest                                   # Run all Python tests
pytest -m unit                           # Run only unit tests
pytest -m integration                    # Run only integration tests
pytest -m particle                       # Run particle system tests
pytest -m memory                         # Run memory system tests
```

### Docker

```bash
docker-compose up                        # Start production services (nextjs + mongodb)
docker-compose -f docker-compose.dev.yml up  # Start dev services (localhost-only)
docker build -f Dockerfile.flowagent .   # Build FlowAgent container
```

### Kubernetes / GKE

```bash
scripts/oneclick_gke_init.sh             # One-click GKE initialization
scripts/actual_deploy.sh                 # Deploy to GKE
scripts/check_deployment_status.sh       # Check deployment status
```

---

## Testing

### TypeScript (Jest)

- Config: `jest.config.js` with `ts-jest` preset, `jsdom` environment
- Test patterns: `**/__tests__/**/*.ts`, `**/?(*.)+(spec|test).ts`
- Root directory: `src/`
- Module aliases: `@/*` maps to `src/*`
- WebGPU globals are mocked in `jest.setup.js` (navigator.gpu = undefined)
- Coverage collected from `src/**/*.{ts,tsx}`, excluding `.d.ts` and test files

### Python (pytest)

- Config: `pytest.ini`
- Test paths: `tests/`, `global_parallel_network/tests/`, `particle_unified_system/tests/`, `terminal_seed/tests/`
- Markers: `unit`, `integration`, `slow`, `particle`, `memory`, `core`, `api`, `e2e`
- Output: verbose, strict markers, short tracebacks

---

## Code Conventions

### TypeScript

- Class-based architecture with strict TypeScript interfaces
- PascalCase for classes (e.g., `NeuronComputeCore`, `AttentionRoutingLayer`)
- Barrel exports via `index.ts` files
- Bilingual JSDoc comments (English + Traditional Chinese)
- ESLint: extends `next/core-web-vitals`
- tsconfig: target ES2017, strict mode OFF, bundler module resolution

### Python

- Flask-based microservices in `apps/`
- Each app has: `app.py`, `Dockerfile`, `requirements.txt`, `deployment.yaml`
- Test files use `test_` prefix with descriptive docstrings
- Bilingual print output with checkmark symbols for test feedback

### Git Conventions

- **Commit style**: imperative verb-first (e.g., "Add feature", "Fix bug", "Update config")
- **Branch naming**: feature branches often use `copilot/` prefix
- **Pre-commit hook**: Merkle tree signature verification via `git-hooks/pre-commit`
- **PR template**: bilingual checklist with sections for description, testing, screenshots

---

## Architecture

### Deployment Pipeline

1. Push to `main` triggers `ci-build.yml` (builds Docker images for module-a, orchestrator, nextjs-frontend)
2. Images pushed to GCP Artifact Registry (`asia-east1-docker.pkg.dev/flowmemorysync/`)
3. `cd-deploy.yml` runs after successful build, deploys to GKE cluster `modular-cluster` in `asia-east1-a`
4. Kustomize builds manifests from `cluster/overlays/prod/`
5. ArgoCD can also manage deployments via `argocd/app.yaml`

### Services (GKE namespace: `flowagent`)

- **nextjs-frontend**: Next.js app (port 3000)
- **module-a**: Python Flask microservice
- **orchestrator**: Service orchestrator
- **mongodb**: MongoDB 6.0 (persistent storage)
- **monitoring**: Prometheus

### Key Integrations

- **GrowthBook**: Feature flags via `@growthbook/growthbook` and `@flags-sdk/growthbook`
- **Vercel**: Alternative deployment target (vercel.json configured)
- **External repo sync**: Configured in `repos_sync.yaml`, automated via workflow

---

## Configuration

### Environment Variables

See `.env.example` for full reference. Key variables:

| Variable | Purpose |
|----------|---------|
| `MONGODB_PASSWORD` / `MONGODB_URI` | Database connection |
| `NODE_ENV` | Node environment (development/production) |
| `NEXT_PUBLIC_GROWTHBOOK_API_HOST` | GrowthBook API endpoint |
| `NEXT_PUBLIC_GROWTHBOOK_CLIENT_KEY` | GrowthBook client key |
| `PROJECT_ID` / `REGION` / `ZONE` | GCP project settings |
| `CLUSTER_NAME` | GKE cluster name |

### Config Files

| File | Purpose |
|------|---------|
| `config.sample.yaml` | Context management strategies (workspace, sliding_window, summary, rag, hybrid) |
| `config/dev-mode.yaml` | Development mode settings |
| `config/connectors.yaml` | Connector configurations |
| `repos_sync.yaml` | External repository sync settings |

---

## CI/CD Workflows (.github/workflows/)

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `ci.yml` | Push to main/work/develop, PRs | Python smoke tests, artifact archival |
| `ci-build.yml` | Push to main (app paths) | Build & push Docker images to GCP |
| `cd-deploy.yml` | After ci-build success | Deploy to GKE with Kustomize |
| `deploy.yml` | Manual dispatch | Build Next.js, upload artifact |
| `pr-validation.yml` | Pull requests | Lint (flake8, black), test, build validation |
| `codeql-analysis.yml` | Scheduled/PRs | Security code analysis |
| `merkle-verify.yml` | On demand | Merkle tree verification |
| `webgpu-neural-network-ci.yml` | On push | WebGPU neural network testing |

---

## Important Notes for AI Assistants

- **Do not commit `.env` files** or secrets. Use `.env.example` as reference.
- **Bilingual convention**: code comments and docs use English + Traditional Chinese. Maintain this pattern when editing existing bilingual files.
- **Kubernetes manifests** in `apps/` and `cluster/` follow Kustomize patterns. Changes to these affect production deployments.
- **Pre-commit hook** runs Merkle signature verification. If `git-hooks/pre-commit` is active, commits will verify staged files.
- **TypeScript strict mode is OFF** (`tsconfig.json`). Do not assume strict null checks.
- **Next.js uses standalone output** (`next.config.mjs: output: 'standalone'`) for Docker optimization.
- **GCP region**: `asia-east1`. Container registry: `asia-east1-docker.pkg.dev`.
- **MongoDB credentials** default to `admin`/`changeme123` in production compose; dev uses `mrliou_dev` with env-var password.
- **Python has duplicate entries** in `requirements.txt` (Flask listed twice with different versions). Use the higher version constraint.
- The repo contains many **standalone subsystems** (particle-chat-v42, particle-edge-v4, MrLiou_AI_SuperComputer, etc.) that are semi-independent projects within the monorepo.
