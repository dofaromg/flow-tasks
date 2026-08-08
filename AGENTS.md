# AGENTS.md

> Instructions for AI coding agents (GitHub Copilot Coding Agent, Claude, etc.) working in this repository.

## Project Overview

**MrLiouAI GKE Starter** is a bilingual (English / Traditional Chinese) GitOps + CI/CD foundation for deploying MrLiouAI services on Google Kubernetes Engine (GKE). It also hosts the **MRLiou Particle Language Core System** (粒子語言核心系統) — a logic-seed computation and function-chain execution framework.

### Key Subsystems

| Subsystem | Location | Purpose |
|---|---|---|
| Particle Language Core | `particle_core/` | Logic seed computation, function-chain execution, compression/restoration, memory archival |
| Next.js Frontend | `pages/`, `src/` | React/Next.js 15 web application (weather dashboard, MrLiouAI UI) |
| Kubernetes Apps | `apps/` | Orchestrator, module-a, MongoDB, monitoring, frontend manifests |
| Cluster Config | `cluster/` | Kustomize base + overlays for GKE prod |
| GitOps | `argocd/` | Argo CD application definitions |
| CI/CD | `.github/workflows/` | GitHub Actions: build, deploy, lint, CodeQL, structure-index |
| Task System | `tasks/` | YAML task definitions processed by `process_tasks.py` |
| FlowOS Runtime | `flowos/` | TypeScript edge/runtime skeleton (neural links, gates, adapters) |

---

## Repository Layout

```
flow-tasks/
├── particle_core/          # Particle Language Core
│   ├── src/                # Core Python modules
│   ├── config/             # JSON configuration
│   ├── docs/               # Bilingual documentation
│   └── examples/           # Usage examples
├── apps/                   # Kubernetes app manifests
│   ├── orchestrator/
│   ├── module-a/
│   ├── mongodb/
│   ├── monitoring/
│   └── nextjs-frontend/
├── cluster/
│   ├── base/               # Kustomize base manifests
│   └── overlays/prod/      # Production overlay
├── argocd/                 # Argo CD app definitions
├── tasks/                  # Task YAML definitions + results/
├── flowos/                 # TypeScript runtime
├── pages/                  # Next.js pages
├── src/                    # Next.js app source
├── scripts/                # Utility scripts
├── docs/                   # Documentation index
├── flow_code/              # Generated code output
└── .github/
    ├── workflows/          # CI/CD workflow definitions
    └── copilot-instructions.md
```

---

## Environment Setup

```bash
# Python dependencies (main project)
pip install -r requirements.txt

# Python dependencies (particle core)
pip install -r particle_core/requirements.txt

# Node.js / Next.js dependencies
npm install
```

---

## Build & Validation Commands

### Next.js / TypeScript

```bash
npm run lint       # ESLint — run after any JS/TS/TSX change
npm run build      # Production build — must pass before merging
npm run dev        # Local dev server at http://localhost:3000
npm test           # Jest unit tests
npm run test:coverage  # Jest with coverage report
```

### Python

```bash
# Syntax check individual files
python -m py_compile <file.py>

# Run all Python tests
pytest

# Run integration tests
python test_integration.py
python test_comprehensive.py

# Process task definitions
python process_tasks.py
```

### Particle Core

```bash
cd particle_core

# Demo / smoke test
python demo.py demo

# Interactive memory archive system
python src/memory_archive_seed.py interactive

# Start the particle core CLI
python src/cli_runner.py
```

### Kubernetes Manifests

```bash
# Render and validate production overlay (dry-run)
kubectl kustomize cluster/overlays/prod/

# Apply dry-run (requires a cluster context)
kubectl apply --dry-run=client -k cluster/overlays/prod/
```

---

## Testing Guidelines

- **Always** run `npm run lint` and `npm run build` after any JavaScript/TypeScript change.
- **Always** run `pytest` (or the relevant test file) after any Python change.
- **Always** run `kubectl kustomize cluster/overlays/prod/` after modifying Kubernetes manifests.
- Run `python process_tasks.py` when modifying task YAML files under `tasks/`.
- Run `cd particle_core && python demo.py demo` after changes to `particle_core/src/`.

---

## Code Style & Conventions

### Python
- Python 3.10+, PEP 8, type hints where appropriate.
- Docstrings for public classes and functions (English or Traditional Chinese both acceptable).
- Use `rich` for CLI output formatting.
- File encoding: always `utf-8`.
- Use `os.path.join()` or `pathlib.Path` for cross-platform paths.

### JavaScript / TypeScript
- Next.js 15, React 18, TypeScript strict mode.
- ESLint configuration in `.eslintrc.json` — do not disable rules without justification.
- Use `async/await` over raw Promises.

### Naming Conventions
- **Python files**: `snake_case.py`
- **MRLiou modules**: `Mr.liou.{Component}.{Subcomponent}.{version}.{extension}` (e.g., `Mr.liou.MetaEnv.Core.pcode`)
- **Kubernetes manifests**: lowercase with hyphens.
- **Documentation**: Markdown; bilingual (English + 繁體中文) encouraged.

### Commit Messages
- English, concise, imperative mood (e.g., `fix: null check in auth middleware`).
- Keep commits atomic and focused.

---

## Security

- **Never commit secrets, credentials, API keys, or tokens.**
- Production secrets belong in GitHub Secrets, GCP Secret Manager, Sealed Secrets, or External Secrets Operator — not in Git.
- `apps/mongodb/secret.yaml` contains example credentials — replace before any production deployment.
- Use GCP Workload Identity Federation for service-account authentication.

---

## GCP / GKE Configuration

| Setting | Default |
|---|---|
| Project | `mrliouai` |
| Region | `asia-east1` |
| Zone | `asia-east1-a` |
| Cluster | `modular-cluster` |
| Container registry | `asia-east1-docker.pkg.dev/mrliouai/mrliouai/` |

Update these values in manifests and `argocd/app.yaml` when forking or deploying to a different environment.

---

## Important Files for AI Agents

| File | Notes |
|---|---|
| `.github/copilot-instructions.md` | Extended Copilot-specific guidelines |
| `README.md` | Project entry point and quick validation steps |
| `particle_core/README.md` | Particle Language Core documentation |
| `tasks/README.md` | Task definition format and processing |
| `cluster/README.md` | Kubernetes cluster layout |
| `apps/README.md` | Application manifest overview |
| `CHANGELOG.md` | Version history — update for significant changes |
