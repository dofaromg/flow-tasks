# Root Laws v1 (1–42)

## Purpose
This document defines the 42 Root Laws for the RootLaw Package v1. Each law should be concise, testable, and mapped to evidence and execution rules.

## Structure
Use the following template for each law:

```
Law <number>: <title>
- Statement: <single-sentence rule>
- Rationale: <why this law exists>
- Scope: <systems or documents affected>
- Evidence: <pointers to Evidence_Index entries>
```

## Laws

### Particle System Integrity (Laws 1-10)

**Law 1: Particle Identity**
- Statement: Every particle must have a unique identifier and maintain its identity through state transitions.
- Rationale: Ensures traceability and prevents particle collision in the system.
- Scope: All particle_core modules, flow_code, flowos
- Evidence: EV-001, EV-002

**Law 2: Particle Overflow Prevention**
- Statement: No more than 10 draft particles shall exist without collapse.
- Rationale: Prevents memory overflow and maintains system performance.
- Scope: flowos/src/lib/flow-law.ts, particle_core execution
- Evidence: EV-003 (PARTICLE_OVERFLOW code)

**Law 3: Persona Attribution**
- Statement: All particles must reference a persona to maintain narrative consistency.
- Rationale: Orphaned particles break the coherence of the logic chain.
- Scope: particle_core, flowos persona management
- Evidence: EV-004 (ORPHANED_PARTICLE code)

**Law 4: State Transition Integrity**
- Statement: Particle state transitions must follow the sequence: STRUCTURE → MARK → FLOW → RECURSE → STORE.
- Rationale: Ensures predictable execution flow and proper logic chain processing.
- Scope: particle_core/src/logic_pipeline.py
- Evidence: EV-005

**Law 5: Collapse Consistency**
- Statement: Particle collapse must preserve all essential metadata and context.
- Rationale: Information loss during collapse breaks the reversibility principle.
- Scope: particle_core compression/decompression modules
- Evidence: EV-006

**Law 6: Memory Archive Integrity**
- Statement: Memory seeds must contain complete snapshot data and SHA-256 verification hashes.
- Rationale: Ensures seed restoration accuracy and detects corruption.
- Scope: particle_core/src/memory_archive_seed.py
- Evidence: EV-007

**Law 7: Logic Chain Completeness**
- Statement: Every logic chain execution must have a defined start and end point.
- Rationale: Prevents infinite loops and ensures deterministic behavior.
- Scope: All logic pipeline modules
- Evidence: EV-008

**Law 8: Reversibility Principle**
- Statement: All particle transformations must be reversible through stored metadata.
- Rationale: Core principle of the MRLiou particle language system.
- Scope: All transformation modules
- Evidence: EV-009

**Law 9: Context Preservation**
- Statement: Context data must be preserved across particle state changes.
- Rationale: Maintains the semantic meaning and execution environment.
- Scope: particle_core context management
- Evidence: EV-010

**Law 10: Particle Hierarchy**
- Statement: Parent-child relationships between particles must form a directed acyclic graph (DAG).
- Rationale: Prevents circular dependencies and ensures proper execution order.
- Scope: All particle relationship management
- Evidence: EV-011

### Data Integrity (Laws 11-20)

**Law 11: Encoding Consistency**
- Statement: All text data must use UTF-8 encoding.
- Rationale: Supports multilingual content (Chinese/English) and prevents encoding errors.
- Scope: All file I/O operations
- Evidence: EV-012

**Law 12: Version Tagging**
- Statement: All packages and modules must include semantic versioning.
- Rationale: Enables version tracking and compatibility management.
- Scope: .flpkg files, module definitions
- Evidence: EV-013

**Law 13: Metadata Completeness**
- Statement: All artifacts must include creation timestamp, author, and purpose metadata.
- Rationale: Provides audit trail and usage context.
- Scope: All generated files and packages
- Evidence: EV-014

**Law 14: File Format Standards**
- Statement: Standard file extensions must be used (.flpkg, .fltnz, .pcode, .json, .md).
- Rationale: Ensures proper file type identification and processing.
- Scope: All file creation operations
- Evidence: EV-015

**Law 15: Data Validation**
- Statement: All input data must be validated before processing.
- Rationale: Prevents injection attacks and data corruption.
- Scope: All API endpoints and CLI inputs
- Evidence: EV-016

**Law 16: Checksum Verification**
- Statement: All packaged modules must include and verify SHA-256 checksums.
- Rationale: Detects tampering and corruption.
- Scope: Package creation and restoration
- Evidence: EV-017

**Law 17: Backup Redundancy**
- Statement: Critical state data must have at least one backup copy.
- Rationale: Prevents data loss from system failures.
- Scope: Memory archive system, website manager
- Evidence: EV-018

**Law 18: Compression Integrity**
- Statement: Compressed packages must be decompressible without data loss.
- Rationale: Ensures reliable storage and transmission.
- Scope: .flpkg compression, ZIP handlers
- Evidence: EV-019

**Law 19: Schema Versioning**
- Statement: Data schemas must be versioned and backward compatible.
- Rationale: Allows system evolution without breaking existing data.
- Scope: JSON schemas, database models
- Evidence: EV-020

