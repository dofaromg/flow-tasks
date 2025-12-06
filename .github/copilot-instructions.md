# GitHub Copilot Instructions for flow-tasks

## Project Overview

This is the **FlowAgent GKE Starter** repository, featuring a complete GitOps + CI/CD deployment framework with the **MRLiou Particle Language Core System** (粒子語言核心系統). The project combines Kubernetes orchestration with a unique particle-based logic execution framework.

### Key Components

1. **Particle Language Core** (`particle_core/`): A logic seed computation and function chain execution framework
2. **Kubernetes Deployments** (`apps/`, `cluster/`): GKE-based microservices architecture
3. **GitOps Configuration** (`argocd/`): Argo CD application definitions
4. **CI/CD Workflows** (`.github/workflows/`): Automated build and deployment pipelines
5. **Task Management** (`tasks/`): Project task definitions and results

## Code Style and Conventions

### Python Code
- Use Python 3.10+ features
- Follow PEP 8 style guidelines
- Include type hints where appropriate
- Add docstrings for classes and functions (support both English and Chinese)
- Use `rich` library for CLI output formatting

### Naming Conventions
- **Modules**: Use `Mr.liou.{Component}.{Subcomponent}.{version}.{extension}` pattern
  - Example: `Mr.liou.MetaEnv.Core.pcode`, `Mr.liou.TotalCore.Unity.v1.flpkg`
- **Python files**: Use snake_case (e.g., `logic_pipeline.py`, `cli_runner.py`)
- **Configuration files**: Use descriptive names with extensions (e.g., `core_config.json`)

### Documentation
- Support bilingual documentation (English and Traditional Chinese 繁體中文)
- Use markdown for all documentation files
- Include practical examples in documentation

## Project Structure

```
flow-tasks/
├── particle_core/          # Particle Language Core System
│   ├── src/               # Core source modules
│   ├── config/            # Configuration files
│   ├── docs/              # Documentation (Chinese & English)
│   └── examples/          # Usage examples
├── tasks/                 # Task definitions and results
│   ├── *.yaml            # Task definition files
│   └── results/          # Task execution results
├── flow_code/            # Generated code directory
├── apps/                 # Kubernetes application manifests
├── cluster/              # Cluster configuration
├── argocd/               # ArgoCD application definitions
├── scripts/              # Utility scripts
└── .github/
    ├── workflows/        # CI/CD workflows
    └── ISSUE_TEMPLATE/   # Issue templates
```

## Particle Language Core Specifics

### Logic Chain Execution Pattern
The core system follows this execution flow:
```
STRUCTURE → MARK → FLOW → RECURSE → STORE
```

### Key Modules
1. **logic_pipeline.py**: Main logic pipeline orchestration
2. **cli_runner.py**: CLI simulator and executor
3. **rebuild_fn.py**: Compression and restoration engine
4. **logic_transformer.py**: Logic transformation utilities
5. **memory_archive_seed.py**: Memory archival and restoration system

### File Formats
- `.flpkg`: Compressed logic package format
- `.fltnz`: Tensor/flow notation files
- `.pcode`: Particle code modules
- `.json`: Configuration and data files

## Testing Guidelines

### Running Tests
```bash
# Integration tests
python test_integration.py

# Comprehensive tests
python test_comprehensive.py

# Particle core demos
cd particle_core && python demo.py demo
```

### Test Organization
- Unit tests should be placed in module directories
- Integration tests in the root directory
- Use descriptive test function names with `test_` prefix

## Kubernetes and Deployment

### GCP Project Configuration
- Default project: `flowmemorysync`
- Default region: `asia-east1`
- Default zone: `asia-east1-a`
- Container registry: `asia-east1-docker.pkg.dev/flowmemorysync/flowagent/`

### Deployment Approaches
1. **GitOps (Argo CD)**: Pull-based deployment from repository
2. **GitHub Actions**: Push-based deployment with `ci-build.yml` and `cd-deploy.yml`

### Key Parameters to Modify
When forking or adapting this repository:
- Container image paths in manifests
- `argocd/app.yaml` repository URL
- Cluster name (default: `modular-cluster`)
- Region and zone settings
- GCP project ID

## API Development

### FastAPI Standards
- Use FastAPI for REST API endpoints
- Include OpenAPI/Swagger documentation
- Follow RESTful conventions
- Add proper request/response models with Pydantic

### Example API Structure
See `P.MetaEnv.openapi.yaml.txt` for the MetaEnv Control API specification.

## Memory and State Management

### Memory Archive System
- Use `MemoryArchiveSeed` for state persistence
- Follow snapshot/restore patterns
- Store archives in designated directories with versioning
- Include metadata for tracking (SHA-256 hashes, timestamps)

### Configuration Management
- Use JSON for structured configuration
- Support environment-specific configs
- Include validation for required fields

## Special Considerations

### Multilingual Support
- This is a Chinese-English bilingual codebase
- Comments and documentation may be in either language
- CLI output uses Traditional Chinese (繁體中文) with English technical terms
- Maintain consistency within each file

### Cross-Domain Integration
The project emphasizes "跨領域共振" (cross-domain resonance):
- Logic should be domain-agnostic where possible
- Support multiple execution contexts (local, container, K8s, WASM)
- Design for modularity and extensibility

### Version Control Best Practices
- Use descriptive commit messages (English preferred)
- Tag releases following semantic versioning
- Keep commits focused and atomic
- Update CHANGELOG.md for significant changes

## Dependencies

### Python Requirements
```
fastapi
uvicorn
rich
```

### Cloud Dependencies
- Google Cloud SDK (gcloud)
- kubectl for Kubernetes
- Kustomize for manifest management
- Argo CD for GitOps

## Common Patterns and Helpers

### CLI Interface Pattern
```python
from rich.console import Console
from rich.table import Table

console = Console()

def display_results(data):
    table = Table(title="Results")
    # Add columns and rows
    console.print(table)
```

### Logic Pipeline Pattern
```python
from logic_pipeline import LogicPipeline

pipeline = LogicPipeline()
result = pipeline.simulate(input_data)
```

### Configuration Loading
```python
import json

with open('config/core_config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)
```

## Security Considerations

- Never commit sensitive credentials
- Use GCP Workload Identity Federation for authentication
- Store secrets in GitHub Secrets or GCP Secret Manager
- Follow principle of least privilege for service accounts

## Quick Start Commands

### Particle Core Development
```bash
cd particle_core

# Run demo
python demo.py demo

# Start CLI
python src/cli_runner.py

# Memory archive system
python src/memory_archive_seed.py interactive
```

### GKE Deployment
```bash
# Set up environment
export PROJECT_ID=flowmemorysync
export REGION=asia-east1
export ZONE=asia-east1-a

# Get cluster credentials
gcloud container clusters get-credentials modular-cluster \
  --zone $ZONE --project $PROJECT_ID

# Apply configurations
kubectl apply -k cluster/overlays/prod/
```

## Additional Resources

- [README.md](../README.md): Main project documentation
- [Particle Core README](../particle_core/README.md): Particle Language system details
- [本地執行說明](../particle_core/docs/本地執行說明.md): Local execution guide
- [記憶封存種子說明](../記憶封存種子系統更新說明.md): Memory archive system
- [CHANGELOG.md](../CHANGELOG.md): Version history

## Contact and Contribution

This is a specialized system combining quantum computing concepts, particle-based logic, and modern cloud-native practices. When contributing:
- Respect the existing architectural patterns
- Maintain bilingual documentation
- Test thoroughly in both local and cloud environments
- Follow the established module naming conventions
