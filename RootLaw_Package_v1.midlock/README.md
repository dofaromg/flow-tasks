# RootLaw Package v1.0 - User Guide

## Overview

The RootLaw Package v1.0 is a comprehensive governance framework for the FlowAgent GKE Starter repository with the MRLiou Particle Language Core System. It defines 47 laws (42 Root Laws + 5 Execution Laws) that govern system behavior, data integrity, execution control, integration, and documentation.

## Package Structure

```
RootLaw_Package_v1.midlock/
├─ README.md                 # This file - User guide
├─ RootLaws_v1.md           # 42 Root Laws (1-42)
├─ Execution_Laws.md        # 5 Execution Laws (E-1 to E-5)
├─ Absorption_Map.md        # File → Law mapping (60+ artifacts)
├─ Evidence_Index.md        # Evidence registry (110+ entries)
└─ Progress_Snapshot.md     # Task progress & anchors
```

## Quick Start

### For Developers

1. **Read RootLaws_v1.md** to understand the 42 laws organized in 5 categories:
   - Particle System Integrity (Laws 1-10)
   - Data Integrity (Laws 11-20)
   - Execution Control (Laws 21-30)
   - Integration & Compatibility (Laws 31-40)
   - Documentation & Governance (Laws 41-42)

2. **Check Absorption_Map.md** to find which laws apply to the files you're working on
   - Example: Working on `particle_core/src/logic_pipeline.py`? See Laws 4, 7, 27, 28

3. **Follow E-1 (Automated Compliance)** - Your code will be automatically checked by:
   - `code_review` tool
   - `codeql_checker` security scanner
   - `pytest` test suite
   - GitHub Actions CI/CD

### For Repository Maintainers

1. **Review Progress_Snapshot.md** quarterly (per E-5)
   - Next review: 2026-04-26
   - Track violations and waivers
   - Update evidence index

2. **Handle Violation Reports** (per E-2)
   - Critical: Immediate escalation
   - High: Escalate within 1 hour
   - Medium: Escalate within 24 hours
   - Low: Log and monitor

3. **Manage Waiver Requests** (per E-4)
   - Review justification and risk assessment
   - Maximum duration: 90 days
   - Regular review every 30 days

## Law Categories Explained

### Particle System Integrity (Laws 1-10)
Ensures particle identity, prevents overflow, maintains persona attribution, and enforces state transitions.

**Key Laws:**
- **Law 2**: No more than 10 draft particles without collapse
- **Law 3**: All particles must reference a persona
- **Law 4**: Follow STRUCTURE → MARK → FLOW → RECURSE → STORE sequence

### Data Integrity (Laws 11-20)
Enforces encoding standards, versioning, metadata, and data validation.

**Key Laws:**
- **Law 11**: UTF-8 encoding for all text
- **Law 16**: SHA-256 checksums for packages
- **Law 17**: Backup redundancy for critical data

### Execution Control (Laws 21-30)
Manages timeouts, error handling, resource cleanup, and logging.

**Key Laws:**
- **Law 21**: Timeout enforcement for all operations
- **Law 22**: Error propagation with full context
- **Law 28**: Logging requirements with severity levels

### Integration & Compatibility (Laws 31-40)
Ensures API versioning, backward compatibility, and cross-platform support.

**Key Laws:**
- **Law 31**: API versioning required
- **Law 32**: Backward compatibility maintained
- **Law 40**: Health check endpoints for services

### Documentation & Governance (Laws 41-42)
Maintains documentation synchronization and change traceability.

**Key Laws:**
- **Law 41**: Documentation updates with code changes
- **Law 42**: Change traceability to issues/tasks

## Execution Laws Explained

### E-1: Automated Compliance Verification
All laws are automatically checked by CI/CD pipelines.

### E-2: Exception Handling and Escalation
Violations are logged and escalated based on severity.

### E-3: Progressive Enforcement
New laws introduced with grace period (30-90 days).

### E-4: Remediation and Waiver Process
Temporary waivers available with justification (max 90 days).

### E-5: Continuous Monitoring and Improvement
Quarterly review and update of laws based on feedback.

## How to Use This Package

### When Writing Code

1. **Before coding**: Check Absorption_Map.md for applicable laws
2. **During coding**: Follow the relevant laws from RootLaws_v1.md
3. **Before committing**: Run local tests and linters
4. **After PR creation**: CI/CD will enforce E-1 automated compliance

### When Reviewing Code

1. Check that code follows applicable laws from Absorption_Map.md
2. Verify evidence exists in Evidence_Index.md for new patterns
3. Ensure documentation is updated (Law 41)
4. Verify change is traceable to issue/task (Law 42)

### When Encountering Violations

