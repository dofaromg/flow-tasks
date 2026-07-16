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

## Build and Development Tools

### Available Scripts and Commands

**Python Environment**
- Main requirements: `requirements.txt` (Flask, PyYAML, requests, pytest)
- Particle core requirements: `particle_core/requirements.txt` (FastAPI, uvicorn, rich)
- Test runner: `pytest` (installed via requirements.txt)

**Node.js/Next.js Environment**
- Package manager: `npm`
- Available scripts in `package.json`:
  - `npm run dev` - Start development server
  - `npm run build` - Build production bundle
  - `npm run start` - Start production server
  - `npm run lint` - Run ESLint

**Testing Commands**
```bash
# Python integration tests
python test_integration.py

# Python comprehensive tests
python test_comprehensive.py

# Particle core demo
cd particle_core && python demo.py demo

# Task processing
python process_tasks.py
```

**Kubernetes Tools**
- `kubectl` - Kubernetes CLI for manifest validation and deployment
- `kustomize` - Built into kubectl for overlay management
- Validation: `kubectl apply --dry-run=client -k cluster/overlays/prod/`

### Repository Initialization
When working with a fresh clone:
```bash
# Install Python dependencies
pip install -r requirements.txt
pip install -r particle_core/requirements.txt

# Install Node.js dependencies
npm install

# Verify setup
python test_integration.py
npm run lint
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

## Database Management (MongoDB)

### MongoDB Deployment
This repository includes MongoDB as the primary database:
- **Location**: `apps/mongodb/`
- **Deployment**: StatefulSet pattern with persistent storage
- **Version**: MongoDB 6.0
- **Namespace**: `flowagent`
- **Port**: 27017

### Database Configuration
- **Connection string format**: `mongodb://admin:<password>@mongodb.flowagent.svc.cluster.local:27017`
- **Credentials**: Stored in `apps/mongodb/secret.yaml` (change for production!)
- **Persistent storage**: 10Gi PVC at `/data/db`
- **Resource limits**: 256Mi-512Mi memory, 100m-500m CPU

### Automatic Updates and Optimization
The database system is designed to:
1. **Auto-scale storage**: PVC can be expanded when needed (requires manual intervention)
2. **Self-optimize**: MongoDB's internal optimization runs automatically
3. **Auto-backup**: Configure periodic backups using CronJobs or external tools
4. **Monitor performance**: Integrate with Prometheus for metrics

### Database Operations

**Connecting to MongoDB**
```bash
# Port forward to local machine
kubectl port-forward svc/mongodb 27017:27017 -n flowagent

# Connect using mongosh
mongosh "mongodb://admin:<password>@localhost:27017"
```

**Backup and Restore**
```bash
# Backup
kubectl exec -it deployment/mongodb -n flowagent -- mongodump --out /data/backup

# Restore
kubectl exec -it deployment/mongodb -n flowagent -- mongorestore /data/backup
```

**Scaling Storage**
```bash
# Edit PVC to increase size
kubectl edit pvc mongodb-pvc -n flowagent
# Update storage size, then restart pod
kubectl rollout restart deployment/mongodb -n flowagent
```

**Monitoring Database Health**
```bash
# Check database status
kubectl exec -it deployment/mongodb -n flowagent -- mongosh --eval "db.adminCommand('ping')"

# Check pod logs
kubectl logs -f deployment/mongodb -n flowagent

# Check resource usage
kubectl top pod -n flowagent -l app=mongodb
```

### Database Schema and Migrations
- Use versioned migration scripts for schema changes
- Store migrations in `scripts/migrations/` directory
- Document all schema changes in CHANGELOG.md
- Test migrations in development before production

### Performance Optimization
- **Indexes**: Create indexes for frequently queried fields
- **Connection pooling**: Applications use connection pooling by default
- **Query optimization**: Monitor slow queries and optimize
- **Sharding**: Consider sharding for large-scale data growth

### Security Best Practices
- **Change default password**: Update `apps/mongodb/secret.yaml` for production
- **Enable authentication**: Always use authenticated connections
- **Network isolation**: Use NetworkPolicy to restrict database access
- **Encryption**: Enable encryption at rest and in transit for sensitive data
- **Regular updates**: Keep MongoDB version updated for security patches

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

## Testing and Validation Procedures

### Test Execution Workflow
When making changes to this repository, follow this testing sequence:

1. **Run targeted tests first** to validate specific changes:
   ```bash
   # For Python changes
   python test_integration.py
   python test_comprehensive.py
   
   # For Next.js/React changes
   npm run lint
   npm run build
   ```

2. **Run particle core tests** for particle language changes:
   ```bash
   cd particle_core
   python demo.py demo
   ```

3. **Full validation** before finalizing:
   ```bash
   # Python linting (if available)
   python -m pytest --cov
   
   # Next.js linting and build
   npm run lint
   npm run build
   ```

### When to Run Tests
- **Always** run tests after modifying Python modules in `particle_core/src/`
- **Always** run linting after changing JavaScript/React code
- **Always** validate Kubernetes manifests before committing:
  ```bash
  kubectl apply --dry-run=client -k cluster/overlays/prod/
  ```
- Run integration tests when changing task processing logic
- Run comprehensive tests before creating a pull request

### Test Organization
- **Unit tests**: Place in the same directory as the module being tested
- **Integration tests**: Keep in repository root (`test_integration.py`, `test_comprehensive.py`)
- **Particle core tests**: Use `particle_core/demo.py` for demonstration and validation

## Linting and Code Quality

