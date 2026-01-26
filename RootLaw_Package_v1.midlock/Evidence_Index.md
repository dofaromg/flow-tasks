# Evidence Index

## Purpose
Registry of evidence supporting Root Laws and Execution Laws, including versioning and name conflicts.

## Evidence Registry

| Evidence ID | Law(s) | Source | Version | Notes |
| --- | --- | --- | --- | --- |
| EV-001 | 1 | particle_core/src/logic_pipeline.py | v1.0 | Particle unique ID generation and tracking |
| EV-002 | 1 | flowos/src/types/index.ts | v1.0 | FlowParticleSnapshot type definition |
| EV-003 | 2 | flowos/src/lib/flow-law.ts:8-14 | v1.0 | PARTICLE_OVERFLOW violation check |
| EV-004 | 3 | flowos/src/lib/flow-law.ts:16-23 | v1.0 | ORPHANED_PARTICLE violation check |
| EV-005 | 4 | particle_core/README.md:7 | v1.0 | STRUCTURE→MARK→FLOW→RECURSE→STORE chain |
| EV-006 | 5 | particle_core/src/rebuild_fn.py | v1.0 | Compression with metadata preservation |
| EV-007 | 6 | particle_core/src/memory_archive_seed.py | v1.0 | SHA-256 hash verification in seeds |
| EV-008 | 7 | particle_core/src/logic_pipeline.py | v1.0 | Start/end point definitions |
| EV-009 | 8 | particle_core/src/rebuild_fn.py | v1.0 | Reversible transformation implementation |
| EV-010 | 9 | particle_core/src/logic_transformer.py | v1.0 | Context preservation during transforms |
| EV-011 | 10 | particle_core/src/ | v1.0 | DAG structure in particle relationships |
| EV-012 | 11 | All Python files | v1.0 | UTF-8 encoding declarations |
| EV-013 | 12 | *.flpkg file naming | v1.0 | Semantic versioning in package names |
| EV-014 | 13 | particle_core/src/conversation_extractor.py | v1.0 | Metadata in conversation packages |
| EV-015 | 14 | File extension standards | v1.0 | .flpkg, .fltnz, .pcode, .json, .md extensions |
| EV-016 | 15 | particle_core/src/cli_runner.py | v1.0 | Input validation implementation |
| EV-017 | 16 | particle_core/src/memory_archive_seed.py | v1.0 | SHA-256 checksum in package creation |
| EV-018 | 17 | particle_core/src/website_manager.py | v1.0 | Backup functionality |
| EV-019 | 18 | particle_core/src/rebuild_fn.py | v1.0 | Lossless compression/decompression |
| EV-020 | 19 | data/*.json | v1.0 | JSON schema versioning |
| EV-021 | 20 | flowos/src/types/index.ts | v1.0 | Optional types with null handling |
| EV-022 | 21 | .github/workflows/ci-build.yml | v1.0 | Timeout settings in CI jobs |
| EV-023 | 22 | particle_core/src/logic_pipeline.py; particle_core/src/cli_runner.py | v1.0 | Try-except with full context |
| EV-024 | 23 | Service initialization code | v1.0 | Graceful degradation patterns |
| EV-025 | 24 | File handle management | v1.0 | Context managers for resource cleanup |
| EV-026 | 25 | Database access code | v1.0 | Lock mechanisms implementation |
| EV-027 | 26 | API client implementations | v1.0 | Rate limiting and retry logic |
| EV-028 | 27 | test_integration.py | v1.0 | Deterministic execution tests |
| EV-029 | 28 | Logging statements throughout | v1.0 | Structured logging with severity |
| EV-030 | 29 | Database transaction code | v1.0 | Atomic operations and rollback |
| EV-031 | 30 | File operation checks | v1.0 | Permission validation |
| EV-032 | 31 | API endpoint definitions | v1.0 | Version prefixes in URLs |
| EV-033 | 32 | Data migration scripts | v1.0 | Backward compatibility support |
| EV-034 | 33 | config.sample.yaml | v1.0 | External configuration example |
| EV-035 | 34 | requirements.txt, package.json | v1.0 | Pinned dependency versions |
| EV-036 | 35 | CI test matrix | v1.0 | Multi-platform testing |
| EV-037 | 36 | String encoding handling | v1.0 | Unicode-aware operations |
| EV-038 | 37 | Path operations | v1.0 | os.path.join and Path usage |
| EV-039 | 38 | Environment validation code | v1.0 | Startup checks for env vars |
| EV-040 | 39 | Kubernetes service definitions | v1.0 | Service discovery configuration |
| EV-041 | 40 | Health check endpoints | v1.0 | /health and /ready endpoints |
| EV-042 | 41 | Git commit history | v1.0 | Documentation updates with code |
| EV-043 | 42 | Pull request templates | v1.0 | Issue/task references required |
| EV-101 | E-1 | .github/workflows/*.yml | v1.0 | CI/CD automated compliance checks |
| EV-102 | E-1 | test_*.py files | v1.0 | Automated test suites |
| EV-103 | E-2 | Logging framework configuration | v1.0 | Severity level implementation |
| EV-104 | E-2 | Alert system integration | v1.0 | Violation reporting mechanism |
| EV-105 | E-3 | Law rollout documentation | v1.0 | Phased enforcement timeline |
| EV-106 | E-3 | Migration guides | v1.0 | Adoption assistance documentation |
| EV-107 | E-4 | Waiver request template | v1.0 | Waiver documentation process |
| EV-108 | E-4 | Approval workflow | v1.0 | Maintainer review process |
| EV-109 | E-5 | Quarterly review notes | v1.0 | Law review meeting records |
| EV-110 | E-5 | CHANGELOG.md | v1.0 | Law evolution history |

## Version Conflicts

### Conflict Resolution Log

**CR-001: Conversation Extractor Import/Export Methods**
- **Issue**: Multiple versions of import/export methods found in conversation_extractor.py
- **Files Affected**: particle_core/src/conversation_extractor.py
- **Versions**: 
  - v1.0: Basic JSON/Markdown/TXT export
  - v1.1: Added CSV, XML, YAML import/export support
- **Resolution**: v1.1 is current standard; v1.0 methods maintained for backward compatibility
- **Evidence**: Lines 90-130 in particle_core/README.md
- **Date**: 2026-01-10
- **Status**: Resolved - Both versions coexist with feature flags

**CR-002: Theme System Multiple Implementations**
- **Issue**: Two different theme implementation approaches
- **Files Affected**: particle_core/src/conversation_extractor.py, particle_core/src/website_manager.py
- **Versions**:
  - Original: Single default theme
  - Enhanced: 6 preset themes + custom palette support
- **Resolution**: Enhanced version adopted as standard
- **Evidence**: Lines 145-165 in particle_core/README.md
- **Date**: 2026-01-08
- **Status**: Resolved - Legacy code removed

**CR-003: Memory Archive Seed Format**
- **Issue**: Two snapshot format versions discovered
- **Files Affected**: particle_core/src/memory_archive_seed.py
- **Versions**:
  - v1: Basic JSON snapshot
  - v2: Enhanced with SHA-256 checksums and metadata
- **Resolution**: v2 is standard; v1 format still readable for migration
- **Evidence**: particle_core/docs/記憶封存種子說明.md
- **Date**: 2025-12-15
- **Status**: Resolved - Migration path documented

**CR-004: Particle Notation Syntax**
- **Issue**: Conflicting .fltnz notation styles
- **Files Affected**: *.fltnz files, particle_core/src/logic_transformer.py
- **Versions**:
  - Style A: ⋄fx.function.define syntax
  - Style B: Alternative compact notation
- **Resolution**: Style A (⋄fx prefix) is canonical standard
- **Evidence**: 萬用運算宇宙結構律法種子模組.md:36-40
- **Date**: 2025-11-20
- **Status**: Resolved - Style B deprecated

**CR-005: API Response Format**
- **Issue**: Inconsistent API response structures
- **Files Affected**: src_server_api_Version3.py, various API endpoints
- **Versions**:
  - v1: {status, data} format
  - v2: {success, result, errors} format
  - v3: Standardized with {status, data, metadata, errors}
- **Resolution**: v3 adopted across all new endpoints; v1/v2 supported in legacy endpoints
- **Evidence**: P.MetaEnv.openapi.yaml.txt
- **Date**: 2025-10-30
- **Status**: Resolved - v3 is standard, backward compatibility maintained

## Evidence Update History

| Date | Evidence ID | Change Type | Description |
| --- | --- | --- | --- |
| 2026-01-26 | All | Initial | Initial evidence registry creation |
| 2026-01-26 | CR-001 to CR-005 | Initial | Initial conflict resolution documentation |

## Evidence Validation Schedule

- **Next Review**: 2026-04-26 (Quarterly review per E-5)
- **Review Frequency**: Every 90 days
- **Validation Method**: Cross-reference source files, verify line numbers, check for deprecated evidence
- **Responsible Party**: Repository maintainer
- **Escalation**: Report discrepancies in GitHub issues with label `evidence-validation`