1. **Low severity**: Fix in next convenient iteration
2. **Medium severity**: Create issue and fix within sprint
3. **High severity**: Fix immediately, may block deployment
4. **Critical severity**: Stop deployment, fix immediately, escalate

### When Requesting a Waiver

1. Create GitHub issue with label `rootlaw-waiver`
2. Include:
   - Which law(s) need waiver
   - Justification (why compliance not feasible)
   - Risk assessment
   - Mitigation plan
   - Remediation timeline
3. Wait for maintainer approval
4. Document in Evidence_Index.md

## Cross-Reference Guide

### Finding Evidence for a Law
1. Open RootLaws_v1.md and find the law
2. Note the Evidence IDs (e.g., EV-003)
3. Look up evidence in Evidence_Index.md
4. Evidence entry shows source file and line numbers

### Finding Laws for a File
1. Open Absorption_Map.md
2. Search for your file in the Artifact column
3. Note the law numbers in the Law(s) column
4. Look up laws in RootLaws_v1.md

### Finding Implementation Status
1. Open Progress_Snapshot.md
2. Check "Implementation Status by Law Category"
3. See which laws are ✅ Implemented or ⚠️ Partial

## Package Maintenance

### Quarterly Review Process (E-5)

Every 90 days (next: 2026-04-26):

1. **Collect feedback** from developers and operations
2. **Analyze violations** from Progress_Snapshot.md
3. **Review waivers** for patterns indicating needed changes
4. **Propose updates** through GitHub issues
5. **Update Evidence_Index.md** with new evidence
6. **Update Progress_Snapshot.md** with review anchor
7. **Communicate changes** through documentation

### Adding a New Law

1. Create GitHub issue proposing new law
2. Follow E-3 progressive enforcement:
   - Warning Phase (30 days)
   - Error Phase (30 days)
   - Blocking Phase (ongoing)
3. Add law to appropriate category in RootLaws_v1.md
4. Add evidence to Evidence_Index.md
5. Update Absorption_Map.md with affected files
6. Update Progress_Snapshot.md with anchor
7. Announce via documentation update

### Updating Evidence

1. When code changes affect evidence:
   - Update source file reference in Evidence_Index.md
   - Update version number
   - Add note about change
2. When evidence conflicts arise:
   - Document in "Version Conflicts" section
   - Provide resolution notes
   - Update conflict resolution log

## Integration with Tools

### code_review Tool
- Validates code against documented laws
- Provides feedback on violations
- Must be run before finalizing PR

### codeql_checker Tool
- Scans for security vulnerabilities
- Enforces Laws 15, 16 (data validation, checksums)
- Must be run after code_review

### pytest Test Suite
- Validates functional requirements
- Enforces Law 27 (deterministic execution)
- Tests evidence implementations

### GitHub Actions CI/CD
- Enforces E-1 (automated compliance)
- Runs code_review, codeql_checker, pytest
- Blocks deployment on critical violations

## Troubleshooting

### "My PR is blocked by law violations"
1. Check CI/CD logs for specific violations
2. Look up the law in RootLaws_v1.md
3. Review evidence in Evidence_Index.md for examples
4. Fix the violation or request waiver if justified

### "A law seems outdated for my use case"
1. Create GitHub issue explaining the problem
2. Propose law modification or waiver
3. Wait for maintainer response
4. May go through E-3 progressive enforcement if law changes

### "I can't find evidence for a law"
1. Check Evidence_Index.md for the law number
2. If missing, create GitHub issue with label `evidence-missing`
3. Maintainer will add evidence or update law

### "Multiple laws conflict for my case"
1. Document the conflict in GitHub issue
2. Reference both laws and explain conflict
3. Maintainer will review and provide guidance
4. May result in law clarification or waiver

## Additional Resources

- **Main Repository**: [dofaromg/flow-tasks](https://github.com/dofaromg/flow-tasks)
- **Particle Core Docs**: `particle_core/docs/`
- **Architecture Guide**: `ARCHITECTURE.md`
- **Contributing Guide**: `BRANCH_INTEGRATION_GUIDE.md`

## Version History

| Version | Date | Changes |
| --- | --- | --- |
| v1.0 | 2026-01-26 | Initial release with 42 Root Laws + 5 Execution Laws |

## Contact

- **Issues**: Create GitHub issue with appropriate label
  - `rootlaw-package`: General questions
  - `rootlaw-waiver`: Waiver requests
  - `evidence-missing`: Missing evidence
  - `evidence-validation`: Evidence discrepancies
- **Maintainer**: Repository owner (dofaromg/flow-tasks)
- **Emergency**: Create issue with `critical` label

---

**Package Version**: v1.0  
**Last Updated**: 2026-01-26  
**Status**: Active  
**Next Review**: 2026-04-26