### Python Code Quality
- Run `python -m py_compile <file>` to check syntax before committing
- Follow PEP 8 style guidelines (use `black` or `autopep8` if available)
- Validate type hints with `mypy` if configured
- Check for common issues:
  ```bash
  python -m py_compile particle_core/src/*.py
  ```

### JavaScript/TypeScript Code Quality
- Use `npm run lint` to check Next.js code
- ESLint configuration is in `.eslintrc.json`
- Fix auto-fixable issues with `npm run lint -- --fix`
- Always run linting before committing React/Next.js changes

### YAML/Manifest Validation
- Validate Kubernetes manifests:
  ```bash
  kubectl apply --dry-run=client -f <manifest>
  ```
- Check YAML syntax for task definitions:
  ```bash
  python -c "import yaml; yaml.safe_load(open('tasks/<file>.yaml'))"
  ```

## Development Workflow and Iteration

### Making Changes
1. **Before starting**: Check current state with `git status` and run existing tests
2. **During development**: Make small, incremental changes
3. **After each change**: Run relevant tests and validation
4. **Before committing**: Run full test suite and linting

### Debugging Failed Tests
- Check test output carefully for specific failure messages
- Use `python -i <test_file.py>` for interactive debugging
- Add print statements or use `rich.print()` for detailed output
- Check logs in `tasks/results/` for task processing issues

### Common Development Commands
```bash
# Check Python module imports
python -c "import sys; sys.path.insert(0, 'particle_core/src'); from logic_pipeline import LogicPipeline"

# Validate task YAML files
python -c "import yaml; print(yaml.safe_load(open('tasks/<file>.yaml')))"

# Test API endpoints locally
python src_server_api_Version3.py  # Start server, then test

# Check Kubernetes manifest syntax
kubectl apply --dry-run=client -k cluster/overlays/prod/
```

## Dependency Management

### Adding Python Dependencies
1. **Check for vulnerabilities** before adding new packages
2. Add to appropriate `requirements.txt`:
   - Root `requirements.txt` for main project dependencies
   - `particle_core/requirements.txt` for particle core specific dependencies
3. Install and test:
   ```bash
   pip install -r requirements.txt
   pip install -r particle_core/requirements.txt
   ```

### Adding Node.js Dependencies
1. Use `npm install <package>` to add dependencies
2. Commit both `package.json` and `package-lock.json`
3. Test the build after adding dependencies:
   ```bash
   npm install
   npm run build
   ```

### Version Pinning
- Pin major versions for stability
- Document why specific versions are required
- Test thoroughly when upgrading dependencies

## Troubleshooting and Common Pitfalls

### Common Issues and Solutions

**Import Errors in Particle Core**
- Ensure `particle_core/src` is in Python path
- Use: `sys.path.insert(0, 'particle_core/src')` before imports

**Kubernetes Manifest Validation Failures**
- Check indentation (use spaces, not tabs)
- Validate with `kubectl apply --dry-run=client`
- Ensure namespace references are correct

**Task Processing Errors**
- Check YAML syntax in task definition files
- Verify required fields are present
- Check logs in `tasks/results/` directory

**Build Failures**
- For Next.js: Clear `.next` directory and rebuild
- For Python: Check for circular imports
- Ensure all dependencies are installed

**Test Failures**
- Read the full error message and stack trace
- Check if files/directories referenced in tests exist
- Verify test data and fixtures are available

### File Encoding Issues
- Always use UTF-8 encoding for files
- Python file operations: `open(file, 'r', encoding='utf-8')`
- This is critical for bilingual (Chinese/English) content

### Path Issues
- Use absolute paths when in doubt
- For particle core: `/home/runner/work/flow-tasks/flow-tasks/particle_core/`
- Use `os.path.join()` or `pathlib.Path()` for cross-platform compatibility

## Git and Version Control

### Commit Guidelines
- **Commit messages**: Use clear, descriptive messages in English
- **Commit scope**: Keep commits atomic and focused
- **What to commit**:
  - Source code changes
  - Configuration updates
  - Documentation updates
  - Test additions/modifications
- **What NOT to commit**:
  - `node_modules/` (already in `.gitignore`)
  - Build artifacts (`.next/`, `__pycache__/`, etc.)
  - Local configuration files
  - Temporary test files
  - IDE-specific files

### Branch Strategy
- Main branch: `main`
- Feature branches: Use descriptive names
- Copilot branches: Automatically created as `copilot/<task-name>`

### Before Pushing
1. Run `git status` to review changes
2. Run tests and linting
3. Review diff with `git diff`
4. Ensure no sensitive data is being committed

## Working with Copilot Coding Agent

### Best Practices for Task Assignment
- Provide clear, specific issue descriptions
- Include file paths and line numbers when relevant
- Specify expected behavior and acceptance criteria
- Reference existing code patterns to follow

### Iterating on Copilot's Work
- Review changes carefully before approving
- Leave feedback via PR comments for improvements
- Use @copilot mentions in PR comments for clarifications
- Request specific changes rather than general feedback

### Good Tasks for Copilot
- Bug fixes with clear reproduction steps
- Adding tests for existing functionality
- Documentation updates and improvements
- Code refactoring with defined scope
- Adding new features with clear specifications

### Tasks Requiring Human Review
- Security-critical changes
- Complex architectural decisions
- Changes to deployment configurations
- Breaking changes to APIs
- Modifications to CI/CD pipelines

## Contact and Contribution

This is a specialized system combining quantum computing concepts, particle-based logic, and modern cloud-native practices. When contributing:
- Respect the existing architectural patterns
- Maintain bilingual documentation
- Test thoroughly in both local and cloud environments
- Follow the established module naming conventions
- Use the testing and validation procedures outlined above
- Ensure code quality through linting and validation
- Communicate clearly in issues and pull requests
