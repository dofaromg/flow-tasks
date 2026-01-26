# Absorption Map (File → Law Mapping)

## Purpose
Tracks which documents and artifacts are absorbed by specific Root Laws or Execution Laws.

## Mapping Table

### Core Package Files
| Artifact | Law(s) | Notes |
| --- | --- | --- |
| README.md | All | User guide and quick start documentation. |
| RootLaws_v1.md | 1–42 | Canonical law list. Defines all root laws. |
| Execution_Laws.md | E-1–E-5 | Execution rules and enforcement mechanisms. |
| Evidence_Index.md | All | Evidence registry for all laws. |
| Progress_Snapshot.md | All, E-5 | Operational status and quarterly review tracking. |
| Absorption_Map.md | All | This file - maps artifacts to laws. |

### Particle Core System
| Artifact | Law(s) | Notes |
| --- | --- | --- |
| particle_core/src/logic_pipeline.py | 4, 7, 27, 28 | Implements STRUCTURE→MARK→FLOW→RECURSE→STORE chain. |
| particle_core/src/memory_archive_seed.py | 6, 16, 17, 18 | Memory seed creation with SHA-256 verification. |
| particle_core/src/cli_runner.py | 15, 21, 22 | CLI simulator with timeout and error handling. |
| particle_core/src/rebuild_fn.py | 5, 8, 18 | Compression/decompression with reversibility. |
| particle_core/src/logic_transformer.py | 8, 9, 27 | Logic transformation with context preservation. |
| particle_core/src/ai_persona_toolkit.py | 3, 9, 12 | Persona management and metadata handling. |
| particle_core/src/fluin_dict_agent.py | 1, 6, 12 | Dictionary seed memory with versioning. |
| particle_core/src/conversation_extractor.py | 11, 14, 18 | UTF-8 encoding and multiple format export. |
| particle_core/src/website_manager.py | 17, 19, 28 | Project backup and version control. |
| particle_core/requirements.txt | 34 | Python dependency version pinning. |

### FlowOS System
| Artifact | Law(s) | Notes |
| --- | --- | --- |
| flowos/src/lib/flow-law.ts | 2, 3, 22, 28 | Implements PARTICLE_OVERFLOW and ORPHANED_PARTICLE checks. |
| flowos/src/types/index.ts | 1, 9, 13 | Type definitions with metadata. |

### Task Management
| Artifact | Law(s) | Notes |
| --- | --- | --- |
| process_tasks.py | 7, 15, 22, 28 | Task processing with validation and logging. |
| tasks/*.yaml | 13, 14, 42 | Task definitions with metadata and traceability. |

### Testing & Validation
| Artifact | Law(s) | Notes |
| --- | --- | --- |
| test_integration.py | 27, E-1 | Integration testing for deterministic execution. |
| test_comprehensive.py | 27, E-1 | Comprehensive test suite. |
| particle_core/test_conversation_extractor.py | 11, 18, E-1 | Tests for conversation extractor module. |
| particle_core/test_import_export.py | 8, 18, E-1 | Tests for reversibility and compression integrity. |
| particle_core/test_website_manager.py | 17, E-1 | Tests for backup and versioning. |

### CI/CD & Deployment
| Artifact | Law(s) | Notes |
| --- | --- | --- |
| .github/workflows/ci-build.yml | 21, 29, E-1 | CI pipeline with timeout enforcement. |
| .github/workflows/cd-deploy.yml | 23, 29, E-1 | CD pipeline with graceful degradation. |

### Kubernetes Deployments
| Artifact | Law(s) | Notes |
| --- | --- | --- |
| apps/mongodb/*.yaml | 17, 25, 26, 39, 40 | MongoDB with health checks and resource limits. |
| cluster/base/*.yaml | 33, 35, 39, 40 | Base cluster configuration. |
| cluster/overlays/prod/*.yaml | 33, 38 | Production environment configuration. |
| argocd/app.yaml | 31, 32, 39 | ArgoCD GitOps configuration. |

### Configuration Files
| Artifact | Law(s) | Notes |
| --- | --- | --- |
| config.sample.yaml | 33, 38 | Sample configuration with environment variables. |
| repos_sync.yaml | 31, 34, 42 | Repository sync configuration with versioning. |
| package.json | 34, E-1 | Node.js dependencies version-pinned. |
| requirements.txt | 34, E-1 | Python dependencies version-pinned. |
| tsconfig.json | 35, 37 | TypeScript configuration for cross-platform. |
| .eslintrc.json | 41, E-1 | Code style enforcement. |

### Documentation
| Artifact | Law(s) | Notes |
| --- | --- | --- |
| README.md | 41, 42 | Main project documentation. |
| particle_core/README.md | 11, 41 | Bilingual documentation (Chinese/English). |
| particle_core/docs/*.md | 41, E-5 | Feature-specific documentation. |
| ARCHITECTURE.md | 41, 42 | System architecture documentation. |
| CHANGELOG.md | 12, 19, 42 | Version history and change tracking. |
| DEPLOYMENT.md | 33, 35, 41 | Deployment instructions. |

### Data & Examples
| Artifact | Law(s) | Notes |
| --- | --- | --- |
| particle_core/examples/*.json | 11, 13, 14, 16 | Example data with UTF-8 encoding and metadata. |
| data/*.json | 11, 13, 15 | Application data with validation. |
| FlowCapsule_Prototype_FLTN001.json | 1, 9, 13 | Particle prototype with complete metadata. |

### Scripts & Tools
| Artifact | Law(s) | Notes |
| --- | --- | --- |
| cli.py | 15, 21, 22, 28 | CLI tool with input validation and error handling. |
| sync_repositories.py | 24, 27, 28 | Repository sync with resource cleanup. |
| verify_no_missing_files.sh | 18, E-1 | File integrity verification script. |
| scripts/*.py | 22, 24, 28 | Utility scripts with proper error handling. |

### Package Formats
| Artifact | Law(s) | Notes |
| --- | --- | --- |
| *.flpkg files | 5, 12, 14, 16, 18 | Compressed logic packages with checksums. |
| *.fltnz files | 4, 14 | Tensor/flow notation files. |
| *.pcode files | 14, 27 | Particle code modules. |
| *.json files | 11, 13, 14, 15, 19 | JSON data with schema versioning. |
| *.md files | 11, 41 | Markdown documentation with UTF-8 encoding. |

### Cross-Cutting Concerns
| Artifact Pattern | Law(s) | Notes |
| --- | --- | --- |
| All Python modules | 11, 20, 22, 24, 28, 35 | UTF-8 encoding, null safety, error handling, resource cleanup, logging, cross-platform. |
| All TypeScript modules | 20, 22, 24, 35 | Null safety, error handling, resource cleanup, cross-platform. |
| All API endpoints | 15, 21, 26, 30, 31, 40 | Input validation, timeout, rate limiting, permissions, versioning, health checks. |
| All database operations | 25, 26, 29 | Concurrent access control, transaction atomicity. |
| All file operations | 11, 24, 30, 37, 38 | UTF-8 encoding, resource cleanup, permissions, path normalization. |
