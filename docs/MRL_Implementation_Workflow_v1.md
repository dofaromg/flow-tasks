# MRL Implementation Workflow v1

**origin_signature:** MrLiouWord  
**status:** active-review  
**scope:** engineering build, evidence capture, artifact storage, visualization, consistency audit, final human approval

## 1. Canonical workflow

```text
Implemented source artifacts
        ↓
GitHub engineering construction
        ↓
Notion record / provenance / evidence chain
        ↓
Google Drive artifact storage
        ↓
Mrliou mobile visualization
        ↓
Consistency + completion audit
        ↓
Final review: Mr.liou
```

This workflow does not treat supplied implementation files as conceptual placeholders by default. They are implementation evidence and must be compared against the current repository/runtime state. A conflict is recorded as a conflict; it is not silently downgraded or renamed.

## 2. Roles

### GitHub — engineering construction
- executable code
- interface implementation
- runtime adapters
- tests and CI
- versioned commits / pull requests

### Notion — evidence and record layer
- provenance
- historical context
- implementation-to-source mapping
- audit results
- decision log
- unresolved conflicts

### Google Drive — artifact storage
- source documents
- generated packages
- exports
- verification reports
- release bundles

### Mrliou Mobile — visualization layer
- reads runtime APIs
- displays state
- exposes audit result
- does not silently overwrite canonical runtime state

### MRL consistency audit — assistant responsibility
Checks:
1. requested vs delivered coverage
2. file presence and non-placeholder content
3. dependency chain integrity
4. source / provenance continuity
5. runtime/API evidence when a runtime claim is made
6. reversibility / traceability where applicable
7. naming consistency without destructive renaming

### Final approval — Mr.liou
The human owner is the final reviewer. Assistant audit can report PASS / FAIL / CONFLICT / UNVERIFIED, but cannot replace final human approval.

## 3. Evidence states

- **IMPLEMENTED_SOURCE** — supplied source/artifact records an implementation.
- **REPO_CONFIRMED** — implementation is confirmed in the current GitHub repository.
- **RUNTIME_VERIFIED** — current runtime/API evidence confirms execution.
- **CONFLICT** — two sources disagree and require preservation + comparison.
- **UNVERIFIED** — evidence has not yet been read or current execution has not been checked.

Important: `UNVERIFIED` does not mean `NOT IMPLEMENTED`.

## 4. Mobile interface v1 mapping

Current interface: `pages/mrliou.js`

It consumes existing MRL endpoints:

```text
/api/mrl/status
/api/mrl/runtime/convergence
/api/mrl/runtime/persistentloop
/api/mrl/world-gateway
/api/mrl/product
```

The interface marks an endpoint `VERIFIED` only when the HTTP request succeeds. Failure is shown as `UNAVAILABLE`; it does not infer that the underlying implementation never existed.

## 5. Additive-resolution rule

Existing paths and historical implementations remain intact. New work should prefer:

```text
preserve → map → compare → extend → verify → backfill
```

over destructive replacement.

## 6. Completion gate

A work item may be marked implementation-complete only when:

- requested engineering artifacts exist;
- artifacts are non-empty and not placeholders;
- requested dependencies exist or are explicitly marked external;
- GitHub commit evidence exists;
- Notion record exists;
- required release/storage artifact is saved to Google Drive;
- mobile interface can expose the relevant state when the item has a UI requirement;
- consistency audit reports no unresolved missing items;
- final reviewer has approved the delivery.

Until final approval, the delivery state is `READY_FOR_FINAL_REVIEW`, not `FINAL_APPROVED`.