**Law 20: Null Safety**
- Statement: All optional fields must have explicit null handling.
- Rationale: Prevents null reference errors and undefined behavior.
- Scope: All data processing modules
- Evidence: EV-021

### Execution Control (Laws 21-30)

**Law 21: Timeout Enforcement**
- Statement: All operations must have a maximum execution timeout.
- Rationale: Prevents system hangs and resource exhaustion.
- Scope: Async operations, API calls
- Evidence: EV-022

**Law 22: Error Propagation**
- Statement: Errors must be propagated with full context and stack traces.
- Rationale: Enables debugging and proper error handling.
- Scope: All exception handling
- Evidence: EV-023

**Law 23: Graceful Degradation**
- Statement: System must continue operation in degraded mode when non-critical components fail.
- Rationale: Maintains availability during partial failures.
- Scope: Service initialization, optional features
- Evidence: EV-024

**Law 24: Resource Cleanup**
- Statement: All acquired resources must be released after use.
- Rationale: Prevents resource leaks and memory exhaustion.
- Scope: File handles, network connections, memory allocation
- Evidence: EV-025

**Law 25: Concurrent Access Control**
- Statement: Shared resources must implement proper locking mechanisms.
- Rationale: Prevents race conditions and data corruption.
- Scope: Multi-threaded operations, file access
- Evidence: EV-026

**Law 26: API Rate Limiting**
- Statement: External API calls must implement rate limiting and retry logic.
- Rationale: Prevents service abuse and handles transient failures.
- Scope: All external integrations
- Evidence: EV-027

**Law 27: Deterministic Execution**
- Statement: Given identical inputs and state, execution must produce identical outputs.
- Rationale: Enables testing, debugging, and reproducibility.
- Scope: Logic pipeline, transformations
- Evidence: EV-028

**Law 28: Logging Requirements**
- Statement: All state changes and errors must be logged with appropriate severity levels.
- Rationale: Enables monitoring, debugging, and audit trails.
- Scope: All modules
- Evidence: EV-029

**Law 29: Transaction Atomicity**
- Statement: Multi-step operations must be atomic or provide rollback capability.
- Rationale: Maintains data consistency during failures.
- Scope: Database operations, file system changes
- Evidence: EV-030

**Law 30: Permission Validation**
- Statement: All operations must verify user/process permissions before execution.
- Rationale: Enforces security and prevents unauthorized access.
- Scope: File operations, API endpoints
- Evidence: EV-031

### Integration & Compatibility (Laws 31-40)

**Law 31: API Versioning**
- Statement: All public APIs must include version identifiers.
- Rationale: Allows breaking changes without breaking clients.
- Scope: REST APIs, module interfaces
- Evidence: EV-032

**Law 32: Backward Compatibility**
- Statement: New versions must support reading data from previous versions.
- Rationale: Enables seamless upgrades and migration.
- Scope: All data formats, APIs
- Evidence: EV-033

**Law 33: Configuration Externalization**
- Statement: Environment-specific configuration must be external to code.
- Rationale: Enables deployment across different environments.
- Scope: All configurable parameters
- Evidence: EV-034

**Law 34: Dependency Isolation**
- Statement: Module dependencies must be explicitly declared and version-pinned.
- Rationale: Prevents dependency conflicts and ensures reproducible builds.
- Scope: requirements.txt, package.json
- Evidence: EV-035

**Law 35: Cross-Platform Compatibility**
- Statement: Core functionality must work on Linux, macOS, and Windows.
- Rationale: Maximizes usability and deployment options.
- Scope: All Python modules, build scripts
- Evidence: EV-036

**Law 36: Encoding Awareness**
- Statement: All string operations must be encoding-aware and handle Unicode correctly.
- Rationale: Supports multilingual content and prevents encoding bugs.
- Scope: All text processing
- Evidence: EV-037

**Law 37: Path Normalization**
- Statement: All file paths must be normalized to the platform-specific format.
- Rationale: Ensures cross-platform path compatibility.
- Scope: File system operations
- Evidence: EV-038

**Law 38: Environment Variable Validation**
- Statement: Required environment variables must be validated at startup.
- Rationale: Prevents runtime failures due to missing configuration.
- Scope: Application initialization
- Evidence: EV-039

**Law 39: Service Discovery**
- Statement: Services must support discovery mechanisms for distributed deployments.
- Rationale: Enables dynamic service topology and scalability.
- Scope: Kubernetes deployments, microservices
- Evidence: EV-040

**Law 40: Health Check Protocol**
- Statement: All services must expose health check endpoints.
- Rationale: Enables monitoring and automated recovery.
- Scope: All deployable services
- Evidence: EV-041

### Documentation & Governance (Laws 41-42)

**Law 41: Documentation Synchronization**
- Statement: Code changes must be accompanied by corresponding documentation updates.
- Rationale: Keeps documentation accurate and useful.
- Scope: All code changes
- Evidence: EV-042

**Law 42: Change Traceability**
- Statement: All changes must be traceable to a specific issue, task, or requirement.
- Rationale: Enables impact analysis and change management.
- Scope: All commits, pull requests
- Evidence: EV-043 
